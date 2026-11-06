"""tma2-dtables: E-s's decision tables (spec 007 research R2; T017, contracts/cli.md).

    uv run tma2-dtables --in <split.f32pack> --segmentations <C.ndjson> --plan <plan.json>
        --start S --count N --out <tables.npz> [--workers 4]

Re-runs C's confirmation on each σ = 1° scenario of [S, S + N) in the chunks ``tma2-segment``
uses (16 scenarios, padded to the longest), so a shard equal to the segmentation run's shard
reproduces C; scenarios whose re-run differs from the segmentation file at a scored row are
counted in the header (``c_mismatch_rows``). Every decision is recorded, and every decision that
evidence could flip gets its downstream errors with and without it (``gate2.tables``).

Refuses a segmentation file whose parameter or code digest is not the plan's C, and code whose
digest is not the plan's (the tables must be C's decisions).
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

CHUNK = 16  # as cli.segment


def _task(args: tuple[Any, ...]) -> tuple[dict[int, Any], int, int]:
    import torch

    from tma2.gate2.tables import c_confirmations, scenario_table, truth_and_bounds
    from tma2.physics.layer import PhysicsLayer
    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment.score import g5_rows, iter_selected
    from tma2.segment.segmenter import intervals_at
    from tma2.types.generated.tma import SegmentParameters

    path, start, count, params_json, mode, handover, segs, cap = args
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    p = SegmentParameters.model_validate_json(params_json)
    items = []
    for j, m, own, tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if ks:
            items.append((j, m, own, tgt, obs, d, ks))
    if not items:
        return {}, 0, 0
    layer = PhysicsLayer()
    data = [it[5] for it in items]
    r_max = max(d.n for d in data)
    confs = c_confirmations(layer, data, [it[6][0] for it in items], p)
    out: dict[int, Any] = {}
    mismatched = checked = 0
    for (j, m, own, tgt, obs, d, ks), conf in zip(items, confs, strict=True):
        for k in ks:
            if (j, k) in segs:
                checked += 1
                mismatched += intervals_at(conf, k, p) != segs[(j, k)]
        kept, truth, bound = truth_and_bounds(m, own, tgt, obs, ks)
        out[j] = scenario_table(
            layer, d, conf, kept, truth, bound, p, mode, handover, cap, r_max=r_max
        )
    return out, mismatched, checked


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-dtables", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--segmentations", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)

    from tma2.cli.gs import read_segmentations
    from tma2.segment.codeid import code_digest
    from tma2.segment.gate import sha256_file
    from tma2.types.generated.tma import RecordKind, SegmentParameters

    t0 = time.time()
    gp = read_git_provenance()  # before any output (gotcha: provenance first)
    raw = Path(a.plan).read_bytes()
    plan, plan_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    c = plan["c"]
    header, segs = read_segmentations(a.segmentations)
    bad = [
        f"{a.segmentations}: {key} is not the plan's C"
        for key, want in (
            ("segmenter_sha256", c["parameters_sha256"]),
            ("code_sha256", c["code_sha256"]),
        )
        if header.get(key) != want
    ]
    if code_digest() != c["code_sha256"]:
        bad.append("this checkout's segmenter code is not the plan's C (code_sha256)")
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 2
    p = SegmentParameters.model_validate(header["parameters"])
    from tma2.gate2.tables import CAP, c_block_sha256

    cap = CAP
    chunks = [
        (
            a.inp,
            s,
            min(CHUNK, a.start + a.count - s),
            p.model_dump_json(),
            c["mode"],
            c.get("open_handover"),
            {key: v for key, v in segs.items() if s <= key[0] < s + CHUNK},
            cap,
        )
        for s in range(a.start, a.start + a.count, CHUNK)
    ]
    tables: dict[int, Any] = {}
    mismatched = checked = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for part, mm, ck in ex.map(_task, chunks):
            tables.update(part)
            mismatched += mm
            checked += ck
            print(f"{len(tables)} scenarios [{time.time() - t0:.0f} s]", flush=True)
    from tma2.gate2.tables import save_tables
    from tma2.types.generated.tma import DecisionTableHeader

    h = DecisionTableHeader(
        record=RecordKind.header,
        schema_version=header["schema_version"],
        dataset_digest=sha256_file(a.inp),
        parameters_sha256=c["parameters_sha256"],
        code_sha256=c["code_sha256"],
        ordinals=[a.start, a.start + a.count - 1],
        decisions=sum(len(t.decisions) for t in tables.values()),
        git_commit=gp.commit,
        git_dirty=gp.dirty,
    ).model_dump(mode="json", exclude_none=True)
    h |= {
        "plan_c_sha256": c_block_sha256(plan),
        "plan_sha256_at_build": plan_sha,  # informational: the plan names these tables
        "segmentations_sha256": sha256_file(a.segmentations),
        "decision_rows": sum(len(t.rows) for t in tables.values()),
        "c_checked_rows": checked,
        "c_mismatch_rows": mismatched,
    }
    save_tables(a.out, tables, h)
    print(json.dumps({k: h[k] for k in ("decisions", "decision_rows", "c_mismatch_rows")}))
    print(f"wrote {a.out} [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
