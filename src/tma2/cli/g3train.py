"""tma2-g3train: the calibration head and its classical control (spec 008 contracts/cli.md).

    uv run tma2-g3train head --plan <g3 plan> --model <id> --train <cache.npz>… --val <cache.npz>…
        --checkpoint <dir> [--epochs N] [--max-wall-s S]
    uv run tma2-g3train temperature --plan <g3 plan> --val <cache.npz>… --out <temperature.json>

The plan (``configs/gate3/<id>.json``) holds ``head`` (a CalibrationHeadConfig without the seed),
``temperature`` (a TemperatureConfig), ``models`` ({id: {seed, shuffled}}) and
``tuning_ordinals`` [a, b): the validation rows used for early stopping and for the
temperature fit. Caches come from ``tma2-g2predict --features`` and must all be the carried E's.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from tma2.data.provenance import read_git_provenance


def _plan(path: str) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _tuning(plan: dict[str, Any], d: Any) -> Any:
    a, b = plan["tuning_ordinals"]
    return d.select((d.ordinal >= a) & (d.ordinal < b))


def head(a: argparse.Namespace) -> int:
    from tma2.calib import data
    from tma2.calib.train import train_head
    from tma2.types.generated.tma import CalibrationHeadConfig

    gp = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    m = plan["models"].get(a.model)
    if m is None:
        print(f"{a.model} is not in the plan", file=sys.stderr)
        return 2
    cfg = CalibrationHeadConfig.model_validate(
        {**plan["head"], "seed": m["seed"], "shuffled": bool(m.get("shuffled"))}
    )
    tr = data.load(a.train)
    val = _tuning(plan, data.load(a.val))
    if tr.header.get("weights_sha256") != val.header.get("weights_sha256"):
        print("training and validation caches are from different E weights", file=sys.stderr)
        return 2
    meta = train_head(
        cfg,
        tr,
        val,
        Path(a.checkpoint),
        {
            "git_commit": gp.commit,
            "git_dirty": gp.dirty,
            "plan_sha256": plan_sha,
            "e_weights_sha256": tr.header.get("weights_sha256"),
            "train_rows": len(tr),
            "val_rows": len(val),
        },
        a.epochs,
        a.max_wall_s,
    )
    print(json.dumps({"model": a.model, "epoch": meta["epoch"], "complete": meta["complete"]}))
    return 0


def temperature(a: argparse.Namespace) -> int:
    from tma2.calib import data
    from tma2.calib.temperature import fit
    from tma2.types.generated.tma import TemperatureConfig

    gp = read_git_provenance()
    plan, plan_sha = _plan(a.plan)
    cfg = TemperatureConfig.model_validate(plan["temperature"])
    val = _tuning(plan, data.load(a.val))
    temps = fit(cfg, val)
    rec = {
        "slices": list(cfg.slices or []),
        "temperatures": temps,
        "plan_sha256": plan_sha,
        "e_weights_sha256": val.header.get("weights_sha256"),
        "rows": len(val),
        "git_commit": gp.commit,
        "git_dirty": gp.dirty,
    }
    Path(a.out).write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(temps))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g3train", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("head")
    h.add_argument("--plan", required=True)
    h.add_argument("--model", required=True)
    h.add_argument("--train", nargs="+", required=True)
    h.add_argument("--val", nargs="+", required=True)
    h.add_argument("--checkpoint", required=True)
    h.add_argument("--epochs", type=int)
    h.add_argument("--max-wall-s", type=float)
    t = sub.add_parser("temperature")
    t.add_argument("--plan", required=True)
    t.add_argument("--val", nargs="+", required=True)
    t.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return head(a) if a.cmd == "head" else temperature(a)


if __name__ == "__main__":
    raise SystemExit(main())
