"""``tma2-gh``: score one condition's prediction files for Gate H (spec 010 contracts/cli.md).

Estimators are read from ``tma2-hpredict`` / ``tma2-g2predict`` files (named by their header's
``estimator``, or ``NAME=PATH``); one leg, the plain oracle and the frozen IMM and EKF are solved
in the same run on the same rows. With ``--mismatch-truth`` the Cramér–Rao bound is taken under
the true error covariance (realised outliers included), otherwise the standard known-manoeuvres
bound. Writes ``errors.npz`` and ``headroom.json``.

Tuning runs need nothing else. A validation or test scoring needs ``--decision`` and ``--plan``
(the decision record binding the plan), and a test scoring must cover every σ = 1° scenario.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-gh", description=__doc__)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--predictions", nargs="+", required=True, metavar="[NAME=]PATH")
    ap.add_argument("--mismatch-truth", help="the split's truth side file, for the bound only")
    ap.add_argument("--imm", help="the frozen IMM's name")
    ap.add_argument("--ekf", help="the frozen EKF's name")
    ap.add_argument("--no-bound", action="store_true", help="skip the Cramér–Rao bound")
    ap.add_argument("--resamples", type=int, default=2000)
    ap.add_argument("--split", choices=["tuning", "validation", "test"], default="tuning")
    ap.add_argument("--decision", help="the Gate H decision record (validation and test)")
    ap.add_argument("--plan", help="the plan the decision binds")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    import numpy as np
    import torch

    from tma2.cli.hpredict import KNOTS, load_truth
    from tma2.data.f32pack import read_pack_header
    from tma2.data.provenance import read_git_provenance
    from tma2.eval.errors import Truth
    from tma2.eval.rows import settled_row
    from tma2.headroom import gate
    from tma2.headroom.crb import crb_rows_cov
    from tma2.headroom.estimators import true_model
    from tma2.physics.layer import PhysicsLayer
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment import score as sc
    from tma2.segment.gate import sha256_file
    from tma2.sim import mismatch as mm

    gp = read_git_provenance()  # before any output
    t0 = time.time()
    hdr = read_pack_header(a.truth)
    condition = hdr.mismatch.id if hdr.mismatch is not None else "off"
    bad: list[str] = []
    plan: dict[str, Any] = {}
    if a.split != "tuning":
        if not (a.decision and a.plan):
            bad.append(f"--split {a.split} needs --decision and --plan")
        else:
            raw = Path(a.plan).read_bytes()
            plan = json.loads(raw)
            rec = json.loads((Path(a.decision) / "decision.json").read_text())
            if rec.get("plan_digest") != hashlib.sha256(raw).hexdigest():
                bad.append("the decision record does not bind this plan")
            if str(plan["seeds"][a.split]) != hdr.dataset_seed:
                bad.append(f"{a.truth} is not the plan's {a.split} seed")
    elif a.decision or a.plan:
        bad.append("--decision and --plan are for validation and test scorings")
    if a.mismatch_truth and hdr.mismatch is None:
        bad.append("the split carries no mismatch")
    named: dict[str, str] = {}
    for spec in a.predictions:
        name, _, path = spec.rpartition("=")
        head = json.loads(Path(path).read_text().split("\n", 1)[0])
        name = name or head["estimator"]
        if name in named:
            bad.append(f"two prediction files named {name}")
        named[name] = path
        if head.get("dataset_digest") not in (None, sha256_file(a.truth)):
            bad.append(f"{path} was not made from {a.truth}")
        if a.split != "tuning" and head.get("git_dirty"):
            bad.append(f"{path} was made from a dirty tree")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2
    torch.set_default_dtype(torch.float64)
    data, metas, truths = {}, {}, {}
    owns: dict[int, np.ndarray] = {}
    tgts: dict[int, np.ndarray] = {}
    obss: dict[int, np.ndarray] = {}
    total = sum(1 for _ in sc.iter_selected(a.truth, 0, 10**9)) if a.split == "test" else 0
    for j, m, own, tgt, obs in sc.iter_selected(a.truth, a.start, a.count):
        owns[j], tgts[j], obss[j] = own, tgt, obs
        data[j] = bearing_data_from_arrays(m, own, obs)
        metas[j] = m
        truths[j] = Truth.from_block(m, own, tgt)
    if a.split == "test" and condition == plan.get("primary") and len(data) < total:
        print(
            f"a test scoring of the primary condition must cover all {total} sigma = 1 deg "
            f"scenarios, not {len(data)}",
            file=sys.stderr,
        )
        return 2
    rows = [
        sc.Row(j, k, settled_row(metas[j], k))
        for j in sorted(data)
        for k in sc.g5_rows(metas[j], data[j].n)
    ]
    if not rows:
        print("no rows to score", file=sys.stderr)
        return 2
    cluster = np.array([r.ordinal for r in rows], dtype=np.int64)
    ks = np.array([r.k for r in rows], dtype=np.int64)
    settled = np.array([r.settled for r in rows])
    true_range = np.array(
        [
            float(
                np.hypot(
                    tgts[r.ordinal][r.k, 1] - owns[r.ordinal][r.k, 1],
                    tgts[r.ordinal][r.k, 2] - owns[r.ordinal][r.k, 2],
                )
            )
            for r in rows
        ]
    )
    minute = np.array(
        [
            int(
                round(
                    (r.k - int(metas[r.ordinal]["zig_index"]))
                    * float(metas[r.ordinal]["parameters"]["dt_s"])
                    / 60.0
                )
            )
            for r in rows
        ],
        dtype=np.int64,
    )
    layer = PhysicsLayer(knots=KNOTS)
    errs: dict[str, np.ndarray] = {
        "one_leg": sc.layer_errors(layer, rows, data, metas, truths, sc.one_leg),
        "oracle": sc.layer_errors(layer, rows, data, metas, truths, sc.oracle),
    }
    print(f"one leg and oracle [{time.time() - t0:.0f} s]", flush=True)
    if a.imm:
        errs["imm"] = sc.imm_errors(rows, data, truths, a.imm)
    if a.ekf:
        errs["ekf"] = sc.ekf_errors(rows, data, truths, a.ekf)
    for name, path in named.items():
        errs[name] = sc.prediction_errors(rows, data, truths, path)
    bound = None
    if not a.no_bound:
        if a.mismatch_truth:
            _meta, eng, outlier = load_truth(a.mismatch_truth, a.truth)
            bound = np.full((len(rows), 3), np.nan)
            by: dict[int, list[int]] = {}
            for q, r in enumerate(rows):
                by.setdefault(r.ordinal, []).append(q)
            for j, qs in by.items():
                pos = int(metas[j]["index"]) - hdr.index_start
                n = data[j].n
                extra = outlier[pos, :n].astype(np.float64) * float(eng[pos, mm.E_OUT_SD]) ** 2
                crb = crb_rows_cov(
                    owns[j],
                    tgts[j],
                    obss[j],
                    metas[j]["parameters"].get("target_manoeuvres") or [],
                    [rows[q].k for q in qs],
                    true_model(eng[pos]),
                    extra,
                )
                for q, c in zip(qs, crb, strict=True):
                    if not c.singular:
                        bound[q] = (c.sd_range_rel, c.sd_course_deg, c.sd_speed_kt)
        else:
            bound = sc.bounds(rows, metas, owns, tgts, obss)
        print(f"bound [{time.time() - t0:.0f} s]", flush=True)
    level = float(plan.get("bootstrap", {}).get("level", gate.LEVEL))
    res = gate.headroom(errs, cluster, settled, true_range, minute, bound, a.resamples, level)
    res |= {
        "record": "headroom",
        "condition": condition,
        "split": a.split,
        "dataset_seed": hdr.dataset_seed,
        "dataset_digest": sha256_file(a.truth),
        "ordinals": [a.start, a.count],
        "predictions": {n: sha256_file(p) for n, p in named.items()},
        "imm": a.imm,
        "ekf": a.ekf,
        "bound": None if bound is None else ("true_covariance" if a.mismatch_truth else "nominal"),
        "resamples": a.resamples,
        "git_commit": gp.commit,
        "git_dirty": gp.dirty,
        "seconds": round(time.time() - t0, 1),
    }
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    arrays: dict[str, Any] = {
        "ordinal": cluster,
        "k": ks,
        "settled": settled,
        "minute": minute,
        "true_range_m": true_range,
        **{f"err_{n}": e for n, e in errs.items()},
    }
    if bound is not None:
        arrays["bound"] = bound
    np.savez_compressed(out / "errors.npz", **arrays)
    (out / "headroom.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n")
    for key in ("R", "R_nominal", "robust_over_nominal", "closed_by_robust"):
        if key in res:
            r = res[key]["range"]
            print(f"{key}: {r['value']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}]")
    print(f"wrote {out} [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
