"""The Cramér–Rao bound: Monte-Carlo least-squares scatter on a fixed noisy geometry matches it,
and singular cases are flagged (spec 002 FR-005)."""

from __future__ import annotations

import math

import numpy as np

from tma2.references import lsq
from tma2.references.crb import crb_at_row


def _geometry() -> tuple[np.ndarray, ...]:
    t = np.arange(0, 1800, 10.0)
    # ownship: north at 5 m/s for 900 s, then east at 5 m/s (a 90° zig)
    ox = np.where(t < 900, 0.0, 5.0 * (t - 900))
    oy = np.where(t < 900, 5.0 * t, 4500.0)
    # target: from (8 km, 6 km) heading west-south-west at 4 m/s
    vx, vy = -3.6, -1.7
    tx = 8000.0 + vx * t
    ty = 6000.0 + vy * t
    return t, ox, oy, tx, ty, np.array([vx, vy])


def test_bound_matches_least_squares_scatter() -> None:
    t, ox, oy, tx, ty, v = _geometry()
    sigma = math.radians(1.0)
    valid = np.ones(t.shape[0], dtype=np.uint8)
    k = t.shape[0] - 1
    bound = crb_at_row(t, ox, oy, tx, ty, float(v[0]), float(v[1]), valid, 0, k, sigma)
    assert not bound.singular
    rng = np.random.default_rng(7)
    truth_b = np.arctan2(tx - ox, ty - oy)
    ranges, speeds = [], []
    for _ in range(300):
        z = truth_b + rng.normal(0, sigma, t.shape[0])
        found, th, _c, _it, _cost = lsq.solve_batch(t, ox, oy, z, valid, k + 1, 50)
        assert found
        px, py = th[0] + th[2] * t[k], th[1] + th[3] * t[k]
        ranges.append(math.hypot(px - ox[k], py - oy[k]))
        speeds.append(math.hypot(th[2], th[3]))
    r_true = math.hypot(tx[k] - ox[k], ty[k] - oy[k])
    sd_r = float(np.std(ranges)) / r_true
    sd_s = float(np.std(speeds)) / (1852 / 3600)
    assert 0.8 <= sd_r / bound.sd_range_rel <= 1.25, (sd_r, bound.sd_range_rel)
    assert 0.8 <= sd_s / bound.sd_speed_kt <= 1.25, (sd_s, bound.sd_speed_kt)


def test_single_leg_is_singular() -> None:
    t, ox, oy, tx, ty, v = _geometry()
    valid = np.ones(t.shape[0], dtype=np.uint8)
    # straight ownship leg and a constant-velocity target: range is unobservable
    b = crb_at_row(t, ox, oy, tx, ty, float(v[0]), float(v[1]), valid, 0, 80, math.radians(1.0))
    assert b.singular or b.sd_range_rel > 1.0
