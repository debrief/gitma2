"""tma2-segtrain: L's training data and training (spec 005 T032–T033).

    uv run tma2-segtrain tables --in <split.f32pack> --plan <gs-plan.json> --start S --count N
        [--sigma1] --out <shard.npz> [--workers 4]
    uv run tma2-segtrain train --plan <gs-plan.json> --model segL-s1|segL-s2|segL-s3|segL-shuffled
        --train <shard.npz>... --val <val.npz> --checkpoint <dir> [--epochs E] [--max-wall-s T]

``tables`` writes one example per scenario with a scored row: the cost table, truth codes per
prefix and causal features (``segment/train.py``). Without ``--sigma1``, S and N are file
positions (every σ); with it, σ = 1° ordinals. ``train`` trains or resumes one model; the
checkpoint folder holds weights, Adam state, the best weights and ``meta.json`` (CheckpointMeta,
weights bound by SHA-256). Training refuses tables made with other segmenter parameters.
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

from tma2.cli.segment import file_digest, params_digest
from tma2.data.provenance import read_git_provenance
from tma2.types.generated.tma import SegmentParameters

CHUNK = 8


def plan_parameters(plan: dict[str, Any]) -> SegmentParameters:
    return SegmentParameters.model_validate(plan["segmenter"]["parameters"])


def _tables_task(args: tuple[str, int, int, bool, str]) -> list[Any]:
    import torch

    from tma2.segment.train import iter_scenarios, make_example

    torch.set_num_threads(1)
    path, start, count, s1, pj = args
    p = SegmentParameters.model_validate_json(pj)
    out = []
    for key, meta, own, _tgt, obs in iter_scenarios(path, start, count, s1):
        ex = make_example(key, meta, own, obs, p)
        if ex is not None:
            out.append(ex)
    return out


def cmd_tables(a: argparse.Namespace) -> int:
    from tma2.segment.train import save_examples

    plan = json.loads(Path(a.plan).read_text())
    p = plan_parameters(plan)
    t0 = time.time()
    chunks = [
        (a.input, s, min(CHUNK, a.start + a.count - s), a.sigma1, p.model_dump_json())
        for s in range(a.start, a.start + a.count, CHUNK)
    ]
    with ProcessPoolExecutor(a.workers) as ex:
        examples = [e for part in ex.map(_tables_task, chunks) for e in part]
    gp = read_git_provenance()
    commit, dirty = gp.commit, gp.dirty
    header = {
        "plan_id": plan["id"],
        "parameters_sha256": params_digest(p),
        "dataset": str(a.input),
        "dataset_digest": file_digest(a.input),
        "start": a.start,
        "count": a.count,
        "sigma1_only": bool(a.sigma1),
        "examples": len(examples),
        "git_commit": commit,
        "git_dirty": dirty,
        "seconds": round(time.time() - t0, 1),
    }
    save_examples(a.out, examples, header)
    print(json.dumps(header))
    return 0


def cmd_train(a: argparse.Namespace) -> int:
    from tma2.segment.train import config_from_plan, load_examples, train_l

    raw = Path(a.plan).read_bytes()
    plan = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    p = plan_parameters(plan)
    want = params_digest(p)
    train: list[Any] = []
    for path in a.train:
        h, exs = load_examples(path)
        if h["parameters_sha256"] != want:
            print(f"{path}: tables made with other segmenter parameters", file=sys.stderr)
            return 2
        train += exs
    hv, val = load_examples(a.val)
    if hv["parameters_sha256"] != want:
        print(f"{a.val}: tables made with other segmenter parameters", file=sys.stderr)
        return 2
    cfg = config_from_plan(plan, digest, a.model)
    meta = train_l(cfg, p, train, val, a.checkpoint, max_wall_s=a.max_wall_s, epochs=a.epochs)
    print(json.dumps({"model": a.model, "epoch": meta.epoch, "complete": meta.complete}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-segtrain")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tables")
    t.add_argument("--in", dest="input", required=True)
    t.add_argument("--plan", required=True)
    t.add_argument("--start", type=int, required=True)
    t.add_argument("--count", type=int, required=True)
    t.add_argument("--sigma1", action="store_true")
    t.add_argument("--out", required=True)
    t.add_argument("--workers", type=int, default=4)
    r = sub.add_parser("train")
    r.add_argument("--plan", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--train", nargs="+", required=True)
    r.add_argument("--val", required=True)
    r.add_argument("--checkpoint", required=True)
    r.add_argument("--epochs", type=int)
    r.add_argument("--max-wall-s", type=float, default=1e12)
    a = ap.parse_args(argv)
    return cmd_tables(a) if a.cmd == "tables" else cmd_train(a)


if __name__ == "__main__":
    raise SystemExit(main())
