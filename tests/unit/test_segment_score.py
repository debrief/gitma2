"""Spec 005 T017–T018: scoring helpers (gap recovered, prefix metrics, clustered bootstrap)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from tma2.detect.confirm import Accepted
from tma2.eval.bootstrap import bootstrap_clustered_statistic
from tma2.segment import default_parameters
from tma2.segment.score import gap_recovered_cols, glr_confirm_intervals, prefix_metrics


def _meta(spans: list[tuple[int, int]], zig: int = 60, n: int = 400) -> dict[str, Any]:
    return {
        "samples": n,
        "turn_start_index": zig - 10,
        "zig_index": zig,
        "manoeuvres": [{"start_index": a, "end_index": b, "kind": "course"} for a, b in spans],
    }


def test_gap_recovered_cols() -> None:
    one = np.array([[10.0, 1, 1]] * 5)
    ora = np.array([[2.0, 1, 1]] * 5)
    seg = np.array([[6.0, 1, 1]] * 5)
    cols = {"one_leg": one, "oracle": ora, "C": seg}
    assert gap_recovered_cols(cols, "C", 0) == pytest.approx(0.5)
    assert gap_recovered_cols({**cols, "C": ora}, "C", 0) == pytest.approx(1.0)


def test_prefix_metrics() -> None:
    p = default_parameters()
    m = _meta([(150, 165)])
    perfect = prefix_metrics([(150, 165)], m, 300, p)
    assert perfect.contamination == 0.0 and perfect.coverage == 1.0
    assert perfect.hits60 == [True] and perfect.leg_count_ok and perfect.false_split is None
    missed = prefix_metrics([], m, 300, p)
    assert missed.contamination > 0 and missed.hits60 == [False] and missed.leg_count_ok is False
    nochange = prefix_metrics([(200, 210)], _meta([]), 300, p)
    assert nochange.false_split is True
    # a change after k is not counted
    early = prefix_metrics([], m, 140, p)
    assert early.changes == 0 and early.false_split is False


def test_glr_confirm_intervals() -> None:
    acc = [
        Accepted(100, 105, 95, 30.0),
        Accepted(200, 210, 190, 25.0, 205),
        Accepted(300, 300, 290, 20.0),
    ]
    assert glr_confirm_intervals(acc, 250, 6) == [(95, 100), (190, 205)]


def test_bootstrap_clustered_statistic_deterministic() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=60)
    cl = np.repeat(np.arange(20), 3)
    a = bootstrap_clustered_statistic({"x": x}, cl, lambda c: float(np.median(c["x"])), 0.95, 500)
    b = bootstrap_clustered_statistic({"x": x}, cl, lambda c: float(np.median(c["x"])), 0.95, 500)
    assert (a.lo, a.hi) == (b.lo, b.hi) and a.lo <= a.value <= a.hi and a.clusters == 20
