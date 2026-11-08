"""Gate 3's criteria (spec 008 T027)."""

from __future__ import annotations

import numpy as np

from tma2.calib.gate import FAIL, INCONCLUSIVE, PASS, all_of, below, criteria, inside, shuffled_rule

BANDS = {"coverage95": [0.92, 0.98], "nees_median_ratio": [0.8, 1.25]}


def _cal(n: int, scale: float, seed: int) -> np.ndarray:
    """Calibrated rows (true sd 1) stated with sd = scale; NEES consistent with the scale."""
    rng = np.random.default_rng(seed)
    e = np.abs(rng.normal(size=(n, 3)))
    cal = np.zeros((n, 9))
    cal[:, 0:3] = e
    cal[:, 3:6] = scale
    cal[:, 6] = rng.chisquare(4, n) / scale**2
    cal[:, 7:9] = 1.0
    return cal


def test_verdict_helpers() -> None:
    assert inside({"value": 0.95, "lo": 0.94, "hi": 0.96}, 0.92, 0.98) == PASS
    assert inside({"value": 0.80, "lo": 0.78, "hi": 0.82}, 0.92, 0.98) == FAIL
    assert inside({"value": 0.95, "lo": 0.90, "hi": 0.97}, 0.92, 0.98) == INCONCLUSIVE
    assert below({"value": -1, "lo": -2, "hi": -0.5}, 0) == PASS
    assert all_of([PASS, INCONCLUSIVE]) == INCONCLUSIVE and all_of([PASS, FAIL]) == FAIL
    assert shuffled_rule({"value": -1, "lo": -2, "hi": -0.5}) == FAIL
    assert shuffled_rule({"value": -1, "lo": -2, "hi": 0.5}) == PASS


def test_calibrated_e_passes_and_overconfident_fails() -> None:
    n = 3000
    cluster = np.arange(n) // 4
    good = _cal(n, 1.0, 1)
    tight = _cal(n, 0.5, 1)  # the same errors stated with half the sd
    err = np.zeros((n, 3))
    out = criteria(good, tight, err, err.copy(), cluster, BANDS, PASS, 0.975, 300)
    assert out["g3a"] == PASS and out["g3b"] == PASS
    assert out["g3c"] == PASS  # the calibrated rows score better than the overconfident ones
    assert out["g3d"] == PASS and out["overall"] == PASS
    worse = criteria(tight, good, err, err + 1e-9, cluster, BANDS, PASS, 0.975, 300)
    assert worse["g3a"] == FAIL and worse["g3c"] == FAIL and worse["g3d"] == FAIL
    void = criteria(good, tight, err, err.copy(), cluster, BANDS, FAIL, 0.975, 300)
    assert void["g3c"] == FAIL
