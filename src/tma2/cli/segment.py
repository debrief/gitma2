"""tma2-segment: segment the target on every scored prefix of the selected scenarios (spec 005
contracts/cli.md).

    uv run tma2-segment --in <split.f32pack> --out <seg.ndjson> [--segmenter C | L --weights
        <best.safetensors> --plan <gs-plan.json>]
        [--params <SegmentParameters json>] [--set key=value …] [--glr-tune START:COUNT]
        [--start S --count N] [--rows g5|last] [--workers 4] [--allow-dirty]

Scenarios are the σ = 1° ones in file order (ordinals, note 08's selection). ``--glr-tune`` sets
the GLR nominator's threshold to the ``nominator_far`` exceedance of held-leg rows on the
tuning ordinals (note 08's rule; held rows: settled rows from row ``window_rows`` on). The output
is a header (provenance, parameters, configuration digest) and one Segmentation per scenario and
scored row, ordered by ordinal and row; each worker runs torch on one thread.
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

import numpy as np

from tma2.data.provenance import read_git_provenance
from tma2.types import SCHEMA_VERSION
from tma2.types.generated.tma import (
    RecordKind,
    SegmentationHeader,
    SegmentParameters,
)

CHUNK = 16


def params_digest(p: SegmentParameters) -> str:
    return hashlib.sha256(
        json.dumps(p.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()


def file_digest(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _glr_task(args: tuple[str, int, int, int, int]) -> list[float]:
    import torch

    from tma2.eval.rows import settled_row
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment.score import iter_selected
    from tma2.segment.segmenter import glr

    path, start, count, window, w_rows = args
    torch.set_num_threads(1)
    vals: list[float] = []
    for _j, m, own, _tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        s = glr(d, window)
        vals += [float(s[k]) for k in range(w_rows, d.n) if settled_row(m, k)]
    return vals


def tune_glr(path: str, start: int, count: int, p: SegmentParameters, workers: int) -> float:
    from tma2.detect.controls import tune_threshold

    chunks = [
        (path, s, min(CHUNK, start + count - s), p.glr_window, p.window_rows)
        for s in range(start, start + count, CHUNK)
    ]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        vals = [v for part in ex.map(_glr_task, chunks) for v in part]
    h, _f = tune_threshold(np.asarray(vals), p.nominator_far)
    return float(h)


def _segment_task(args: tuple[str, int, int, str, str, str, str]) -> list[dict[str, Any]]:
    import torch

    from tma2.physics.layer import PhysicsLayer
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment import CODE_KIND
    from tma2.segment.score import g5_rows, iter_selected
    from tma2.segment.segmenter import segment

    path, start, count, params_json, rows_mode, weights, net_json = args
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    p = SegmentParameters.model_validate_json(params_json)
    data, metas, rows, ords, owns = [], [], [], [], []
    for j, m, own, _tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n) if rows_mode == "g5" else [d.n - 1]
        if not ks:
            continue
        owns.append(own)
        data.append(d)
        metas.append(m)
        rows.append(ks)
        ords.append(j)
    if not data:
        return []
    evidence = None
    if weights:
        from safetensors.torch import load_file

        from tma2.segment.evidence import EvidenceNet, evidence_for, scenario_features

        cfg = json.loads(net_json)
        net = EvidenceNet(
            width=int(cfg["width"]), kernel=int(cfg["kernel"]), dilations=tuple(cfg["dilations"])
        ).double()
        net.load_state_dict(load_file(weights))
        net.eval()
        feats = [scenario_features(d, own, p) for d, own in zip(data, owns, strict=True)]
        evidence = evidence_for(net, feats)
    segs = segment(PhysicsLayer(), data, metas, rows, p, evidence=evidence)
    out = []
    for j, m, sg in zip(ords, metas, segs, strict=True):
        for ps in sg:
            out.append(
                {
                    "record": RecordKind.segmentation.value,
                    "ordinal": j,
                    "scenario_index": int(m["index"]),
                    "vessel": "target",
                    "prefix_row": ps.k,
                    "intervals": [
                        {
                            "kind": CODE_KIND[iv.kind].value,
                            "start_index": iv.start,
                            "end_index": iv.end,
                            "open": iv.open,
                        }
                        for iv in ps.intervals
                    ],
                    "cost": ps.cost,
                    "margin": ps.margin,
                }
            )
    return out


def main(argv: list[str] | None = None) -> int:
    from tma2.segment import default_parameters

    ap = argparse.ArgumentParser(prog="tma2-segment")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--segmenter", default="C", choices=["C", "L"])
    ap.add_argument("--weights", help="L: the evidence network's best.safetensors")
    ap.add_argument("--plan", help="L: the plan naming the evidence network's configuration")
    ap.add_argument("--params")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--glr-tune", metavar="START:COUNT")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=1 << 30)
    ap.add_argument("--rows", choices=["g5", "last"], default="g5")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args(argv)
    gp = read_git_provenance()
    commit, dirty = gp.commit, gp.dirty
    if dirty and not a.allow_dirty:
        print("refusing: the working tree is dirty (--allow-dirty records it)", file=sys.stderr)
        return 2
    p = (
        SegmentParameters.model_validate_json(Path(a.params).read_text())
        if a.params
        else default_parameters()
    )
    upd: dict[str, Any] = {}
    for kv in a.set:
        key, _, val = kv.partition("=")
        if key not in SegmentParameters.model_fields:
            print(f"unknown parameter {key}", file=sys.stderr)
            return 2
        upd[key] = json.loads(val)
    p = SegmentParameters.model_validate({**p.model_dump(), **upd})
    if (a.segmenter == "L") != bool(a.weights and a.plan):
        print("--segmenter L needs --weights and --plan (and C takes neither)", file=sys.stderr)
        return 2
    net_json = ""
    sha = params_digest(p)
    if a.weights:
        net_json = json.dumps(json.loads(Path(a.plan).read_text())["evidence_network"])
        sha = hashlib.sha256(f"{sha}:{file_digest(a.weights)}:{net_json}".encode()).hexdigest()
    t0 = time.time()
    if a.glr_tune:
        s, _, c = a.glr_tune.partition(":")
        h = tune_glr(a.inp, int(s), int(c), p, a.workers)
        p = p.model_copy(update={"glr_threshold": h})
        print(
            f"GLR threshold {h:.4f} at nominator_far {p.nominator_far} [{time.time() - t0:.0f} s]"
        )
    header = SegmentationHeader(
        record=RecordKind.header,
        schema_version=SCHEMA_VERSION,
        segmenter=a.segmenter,
        segmenter_sha256=sha if a.weights else params_digest(p),
        dataset_digest=file_digest(a.inp),
        parameters=p,
        git_commit=commit,
        git_dirty=dirty,
    )
    chunks = [
        (a.inp, s, CHUNK, p.model_dump_json(), a.rows, a.weights or "", net_json)
        for s in range(a.start, a.start + min(a.count, 1 << 20), CHUNK)
        if s < a.start + a.count
    ]
    chunks = [(x[0], x[1], min(CHUNK, a.start + a.count - x[1]), *x[3:]) for x in chunks]
    recs: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for part in ex.map(_segment_task, chunks):
            if not part and recs:
                break  # past the last σ = 1° scenario
            recs += part
            print(
                f"{len({r['ordinal'] for r in recs})} scenarios [{time.time() - t0:.0f} s]",
                flush=True,
            )
    recs.sort(key=lambda r: (r["ordinal"], r["prefix_row"]))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(header.model_dump_json() + "\n")
        for r in recs:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {out}: {len(recs)} segmentations [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
