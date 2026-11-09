"""tma2-g4predict: E's prediction file with spec 009's usable uncertainty statement.

    uv run tma2-g4predict --in <E prediction.ndjson> --features <cache.npz>… --plan <g4 plan>
        (--model <id> --run <training dir> [--epoch best|last] | --temperature <temperature.json>)
        --out <file>

Each row of the file's scenarios with a usable covariance gains ``course_arc_rad`` (X),
``course_arc_prob`` (P, through the statement's isotonic map), ``course_conc``, ``course_mix_p``,
``range_ratio_q95`` and ``speed_q95_mps``; every point field is copied unchanged. Rows without a
usable covariance are copied without a statement (scored as not covered). The header gains
``calibration``: the kind, the model id (``<model>-<epoch>`` for a head), the weights' or
temperatures' digest, the plan's digest, and this run's commit and dirty flag (read before anything
is written). Refuses a cache made from other E weights, or a file scenario without cache rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g4predict", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--features", nargs="+", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--model")
    ap.add_argument("--run", help="the model's training directory (weights and meta.json)")
    ap.add_argument("--epoch", choices=("best", "last"), default="best")
    ap.add_argument("--temperature")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if (a.run is None) == (a.temperature is None):
        print("give exactly one of --run and --temperature", file=sys.stderr)
        return 2

    from tma2.calib import data
    from tma2.calib import statement_fit as sf
    from tma2.calib.predict import write_fields
    from tma2.calib.statement import isotonic_apply
    from tma2.data.provenance import read_git_provenance
    from tma2.segment.gate import sha256_file

    g = read_git_provenance()  # before anything is written
    raw = Path(a.plan).read_bytes()
    plan, plan_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    d = data.load(a.features)
    with open(a.inp, encoding="utf-8") as fh:
        ph = json.loads(fh.readline())
        ords = {int(json.loads(line)["ordinal"]) for line in fh}
    uncovered = sorted(ords - set(d.ordinal.tolist()))
    if uncovered:
        print(f"{a.inp}: {len(uncovered)} scenarios have no cache rows, e.g. {uncovered[:5]}",
              file=sys.stderr)  # fmt: skip
        return 2
    if ph.get("weights_sha256") != d.header.get("weights_sha256"):
        print(f"{a.inp}: the cache was made from other E weights", file=sys.stderr)
        return 2
    keep = np.isin(d.ordinal, sorted(ords))
    dropped = int((~keep).sum())
    d = d.select(keep)
    xmax = float(plan["head"]["xmax_rad"])
    if a.run:
        import torch
        from safetensors.torch import load_file

        torch.set_default_dtype(torch.float64)
        run = Path(a.run)
        meta = json.loads((run / "meta.json").read_text())
        head = sf.StatementHead(d.x.shape[1], plan["head"]["width"], plan["head"]["bound"],
                                meta["global"]).double()  # fmt: skip
        w = run / f"{a.epoch}.safetensors"
        head.load_state_dict(load_file(str(w)))
        s = sf.predict_head(head, d)
        iso = meta[f"isotonic_{a.epoch}"]
        cal: dict[str, object] = {
            "kind": "head",
            "model": f"{a.model}-{a.epoch}",
            "weights_sha256": sha256_file(w),
        }
    else:
        t = json.loads(Path(a.temperature).read_text())
        s = sf.apply_temperature(t, d, list(t["slices"]))
        iso = t["isotonic"]
        cal = {"kind": "temperature", "model": "temperature",
               "weights_sha256": sha256_file(a.temperature)}  # fmt: skip
    cal |= {"plan_sha256": plan_sha, "git_commit": g.commit, "git_dirty": g.dirty}
    out = sf.stated(s, d, xmax)
    prob = isotonic_apply(out["p_raw"], (iso["x"], iso["y"]))
    assert d.sd is not None
    kappa = 1.0 / (s.a * d.sd[:, 1]) ** 2
    fields = {}
    for i in np.where(d.scalable & np.isfinite(d.sd).all(axis=1))[0]:
        fields[(int(d.ordinal[i]), float(d.t[i]))] = {
            "course_arc_rad": float(out["x"][i]),
            "course_arc_prob": float(prob[i]),
            "course_conc": float(kappa[i]),
            "course_mix_p": float(s.p[i]),
            "range_ratio_q95": float(out["q_r"][i]),
            "speed_q95_mps": float(out["q_s"][i]),
        }
    n = write_fields(Path(a.inp), Path(a.out), fields, cal)
    print(json.dumps({"rows_stated": n, "cache_rows_outside_file": dropped, "out": a.out, **cal}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
