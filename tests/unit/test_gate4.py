"""Gate 4's criteria on synthetic statements (spec 009 T011)."""

from __future__ import annotations

import math

import numpy as np

from tma2.calib.gate4 import PASS, criteria, summed_score
from tma2.eval.calibration import WIDTH

BANDS = {"coverage95": [0.92, 0.98], "reliability_overall": 0.03, "reliability_bin": 0.05,
         "bins": 5, "min_mean_prob": 0.5}  # fmt: skip
SCALE = {"course": 1.0, "range": 1.0, "speed": 1.0}


def _cal(n: int, q_scale: float, seed: int) -> np.ndarray:
    """Rows with standard-normal range and speed errors and a course that is inside a 0.2 rad arc
    with probability P drawn per row; q = q_scale · 1.96."""
    rng = np.random.default_rng(seed)
    c = np.zeros((n, WIDTH))
    c[:, 0] = np.abs(rng.standard_normal(n))
    c[:, 2] = np.abs(rng.standard_normal(n))
    p = rng.uniform(0.4, 0.95, n)
    inside = rng.random(n) < p
    c[:, 1] = np.where(inside, rng.uniform(0, 0.2, n), rng.uniform(0.2001, math.pi, n))
    c[:, 9], c[:, 10] = 0.2, p
    c[:, 11] = c[:, 12] = q_scale * 1.959963984540054
    c[:, 13] = np.where(inside, 0.5, -3.0)
    c[:, 7] = c[:, 8] = 1.0
    return c


def test_reliable_statement_passes_a_to_c_and_e() -> None:
    cal = _cal(6000, 1.0, 1)
    cluster = np.arange(6000) // 6
    err = np.zeros((6000, 3))
    out = criteria(cal, cal, err, err, cluster, BANDS, PASS, 0.95, 200)
    assert out["g4a"] == PASS and out["g4b"] == PASS and out["g4c"] == PASS and out["g4e"] == PASS
    assert out["g4d"] != PASS  # equal to the temperature: no learning shown


def test_overconfident_intervals_and_points_changed_fail() -> None:
    cal = _cal(6000, 0.6, 2)
    cluster = np.arange(6000) // 6
    err = np.zeros((6000, 3))
    out = criteria(cal, cal, err, err + 1e-9, cluster, BANDS, PASS, 0.95, 200)
    assert out["g4a"] == "fail" and out["g4e"] == "fail"


def test_better_head_passes_g4d_unless_shuffled_rule_failed() -> None:
    t = _cal(4000, 2.0, 3)  # wide intervals: worse score
    h = t.copy()
    h[:, 11] = h[:, 12] = 1.959963984540054
    assert summed_score(h, SCALE).mean() < summed_score(t, SCALE).mean()
    cluster = np.arange(4000) // 4
    err = np.zeros((4000, 3))
    assert criteria(h, t, err, err, cluster, BANDS, PASS, 0.95, 200)["g4d"] == PASS
    assert criteria(h, t, err, err, cluster, BANDS, "fail", 0.95, 200)["g4d"] == "fail"
