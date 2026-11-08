"""The stated uncertainty of an estimate (spec 008 T004, research R2)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tma2.physics.uncertainty import (
    cov_usable,
    derived_sds,
    pack_cov,
    row_fields,
    unpack_cov,
)


def _spd(rng: np.random.Generator, scale: np.ndarray) -> np.ndarray:
    a = rng.normal(size=(4, 4))
    q, _ = np.linalg.qr(a)
    d = np.diag(rng.uniform(0.5, 2.0, 4))
    return np.diag(scale) @ q @ d @ q.T @ np.diag(scale)


def test_pack_round_trip() -> None:
    rng = np.random.default_rng(1)
    p = _spd(rng, np.array([100.0, 100.0, 0.5, 0.5]))
    v = pack_cov(p)
    assert len(v) == 10
    np.testing.assert_allclose(unpack_cov(v), 0.5 * (p + p.T), rtol=0, atol=1e-12)
    with pytest.raises(ValueError):
        unpack_cov([1.0] * 9)


def test_sds_match_sampling() -> None:
    """Small covariance: the propagated standard deviations match the spread of sampled states."""
    rng = np.random.default_rng(2)
    state = np.array([12_000.0, -7_000.0, 3.0, -4.5])
    own = (500.0, 300.0)
    p = _spd(rng, np.array([60.0, 60.0, 0.05, 0.05]))
    lr, cr, sp = derived_sds(state, p, own)
    draws = rng.multivariate_normal(state, p, size=200_000)
    dx, dy = draws[:, 0] - own[0], draws[:, 1] - own[1]
    log_r = 0.5 * np.log(dx * dx + dy * dy)
    course = np.arctan2(draws[:, 2], draws[:, 3])
    speed = np.hypot(draws[:, 2], draws[:, 3])
    for want, got in ((log_r.std(), lr), (course.std(), cr), (speed.std(), sp)):
        assert abs(got - want) / want < 0.02, (got, want)


def test_usable_and_row_fields() -> None:
    state = np.array([5_000.0, 5_000.0, 2.0, 1.0])
    good = np.diag([1e4, 1e4, 0.1, 0.1])
    assert cov_usable(good, state, (0.0, 0.0))
    bad = good.copy()
    bad[0, 0] = -1.0
    assert not cov_usable(bad, state, (0.0, 0.0))
    assert not cov_usable(good, state, (5_000.0, 5_000.5))  # on ownship
    assert not cov_usable(np.full((4, 4), math.nan), state, (0.0, 0.0))
    f = row_fields(state, good, (0.0, 0.0))
    assert f["cov_ok"] is True and len(f["cov_xyvv"]) == 10  # type: ignore[arg-type]
    assert {"log_range_sd", "course_sd_rad", "speed_sd_mps"} <= set(f)
    g = row_fields(state, bad, (0.0, 0.0))
    assert g["cov_ok"] is False and "log_range_sd" not in g
