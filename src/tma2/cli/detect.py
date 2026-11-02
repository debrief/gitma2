"""``tma2-detect``: per-timestep detector outputs (spec 004 contracts/cli.md)."""

from __future__ import annotations

import argparse
import json
import sys

from tma2.models.detector_inputs import KNOT_THRESHOLD
from tma2.models.detector_predict import detect_split, load_detector
from tma2.types import RecordError


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-detect")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--model", required=True, help="detector id in the plan")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--knot-threshold", type=float, default=KNOT_THRESHOLD)
    a = ap.parse_args(argv)
    try:
        model = load_detector(a.plan, a.model, a.checkpoint)
        n = detect_split(model, a.truth, a.out, a.limit, threshold=a.knot_threshold)
    except (OSError, ValueError, RecordError) as e:
        print(f"tma2-detect: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"scenarios": n, "out": a.out, "weights_digest": model.weights_digest}))
    return 0
