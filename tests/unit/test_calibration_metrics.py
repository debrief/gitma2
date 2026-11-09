"""Calibration measures on synthetic Gaussians (spec 008 T006, research R4)."""

from __future__ import annotations

import math

import numpy as np

from tma2.eval.calibration import (
    CHI2_4_MEDIAN,
    WIDTH,
    Z95,
    covered,
    interval_score,
    measures,
    reliability_bins,
    row_cal,
    widen,
)
from tma2.physics.uncertainty import row_fields


def _rows(n: int, inflate: float, seed: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """``n`` rows whose estimate is the truth plus a draw from P; the row states inflate·P."""
    rng = np.random.default_rng(seed)
    own = (0.0, 0.0)
    out = []
    for _ in range(n):
        truth = np.array([rng.uniform(8e3, 2e4), rng.uniform(-1e4, 1e4), 3.0, -2.0])
        p = np.diag([40.0**2, 40.0**2, 0.03**2, 0.03**2])
        est = truth + rng.multivariate_normal(np.zeros(4), p)
        row = {
            "converged": True,
            "x_m": est[0],
            "y_m": est[1],
            "range_m": math.hypot(est[0], est[1]),
            "course_rad": math.atan2(est[2], est[3]),
            "speed_mps": math.hypot(est[2], est[3]),
            **row_fields(est, inflate * p, own),
        }
        out.append(row_cal(row, truth, own))
    cal = np.array(out)
    return cal, np.arange(n)


def test_calibrated_rows_cover_at_nominal_rates() -> None:
    cal, _ = _rows(4000, 1.0)
    c95 = covered(cal, Z95).mean(axis=0)
    c68 = covered(cal, 1.0).mean(axis=0)
    se95 = math.sqrt(0.95 * 0.05 / 4000)
    assert np.all(np.abs(c95 - 0.95) < 4 * se95), c95
    assert np.all(np.abs(c68 - 0.6827) < 4 * math.sqrt(0.68 * 0.32 / 4000)), c68
    assert abs(np.median(cal[:, 6]) / CHI2_4_MEDIAN - 1) < 0.08


def test_overconfident_rows_undercover_and_score_worse() -> None:
    good, _ = _rows(3000, 1.0)
    tight, _ = _rows(3000, 0.25)  # stated sd half the true: covers far less, NEES ×4
    assert covered(tight, Z95).mean() < 0.75
    assert np.median(tight[:, 6]) / CHI2_4_MEDIAN > 3.0
    assert interval_score(tight).mean() > interval_score(good).mean()


def test_interval_score_by_hand() -> None:
    cal = np.zeros((1, 9))
    cal[0, 0:3] = [0.3, 0.0, 0.0]  # log-range miss beyond 1.96 sd = 0.1 → 0.104
    cal[0, 3:6] = [0.1, 0.01, 0.1]
    cal[0, 7:9] = 1.0
    s = interval_score(cal)[0, 0]
    want = 2 * Z95 * 0.1 + (2 / 0.05) * (0.3 - Z95 * 0.1)
    assert abs(s - want) < 1e-12


def test_missing_row_is_not_covered() -> None:
    cal, _ = _rows(50, 1.0)
    cal[0] = row_cal(None, np.zeros(4), (0.0, 0.0))
    assert covered(cal, Z95)[0].sum() == 0
    m = {x.name: x for x in measures()}
    assert abs(m["no_estimate_share"].stat({"c": cal}) - 1 / 50) < 1e-12
    assert math.isfinite(m["interval_score95_log_range"].stat({"c": cal}))


def test_statement_from_sds_is_reliable_on_calibrated_rows() -> None:
    """Spec 009 T005: a Gaussian-derived statement on calibrated rows: P matches the hit rate,
    range and speed intervals cover 95%, and the course is more informative than uniform."""
    cal, _ = _rows(4000, 1.0)
    assert cal.shape[1] == WIDTH
    m = {x.name: x.stat({"c": cal}) for x in measures()}
    assert abs(m["statement_reliability"]) < 0.02
    assert abs(m["statement_coverage95_log_range"] - 0.95) < 0.02
    assert abs(m["statement_coverage95_speed"] - 0.95) < 0.02
    assert m["statement_course_log_gain"] > 0.5
    assert all(abs(b["hit"] - b["p"]) < 0.05 for b in reliability_bins(cal))


def test_widen_matches_row_cal_and_missing_rows_state_nothing() -> None:
    cal, _ = _rows(30, 1.0)
    cal[0] = row_cal(None, np.zeros(4), (0.0, 0.0))
    assert np.allclose(widen(cal[:, :9]), cal, equal_nan=True)
    assert cal[0, 9] == cal[0, 10] == 0.0
    assert abs(cal[0, 13] + math.log(2 * math.pi)) < 1e-12


def test_explicit_statement_fields_are_read() -> None:
    cal0, _ = _rows(1, 1.0)
    rng_row = {
        "converged": True, "x_m": 1e4, "y_m": 0.0, "range_m": 1e4, "course_rad": 0.5,
        "speed_mps": 4.0,
        **row_fields(np.array([1e4, 0.0, 4 * math.sin(0.5), 4 * math.cos(0.5)]),
                     np.diag([40.0**2, 40.0**2, 0.03**2, 0.03**2]), (0.0, 0.0)),
        "course_arc_rad": 0.2, "course_arc_prob": 0.7, "course_conc": 50.0, "course_mix_p": 0.8,
        "range_ratio_q95": 0.05, "speed_q95_mps": 0.4,
    }  # fmt: skip
    c = row_cal(rng_row, np.array([1e4, 0.0, 4 * math.sin(0.6), 4 * math.cos(0.6)]), (0.0, 0.0))
    assert c[14] == 1.0 and c[9] == 0.2 and c[10] == 0.7 and c[11] == 0.05 and c[12] == 0.4
    assert math.isfinite(c[13])
    assert cal0.shape == (1, WIDTH)
