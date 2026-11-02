"""Detection metrics (spec 004 FR-028, R8)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tma2.detect.matching import (
    ece,
    episodes,
    match_one_to_one,
    score_scenario,
    summary,
    truth_boundaries,
)


def _meta(spans: list[tuple[str, int, int]], n: int = 200, zig: int = 20) -> dict[str, Any]:
    return {
        "index": 7,
        "samples": n,
        "zig_index": zig,
        "parameters": {"dt_s": 10.0, "noise_sigma_rad": math.pi / 180},
        "manoeuvres": [{"kind": k, "start_index": a, "end_index": b} for k, a, b in spans],
    }


def test_detection_delay_miss_unresolved() -> None:
    meta = _meta([("course", 60, 66), ("speed", 120, 121), ("course", 190, 195)])
    p = np.zeros(200)
    p[63:66] = 0.9  # first span: alarm at 63, delay (63 − 59) × 10 s
    det = {"p_change": p.tolist(), "knot_sets": []}
    sc = score_scenario(meta, det, "d")
    out = [(s.outcome, s.delay_s) for s in sc.record.spans or []]
    assert out == [("detected", 40.0), ("missed", None), ("unresolved", None)]
    s = summary([sc])
    assert s["miss_rate"] == 0.5 and s["unresolved"] == 1 and s["delay_median_s"] == 40.0


def test_held_leg_false_alarms_and_episodes() -> None:
    meta = _meta([("course", 100, 110)])
    p = np.zeros(200)
    p[50] = p[52] = 1.0  # one episode (20 s apart), on a held leg
    p[80] = 1.0  # another
    p[150] = 1.0  # held again (≥ 300 s after the end at 110 → rows ≥ 140)
    sc = score_scenario(meta, {"p_change": p.tolist()}, "d")
    assert episodes(p >= 0.5, 10.0) == [(50, 52), (80, 80), (100, 100)][:2] + [(150, 150)]
    assert sc.record.held_leg_alarms == 3
    # G5 rows: 20 + 30·m = 50, 80, 110, 140 → held: 50, 80, 140 (110 is the span's end)
    assert sc.record.held_leg_g5_rows == 3 and sc.record.held_leg_g5_flagged == 2
    assert sc.record.held_leg_seconds == 10.0 * (100 + (200 - 140))


def test_kind_and_segmentation() -> None:
    meta = _meta([("course", 60, 66), ("speed", 120, 121)])
    p = np.zeros(200)
    p[62] = p[125] = 1.0
    knots = [
        {"row": 58, "weight": 0.9, "p_kind": 0.8},  # near 60: course, correct
        {"row": 67, "weight": 0.7, "p_kind": 0.6},
        {"row": 124, "weight": 0.8, "p_kind": 0.9},  # near 120: course, wrong (speed)
        {"row": 170, "weight": 0.6, "p_kind": 0.1},  # spurious
    ]
    det = {"p_change": p.tolist(), "knot_sets": [{"query_row": 199, "knots": knots}]}
    sc = score_scenario(meta, det, "d")
    assert [s.kind_correct for s in sc.record.spans or []] == [True, False]
    assert truth_boundaries(meta["manoeuvres"]) == [60, 66, 120]  # 121 merged with 120
    assert sc.boundaries_matched == 3 and sc.knots_exported == 4
    s = summary([sc])
    assert math.isclose(s["segmentation_f1"], 2 * 0.75 * 1.0 / 1.75)
    assert s["kind_accuracy"] == 0.5


def test_one_to_one_matching_and_ece() -> None:
    assert match_one_to_one([10, 11], [10], 6) == 1
    assert match_one_to_one([10, 30], [12, 28], 6) == 2
    assert math.isclose(ece([(0.9, 1.0), (0.9, 1.0), (0.1, 0.0)]), 0.1)
    assert math.isnan(ece([]))
