"""``tma2-hpredict``: the Gate H estimators on one split (spec 010 contracts/cli.md).

Kinds (``headroom.estimators``): ``nominal`` (the plain solve), ``robust`` (the classical robust
control), ``attainable`` and ``realisation`` (the oracle ceilings). ``--segmentation truth`` uses
the true manoeuvres (the gated comparison); ``c2`` uses the classical C″ hand-over (C with the zig
veto and the fixed fade of the Gate H plan), C being run at the nominal σ.

Only the ceilings read the mismatch truth: they refuse to run without ``--mismatch-truth`` on a
split that carries a mismatch, and every other kind refuses to be given it. On a split without a
mismatch the ceilings are the plain solve (the existing oracle), and take no truth file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from tma2.data.provenance import read_git_provenance

CHUNK = 16  # as cli.segment, so C's segmentation is the one tma2-g2predict computes
KNOTS = 12
KIND_NAMES = {0: "steady", 1: "transition", 2: "unknown"}

Task = list[tuple[int, int, list[dict[str, Any]], Any]]


def load_truth(path: str, pack: str) -> tuple[dict[str, Any], Any, Any]:
    """(meta, eng, outlier) of a truth side file, checked against the pack it belongs to."""
    import numpy as np

    from tma2.data.dataset import mismatch_truth_digest
    from tma2.data.f32pack import read_pack_header

    z = np.load(path)
    meta = json.loads(str(z["meta"]))
    hdr = read_pack_header(pack)
    bad = []
    if hdr.mismatch is None:
        bad.append("the split carries no mismatch")
    elif meta["condition"]["id"] != hdr.mismatch.id:
        bad.append("condition differs")
    for key, want in (
        ("dataset_seed", hdr.dataset_seed),
        ("split", str(hdr.split.value if hasattr(hdr.split, "value") else hdr.split)),
        ("index_start", hdr.index_start),
        ("scenario_count", hdr.scenario_count),
        ("generator_git_commit", hdr.generator_git_commit),
    ):
        if meta.get(key) != want:
            bad.append(f"{key} differs")
    if meta["truth_sha256"] != mismatch_truth_digest(z["eng"], z["comp"], z["outlier"]):
        bad.append("truth digest does not match its arrays")
    if bad:
        raise ValueError(f"{path} is not the truth of {pack}: " + "; ".join(bad))
    return meta, z["eng"], z["outlier"]


def c2_parameters(c2: dict[str, Any]) -> dict[str, Any]:
    """C's frozen parameters from the file the plan names, checked against the plan's digest."""
    from tma2.cli.segment import params_digest
    from tma2.types.generated.tma import SegmentParameters

    raw = json.loads(Path(c2["parameters_from"]).read_text())["segmenter"]["parameters"]
    if params_digest(SegmentParameters.model_validate(raw)) != c2["parameters_sha256"]:
        raise ValueError(
            f"{c2['parameters_from']}: not the plan's C parameters (parameters_sha256)"
        )
    out: dict[str, Any] = raw
    return out


def _task(args: tuple[Any, ...]) -> Task:
    import numpy as np
    import torch

    from tma2.cli.oracle import empty_row
    from tma2.gate2.inputs import prefix_inputs
    from tma2.gate2.predict import _row, veto_segmentations
    from tma2.headroom.estimators import RobustSettings, Truth, estimate
    from tma2.headroom.gls import WhitenedLayer
    from tma2.physics.layer import PhysicsLayer
    from tma2.physics.segmentation import LayerInputs
    from tma2.references.classical import BearingData, bearing_data_from_arrays
    from tma2.segment.score import g5_rows, iter_selected
    from tma2.segment.score import oracle as oracle_inputs
    from tma2.types.generated.tma import SegmentParameters

    path, start, count, kind, seg, c2, settings, truth, index_start, plain, batch = args
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    data: list[BearingData] = []
    metas, rows, ords = [], [], []
    for j, m, own, _tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if ks:
            data.append(d)
            metas.append(m)
            rows.append(ks)
            ords.append(j)
    if not data:
        return []
    r_max = max(d.n for d in data)
    out = [[empty_row(d, k) for k in ks] for d, ks in zip(data, rows, strict=True)]
    items: list[tuple[BearingData, int, LayerInputs]] = []
    where: list[tuple[int, int]] = []
    if seg in ("c2", "c2r"):
        p = SegmentParameters.model_validate(c2["parameters"])
        seg_data = data
        if c2.get("segments_from"):
            # The segmentation is computed on another split of the same seed (the clean
            # bearings) and applied to this split's bearings (spec 011 FR-003; a diagnostic).
            other = {
                j: bearing_data_from_arrays(m, own, obs)
                for j, m, own, _tgt, obs in iter_selected(c2["segments_from"], start, count)
            }
            seg_data = [other[j] for j in ords]
            if any(a.n != b.n or a.index != b.index for a, b in zip(seg_data, data, strict=True)):
                raise ValueError("--segments-from: not the same scenarios as --in")
        if seg == "c2r":
            from tma2.gate2.predict import zig_veto_evidence
            from tma2.segment.robust import RobustConfirm, robust_segmentations

            ev = [zig_veto_evidence(d, int(c2["window"])) for d in seg_data]
            sg, _ = robust_segmentations(seg_data, rows, p, RobustConfirm(**c2["cr"]), ev)
        else:
            sg = veto_segmentations(seg_data, rows, p, int(c2["window"]))
        fade = c2["fade"]
    for i, (d, m, ks) in enumerate(zip(data, metas, rows, strict=True)):
        for q, k in enumerate(ks):
            if seg == "truth":
                inp = oracle_inputs(ords[i], m, d, k)
            else:
                ivs = sg[i].get(k)
                inp = None
                if ivs is not None:
                    inp = prefix_inputs(d, k, ivs, c2["mode"], c2.get("open_handover"))
                if inp is not None:
                    age = k - np.arange(len(inp.log_weight))
                    add = np.clip(fade[0] - fade[1] * age, -2.0, 2.0)
                    add[age < 0] = 0.0
                    inp.log_weight = inp.log_weight + add
            if inp is not None:
                items.append((d, k, inp))
                where.append((i, q))
    plain_layer = PhysicsLayer(knots=KNOTS)
    layer = WhitenedLayer(knots=KNOTS)
    rs = RobustSettings(**settings) if settings is not None else None
    for s in range(0, len(items), batch):
        part = items[s : s + batch]
        if plain:
            from tma2.cli.oracle import run_layer

            o = run_layer(plain_layer, part, r_max)
        else:
            tr = None
            if truth is not None:
                eng, outlier = truth
                tr = []
                for i, _q in where[s : s + batch]:
                    pos = int(metas[i]["index"]) - index_start
                    tr.append(Truth(eng[pos], outlier[pos, : data[i].n].astype(bool)))
            o, _info = estimate(layer, part, kind, r_max, tr, rs)
        for b, (i, q) in enumerate(where[s : s + batch]):
            d, k, _ = part[b]
            st = o.state[b].numpy()
            if np.isfinite(st).all():
                rcs = (float(o.range[b]), float(o.course[b]), float(o.speed[b]))
                out[i][q] = _row(d, k, st, rcs, bool(o.plausible[b]), o.cov[b].numpy())
    dump = None
    if seg != "truth" and c2 is not None and c2.get("dump"):
        dump = [
            {
                int(k): [[iv.kind, iv.start, iv.end, bool(iv.open)] for iv in ivs]
                for k, ivs in g.items()
            }
            for g in sg
        ]
    return [
        (j, int(m["index"]), r, None if dump is None else dump[i])
        for i, (j, m, r) in enumerate(zip(ords, metas, out, strict=True))
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-hpredict", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True, help="the split's f32pack")
    ap.add_argument("--kind", required=True)
    ap.add_argument("--segmentation", default="truth", choices=("truth", "c2", "c2r"))
    ap.add_argument("--plan", help="the Gate H plan (robust settings; C'' for --segmentation c2)")
    ap.add_argument("--mismatch-truth", help="the split's truth side file (ceilings only)")
    ap.add_argument(
        "--dump-segmentation", help="c2/c2r: write each prefix's intervals here (ndjson.gz)"
    )
    ap.add_argument("--name", help="the estimator name in the header (default: kind@segmentation)")
    ap.add_argument("--robust-confirm", help="c2r: C-r's settings (a JSON file or object)")
    ap.add_argument(
        "--segments-from",
        help="c2: compute the segmentation on this split of the same seed (a diagnostic)",
    )
    ap.add_argument("--only", help="robust: one fix alone (huber, sigma or whiten)")
    ap.add_argument("--set", action="append", default=[], help="robust: key=value over the plan")
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--batch", type=int, default=32)
    a = ap.parse_args(argv)
    from dataclasses import asdict

    from tma2.data.canonical import canonical_json
    from tma2.data.f32pack import read_pack_header
    from tma2.headroom.estimators import KINDS, settings_from
    from tma2.segment.codeid import code_digest
    from tma2.segment.gate import sha256_file
    from tma2.types import SCHEMA_VERSION
    from tma2.types.generated.tma import HeadroomPredictionHeader, RecordKind

    t0 = time.time()
    gp = read_git_provenance()  # before any output
    hdr = read_pack_header(a.inp)
    condition = hdr.mismatch.id if hdr.mismatch is not None else "off"
    ceiling = a.kind in ("attainable", "realisation")
    bad = []
    if a.kind not in KINDS:
        bad.append(f"--kind {a.kind}: expected one of {', '.join(KINDS)}")
    if ceiling and a.segmentation != "truth":
        bad.append("a ceiling uses the true segmentation")
    if ceiling and hdr.mismatch is not None and not a.mismatch_truth:
        bad.append(f"{a.kind} on a mismatch split needs --mismatch-truth")
    if a.mismatch_truth and not ceiling:
        bad.append(f"{a.kind} must not read the mismatch truth")
    if a.mismatch_truth and hdr.mismatch is None:
        bad.append("the split carries no mismatch; a ceiling there is the plain oracle")
    if (a.kind == "robust" or a.segmentation != "truth") and not a.plan:
        bad.append("--plan is needed for robust and for C's segmentations")
    if a.segments_from and a.segmentation not in ("c2", "c2r"):
        bad.append("--segments-from applies to --segmentation c2 or c2r")
    if (a.segmentation == "c2r") != bool(a.robust_confirm):
        bad.append("--robust-confirm is needed for, and only for, --segmentation c2r")
    if a.segments_from:
        oh = read_pack_header(a.segments_from)
        same = (oh.dataset_seed, oh.index_start, oh.scenario_count) == (
            hdr.dataset_seed,
            hdr.index_start,
            hdr.scenario_count,
        )
        if not same:
            bad.append("--segments-from: a split of another seed or range")
    if (a.only or a.set) and a.kind != "robust":
        bad.append("--only and --set apply to robust")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2
    plan: dict[str, Any] = {}
    plan_sha = None
    if a.plan:
        raw = Path(a.plan).read_bytes()
        plan, plan_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    settings = None
    if a.kind == "robust":
        block = dict(plan["robust"])
        for kv in a.set:
            key, val = kv.split("=", 1)
            block[key] = json.loads(val)
        try:
            settings = asdict(settings_from(block, a.only))
        except (TypeError, ValueError) as e:
            print(f"robust settings: {e}", file=sys.stderr)
            return 2
    c2 = None
    code = None
    cr_json = None
    cr_code = None
    if a.segmentation in ("c2", "c2r"):
        c2 = dict(plan["c2"])
        if a.robust_confirm:
            from tma2.segment.robust import RobustConfirm, robust_code_digest

            txt = a.robust_confirm
            raw_cr = json.loads(txt if txt.lstrip().startswith("{") else Path(txt).read_text())
            try:
                c2["cr"] = asdict(RobustConfirm(**raw_cr))
            except (TypeError, ValueError) as e:
                print(f"--robust-confirm: {e}", file=sys.stderr)
                return 2
            cr_json = json.dumps(c2["cr"], sort_keys=True, separators=(",", ":"))
            cr_code = robust_code_digest()
        try:
            c2["parameters"] = c2_parameters(c2)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        if a.segments_from:
            c2["segments_from"] = a.segments_from
        c2["dump"] = bool(a.dump_segmentation)
        code = code_digest()
        if code != c2["code_sha256"]:
            print(
                "this checkout's segmenter code is not the plan's C (code_sha256)", file=sys.stderr
            )
            return 2
    truth = None
    truth_sha = None
    if a.mismatch_truth:
        try:
            meta, eng, outlier = load_truth(a.mismatch_truth, a.inp)
        except (ValueError, OSError, KeyError) as e:
            print(str(e), file=sys.stderr)
            return 2
        truth, truth_sha = (eng, outlier), meta["truth_sha256"]
    plain = ceiling and hdr.mismatch is None
    name = f"{a.kind}{'-' + a.only if a.only else ''}@{a.segmentation}"
    seg_from = None
    if a.segments_from:
        oc = read_pack_header(a.segments_from).mismatch
        seg_from = oc.id if oc is not None else "off"
        name += f"<{seg_from}"
    name = a.name or name
    h = HeadroomPredictionHeader(
        record=RecordKind.header,
        schema_version=SCHEMA_VERSION,
        estimator=name,
        mode="per_timestep",
        kind=a.kind,
        segmentation=a.segmentation,
        segments_from=seg_from,
        segmenter_settings=cr_json,
        robust_code_sha256=cr_code,
        condition=condition,
        dataset_digest=sha256_file(a.inp),
        truth_sha256=truth_sha,
        settings=json.dumps(settings, sort_keys=True, separators=(",", ":")) if settings else None,
        plan_sha256=plan_sha,
        code_sha256=code,
        knots=KNOTS,
        ordinal_start=a.start,
        ordinal_count=a.count,
        git_commit=gp.commit,
        git_dirty=gp.dirty,
    ).model_dump(mode="json", exclude_none=True)
    chunks = [
        (
            a.inp,
            s,
            min(CHUNK, a.start + a.count - s),
            a.kind,
            a.segmentation,
            c2,
            settings,
            truth,
            hdr.index_start,
            plain,
            a.batch,
        )
        for s in range(a.start, a.start + a.count, CHUNK)
    ]
    recs: Task = []
    if a.workers <= 1:
        for ch in chunks:
            recs += _task(ch)
    else:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for part in ex.map(_task, chunks):
                recs += part
                print(f"{len(recs)} scenarios [{time.time() - t0:.0f} s]", flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(canonical_json(h) + "\n")
        for j, index, rows, _seg in sorted(recs, key=lambda r: r[0]):
            f.write(
                canonical_json(
                    {
                        "record": "prediction",
                        "ordinal": j,
                        "scenario_index": index,
                        "estimator": name,
                        "mode": "per_timestep",
                        "rows": rows,
                    }
                )
                + "\n"
            )
    if a.dump_segmentation:
        import gzip

        dp = Path(a.dump_segmentation)
        dp.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(dp, "wt", encoding="utf-8") as g:
            for j, index, _rows, seg in sorted(recs, key=lambda r: r[0]):
                for k, ivs in sorted((seg or {}).items()):
                    rec = {
                        "record": "segmentation",
                        "ordinal": j,
                        "scenario_index": index,
                        "vessel": "target",
                        "prefix_row": k,
                        "intervals": [
                            {
                                "kind": KIND_NAMES[kind],
                                "start_index": s0,
                                "end_index": e0,
                                "open": op,
                            }
                            for kind, s0, e0, op in ivs
                        ],
                    }
                    g.write(json.dumps(rec) + "\n")
    print(f"wrote {out}: {len(recs)} scenarios [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
