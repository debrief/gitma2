"""One convergence definition and gross rows by cause (spec 004 FR-007, FR-008)."""

from __future__ import annotations

import math

import numpy as np

from tma2.eval.errors import Truth, gross_by_cause, gross_cause, plausible_row, row_error
from tma2.eval.stats import ascending, percentile


def _truth() -> Truth:
    s = 4
    t = np.arange(s, dtype=np.float64) * 10.0
    own = np.stack([t, np.zeros(s), np.zeros(s), np.zeros(s), np.full(s, 5.0)], axis=1)
    tgt = np.stack([t, np.zeros(s), np.full(s, 10_000.0), np.zeros(s), np.full(s, 5.0)], axis=1)
    meta = {"index": 0, "samples": s, "parameters": {"dt_s": 10.0}, "zig_time_s": 0.0}
    meta["zig_index"] = 0
    return Truth.from_block(meta, own, tgt)


def _row(rng: float, speed: float = 5.0, converged: bool = True) -> dict[str, float | bool]:
    return {
        "timestamp_s": 10.0,
        "range_m": rng,
        "course_rad": 0.0,
        "speed_mps": speed,
        "x_m": 0.0,
        "y_m": rng,
        "converged": converged,
    }


def test_plausibility_definition() -> None:
    assert plausible_row(_row(10_000.0))
    assert not plausible_row(_row(0.0))  # classical's empty row
    assert not plausible_row(_row(200_000.0))
    assert not plausible_row(_row(10_000.0, speed=30.0))
    assert not plausible_row(_row(math.nan))
    assert plausible_row(_row(10_000.0, converged=False))  # LM flag not consulted


def test_lm_flag_reported_not_gross() -> None:
    truth = _truth()
    lm = _row(10_100.0, converged=False)
    assert row_error(truth, lm, "flag").gross
    assert not row_error(truth, lm, "plausible").gross
    assert gross_cause(truth, lm) is None
    counts = gross_by_cause(
        [(truth, lm), (truth, None), (truth, _row(0.0, converged=False)), (truth, _row(16_000.0))]
    )
    assert counts == {
        "missing": 1,
        "implausible": 1,
        "range_error_over_50pct": 1,
        "lm_flag": 1,
        "flag_gross": 4,
        "rows": 4,
    }


def test_median_convention_is_nearest_rank() -> None:
    x = np.array([4.0, 1.0, 3.0, 2.0])
    assert percentile(ascending(x), 0.5) == 2.0  # np.median would give 2.5
