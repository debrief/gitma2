"""tma2-g2train: E-w's training data and training (spec 007 T015).

    uv run tma2-g2train tables --in <split.f32pack> --segmentations <C.ndjson> --plan <plan.json>
        --start S --count N --out <shard.npz>
    uv run tma2-g2train train --plan <plan.json> --model <id> --train <shard.npz>...
        --val <val.npz> --checkpoint <dir> [--epochs E] [--max-wall-s T]

The plan (``configs/gate2/<id>.json``) names C (``c_parameters_sha256``, ``c_code_sha256``,
``mode``, ``open_handover``), the encoder (``encoder``: PhysicsModelConfig fields), the training
settings (``training``) and the models (``models``: id → seed, shuffled). ``tables`` refuses a
segmentation file whose parameter or code digest differs from the plan's; ``train`` refuses
tables made from another plan.
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
    a = ap.parse_args(argv)
    return tables(a) if a.cmd == "tables" else train(a)


if __name__ == "__main__":
    raise SystemExit(main())
