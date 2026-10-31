"""``tma2-eval``: score prediction files against a truth split (gitma's ``tma-eval`` layouts plus
efficiency)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tma2.data.canonical import canonical_json
from tma2.data.io import AtomicFile
from tma2.eval.errors import Truth
from tma2.eval.metrics import CURVE_COLUMNS, METRIC_COLUMNS, PredictionSet, evaluate, to_csv
from tma2.eval.predictions import check_bound, iter_predictions_raw
from tma2.types import RecordError, parse_record

from .estimators import open_split


def load_prediction_set(path: str, truth: str) -> PredictionSet:
    header = check_bound(path, truth)
    by_index = {int(p["scenario_index"]): p for _, p in iter_predictions_raw(path)}
    mode = str(getattr(header.mode, "value", header.mode))
    label = header.estimator + (":per_timestep" if mode == "per_timestep" else "")
    return PredictionSet(label=label, estimator=header.estimator, by_index=by_index, mode=mode)


def load_crb(path: str) -> dict[int, dict[str, Any]]:
    from tma2.types.generated.tma import CrbHeader, CrbRecord

    out: dict[int, dict[str, Any]] = {}
    with open(path, encoding="utf-8") as f:
        parse_record(CrbHeader, json.loads(f.readline()), path, 1)
        for n, line in enumerate(f, start=2):
            rec = parse_record(CrbRecord, json.loads(line), path, n)
            out[rec.scenario_index] = rec.model_dump()
    return out


def crb_lookup_from(crb: dict[int, dict[str, Any]]) -> Any:
    def lookup(truth: Truth, row: int) -> tuple[float, float, float, bool] | None:
        rec = crb.get(truth.index)
        if rec is None:
            return None
        j = row - int(rec["first_row"])
        if j < 0 or j >= len(rec["sd_range_rel"]):
            return None
        if rec["singular"][j]:
            return (float("nan"), float("nan"), float("nan"), True)
        a, b, c = rec["sd_range_rel"][j], rec["sd_course_deg"][j], rec["sd_speed_kt"][j]
        return (float(a), float(b), float(c), False)

    return lookup


def write_outputs(
    out_dir: Path, metrics: list[dict[str, Any]], curves: list[dict[str, Any]]
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in (
        ("metrics.csv", to_csv(METRIC_COLUMNS, metrics)),
        ("metrics.json", canonical_json(metrics) + "\n"),
        ("curves.csv", to_csv(CURVE_COLUMNS, curves)),
    ):
        f = AtomicFile(out_dir / name)
        f.write(text.encode("utf-8"))
        f.commit()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-eval")
    ap.add_argument("--truth", required=True)
    ap.add_argument("--predictions", nargs="+", required=True)
    ap.add_argument("--crb")
    ap.add_argument("--points", default="300")
    ap.add_argument("--curve-step", type=int, default=60)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        points = tuple(int(p) for p in a.points.split(",") if p)
        sets = [load_prediction_set(p, a.truth) for p in a.predictions]
        _, blocks = open_split(a.truth)
        truths = (Truth.from_block(meta, own, tgt) for _, meta, own, tgt, _obs in blocks)
        lookup = crb_lookup_from(load_crb(a.crb)) if a.crb else None
        ev = evaluate(truths, sets, points, a.curve_step, lookup)
    except (RecordError, ValueError, OSError) as e:
        print(f"tma2-eval: {e}", file=sys.stderr)
        return 2
    write_outputs(Path(a.out), ev.metrics, ev.curves)
    overall = [m for m in ev.metrics if m["slice"] == "overall"]
    print(
        json.dumps(
            {
                "out": a.out,
                "estimators": [s.label for s in sets],
                "records": len(ev.metrics),
                "overall": overall,
            }
        )
    )
    return 0
