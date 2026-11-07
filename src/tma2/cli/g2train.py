"""tma2-g2train: E-w's training data and training (spec 007 T015).

    uv run tma2-g2train tables --in <split.f32pack> --segmentations <C.ndjson> --plan <plan.json>
        --start S --count N --out <shard.npz>
    uv run tma2-g2train train --plan <plan.json> --model <id> --train <shard.npz>...
        --val <val.npz> --checkpoint <dir> [--epochs E] [--max-wall-s T]
    uv run tma2-g2train es --plan <plan.json> --model <id> --data <stream.f32pack>
        --tables <dtables shard.npz>... --val-data <val.f32pack> --val-tables <npz>...
        --checkpoint <dir> [--epochs E] [--max-wall-s T] [--workers 4]

The plan (``configs/gate2/<id>.json``) names C (``c_parameters_sha256``, ``c_code_sha256``,
``mode``, ``open_handover``), the encoder (``encoder``: PhysicsModelConfig fields), the training
settings (``training``) and the models (``models``: id → seed, shuffled). ``tables`` refuses a
segmentation file whose parameter or code digest differs from the plan's; ``train`` refuses
tables made from another plan. ``es`` trains E-s (``gate2.es``; plan ``es``: ESSettings fields)
on ``tma2-dtables`` tables, with spec 005's features computed from the split (refusing tables
made for another C, by the digest of the plan's ``c`` block, or from another split).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

from tma2.data.provenance import read_git_provenance


def _plan(path: str) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _cpu() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def tables(a: argparse.Namespace) -> int:
    import torch

    from tma2.cli.gs import read_segmentations
    from tma2.gate2.train import build_prefixes, save_prefixes
    from tma2.segment.gate import sha256_file

    torch.set_default_dtype(torch.float64)
    gp = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    header, segs = read_segmentations(a.segmentations)
    c = plan["c"]
    for key, want in (
        ("segmenter_sha256", c["parameters_sha256"]),
        ("code_sha256", c["code_sha256"]),
    ):
        if header.get(key) != want:
            print(f"{a.segmentations}: {key} is not the plan's C", file=sys.stderr)
            return 2
    xs = build_prefixes(a.inp, segs, a.start, a.count, c["mode"], c.get("open_handover"))
    save_prefixes(
        a.out,
        xs,
        {
            "plan_sha256": plan_sha,
            "dataset_digest": sha256_file(a.inp),
            "segmentations_sha256": sha256_file(a.segmentations),
            "start": a.start,
            "count": a.count,
            "prefixes": len(xs),
            "git_commit": gp.commit,
            "git_dirty": gp.dirty,
        },
    )
    print(json.dumps({"prefixes": len(xs), "out": a.out}))
    return 0


def train(a: argparse.Namespace) -> int:
    from tma2.gate2.train import TrainSettings, load_prefixes, train_ew
    from tma2.types.generated.tma import PhysicsModelConfig

    gp = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    if a.model not in plan["models"]:
        print(f"{a.model} is not in the plan", file=sys.stderr)
        return 2
    xs: list[Any] = []
    val: list[Any] = []
    for p in [*a.train, a.val]:
        h, part = load_prefixes(p)
        if h["plan_sha256"] != plan_sha:
            print(f"{p}: made from another plan", file=sys.stderr)
            return 2
        (val if p == a.val else xs).extend(part)
    m = plan["models"][a.model]
    cfg = PhysicsModelConfig.model_validate({**plan["encoder"], "id": a.model, "seed": m["seed"]})
    st = TrainSettings(
        **{**plan["training"], "seed": m["seed"], "shuffled": bool(m.get("shuffled"))}
    )
    meta = train_ew(
        cfg,
        st,
        xs,
        val,
        Path(a.checkpoint),
        {
            "git_commit": gp.commit,
            "git_dirty": gp.dirty,
            "cpu_model": _cpu(),
            "plan_sha256": plan_sha,
        },
        a.epochs,
        a.max_wall_s,
    )
    print(json.dumps({"model": a.model, "epoch": meta["epoch"], "complete": meta["complete"]}))
    return 0


def _feats_task(args: tuple[str, int, int, str]) -> dict[int, Any]:
    import torch

    from tma2.references.classical import bearing_data_from_arrays
    from tma2.segment.evidence import scenario_features
    from tma2.segment.score import iter_selected
    from tma2.types.generated.tma import SegmentParameters

    path, start, count, params_json = args
    torch.set_num_threads(1)
    p = SegmentParameters.model_validate_json(params_json)
    out = {}
    for j, m, own, _tgt, obs in iter_selected(path, start, count):
        out[j] = scenario_features(bearing_data_from_arrays(m, own, obs), own, p)
    return out


def _es_examples(
    split: str, tables: list[str], c_sha: str, params_json: str, workers: int
) -> tuple[list[Any], str | None]:
    from concurrent.futures import ProcessPoolExecutor

    from tma2.gate2.es import example_of
    from tma2.gate2.tables import load_tables
    from tma2.segment.gate import sha256_file

    digest = sha256_file(split)
    tabs: dict[int, Any] = {}
    for t in tables:
        h, part = load_tables(t)
        if h.get("plan_c_sha256") != c_sha:
            return [], f"{t}: made for another C (the plan's c block)"
        if h.get("dataset_digest") != digest:
            return [], f"{t}: made from another split than {split}"
        tabs.update(part)
    ords = sorted(tabs)
    if not ords:
        return [], None
    chunks = [
        (split, s, min(64, ords[-1] + 1 - s), params_json) for s in range(ords[0], ords[-1] + 1, 64)
    ]
    feats: dict[int, Any] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for part in ex.map(_feats_task, chunks):
            feats.update(part)
    return [example_of(j, feats[j], tabs[j]) for j in ords], None


def es(a: argparse.Namespace) -> int:
    import time

    from tma2.gate2.es import ESSettings, train_es
    from tma2.types.generated.tma import SegmentParameters

    t_start = time.time()
    gp = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    m = plan["models"].get(a.model)
    if m is None or m.get("kind") != "es":
        print(f"{a.model} is not an E-s model of the plan", file=sys.stderr)
        return 2
    seg_plan = json.loads(Path(plan["c"]["parameters_from"]).read_text())
    p = SegmentParameters.model_validate(seg_plan["segmenter"]["parameters"])
    from tma2.gate2.tables import c_block_sha256

    c_sha = c_block_sha256(plan)
    train, err = _es_examples(a.data, a.tables, c_sha, p.model_dump_json(), a.workers)
    val, err2 = _es_examples(a.val_data, a.val_tables, c_sha, p.model_dump_json(), a.workers)
    if err or err2:
        print(err or err2, file=sys.stderr)
        return 2
    st = ESSettings(**{**plan["es"], "seed": m["seed"], "shuffled": bool(m.get("shuffled"))})
    meta = train_es(
        st,
        train,
        val,
        Path(a.checkpoint),
        {
            "git_commit": gp.commit,
            "git_dirty": gp.dirty,
            "cpu_model": _cpu(),
            "plan_sha256": plan_sha,
        },
        a.epochs,
        # the job's budget includes the feature pre-pass
        None if a.max_wall_s is None else a.max_wall_s - (time.time() - t_start),
    )
    print(json.dumps({"model": a.model, "epoch": meta["epoch"], "complete": meta["complete"]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g2train", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tables")
    t.add_argument("--in", dest="inp", required=True)
    t.add_argument("--segmentations", required=True)
    t.add_argument("--plan", required=True)
    t.add_argument("--start", type=int, required=True)
    t.add_argument("--count", type=int, required=True)
    t.add_argument("--out", required=True)
    r = sub.add_parser("train")
    r.add_argument("--plan", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--train", nargs="+", required=True)
    r.add_argument("--val", required=True)
    r.add_argument("--checkpoint", required=True)
    r.add_argument("--epochs", type=int)
    r.add_argument("--max-wall-s", type=float)
    e = sub.add_parser("es")
    e.add_argument("--plan", required=True)
    e.add_argument("--model", required=True)
    e.add_argument("--data", required=True)
    e.add_argument("--tables", nargs="+", required=True)
    e.add_argument("--val-data", required=True)
    e.add_argument("--val-tables", nargs="+", required=True)
    e.add_argument("--checkpoint", required=True)
    e.add_argument("--epochs", type=int)
    e.add_argument("--max-wall-s", type=float)
    e.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    return {"tables": tables, "train": train, "es": es}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
