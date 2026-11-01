"""``tma2-predict``: per-timestep predictions of a trained model on a split."""

from __future__ import annotations

import argparse
import json
import sys

from tma2.models.predict import load_model, predict_split
from tma2.types import RecordError


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-predict")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--model", required=True, help="model id in the plan")
    ap.add_argument("--checkpoint", required=True, help="checkpoint folder (best weights used)")
    ap.add_argument("--truth", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, help="first N scenarios only (diagnostics)")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args(argv)
    import torch

    torch.set_num_threads(a.threads)
    try:
        model = load_model(a.plan, a.model, a.checkpoint)
        n = predict_split(model, a.truth, a.out, a.limit, log=lambda m: None)
    except (OSError, ValueError, RecordError) as e:
        print(f"tma2-predict: {e}", file=sys.stderr)
        return 2
    print(json.dumps({"out": a.out, "model": a.model, "scenarios": n}))
    return 0
