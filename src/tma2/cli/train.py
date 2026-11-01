"""``tma2-train``: train or resume one model of a plan (spec 003 contracts/cli.md)."""

from __future__ import annotations

import argparse
import json
import sys

from tma2.models.train import train
from tma2.types import RecordError, dump_record


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-train")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--data", required=True, help="directory holding the plan's validation split")
    ap.add_argument("--max-wall-s", type=float, default=1e12)
    ap.add_argument("--epochs", type=int, help="override (smoke runs only)")
    ap.add_argument("--scenarios", type=int, help="scenarios per epoch override (smoke runs only)")
    a = ap.parse_args(argv)
    try:
        meta = train(a.plan, a.model, a.checkpoint, a.data, a.max_wall_s, a.epochs, a.scenarios)
    except (OSError, ValueError, RecordError) as e:
        print(f"tma2-train: {e}", file=sys.stderr)
        return 2
    print(json.dumps(dump_record(meta), sort_keys=True))
    return 0
