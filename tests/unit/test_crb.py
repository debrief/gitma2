"""The Cramér–Rao bound: Monte-Carlo least-squares scatter on a fixed noisy geometry matches it,
and singular cases are flagged (spec 002 FR-005)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tma2.references import lsq
from tma2.references.crb import _model_jacobian, _pos_vel, crb_at_row, crb_rows, manoeuvre_model


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
    assert b.singular


TURN = {
    "kind": "course",
    "start_time_s": 1200.0,
    "change": math.radians(60.0),
    "rate": math.radians(2.0),
}


def _turning_target() -> Any:
    """The zig geometry with a target that turns 60° at 2°/s from t = 1200 s, built with the
    bound's own kinematics (checked against the generator's truth in the conformance tests)."""
    t, ox, oy, _tx, _ty, _v = _geometry()
    c0 = math.radians(245.0)
    theta, mans = manoeuvre_model([TURN], 8000.0, 6000.0, 4 * math.sin(c0), 4 * math.cos(c0))
    pv = np.array([_pos_vel(theta, float(ti), mans) for ti in t])
    return t, ox, oy, pv[:, 0], pv[:, 1], pv[:, 2], pv[:, 3], theta, mans


def _arrays(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    vx: np.ndarray,
    vy: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    own = np.stack([t, ox, oy, 0 * t, 0 * t], 1)
    tgt = np.stack([t, tx, ty, np.arctan2(vx, vy), np.hypot(vx, vy)], 1)
    obs = np.stack([t, np.arctan2(tx - ox, ty - oy), np.ones_like(t)], 1)
    return own, tgt, obs


def test_known_manoeuvres_equals_full_window_without_manoeuvres() -> None:
    t, ox, oy, tx, ty, v = _geometry()
    own, tgt, obs = _arrays(t, ox, oy, tx, ty, np.full_like(t, v[0]), np.full_like(t, v[1]))
    rows = [100, 150, 179]
    a = crb_rows(own, tgt, obs, 0.0175, 90, None, rows, "full_window")
    b = crb_rows(own, tgt, obs, 0.0175, 90, None, rows, "known_manoeuvres", [])
    for x, y in zip(a, b, strict=True):
        assert not x.singular and not y.singular
        assert math.isclose(x.sd_range_rel, y.sd_range_rel, rel_tol=1e-6)
        assert math.isclose(x.sd_speed_kt, y.sd_speed_kt, rel_tol=1e-6)


def test_known_manoeuvres_bound_matches_model_fit_scatter() -> None:
    """Monte Carlo: Gauss–Newton on the known-manoeuvre model itself (start time and kind known,
    change unknown) scatters as the bound says, after the turn and on a straight ownship leg."""
    t, ox, oy, tx, ty, vx, vy, theta, mans = _turning_target()
    own, tgt, obs = _arrays(t, ox, oy, tx, ty, vx, vy)
    sigma = math.radians(1.0)
    k = 170
    (bound,) = crb_rows(own, tgt, obs, sigma, 90, None, [k], "known_manoeuvres", [TURN])
    assert not bound.singular
    truth_b = np.arctan2(tx - ox, ty - oy)
    rng = np.random.default_rng(11)
    ranges, speeds = [], []
    for _ in range(120):
        z = truth_b[: k + 1] + rng.normal(0, sigma, k + 1)
        th = theta.copy()
        for _it in range(5):
            jac = _model_jacobian(th, t[: k + 1], mans)
            pv = np.array([_pos_vel(th, float(ti), mans) for ti in t[: k + 1]])
            dx, dy = pv[:, 0] - ox[: k + 1], pv[:, 1] - oy[: k + 1]
            rho2 = dx * dx + dy * dy
            r = np.arctan2(np.sin(z - np.arctan2(dx, dy)), np.cos(z - np.arctan2(dx, dy)))
            g = (dy / rho2)[:, None] * jac[:, 0] - (dx / rho2)[:, None] * jac[:, 1]
            th = th + np.linalg.lstsq(g, r, rcond=None)[0]
        x, y, ux, uy = _pos_vel(th, float(t[k]), mans)
        ranges.append(math.hypot(x - ox[k], y - oy[k]))
        speeds.append(math.hypot(ux, uy))
    r_true = math.hypot(tx[k] - ox[k], ty[k] - oy[k])
    sd_r = float(np.std(ranges)) / r_true
    sd_s = float(np.std(speeds)) / (1852 / 3600)
    assert 0.8 <= sd_r / bound.sd_range_rel <= 1.25, (sd_r, bound.sd_range_rel)
    assert 0.8 <= sd_s / bound.sd_speed_kt <= 1.25, (sd_s, bound.sd_speed_kt)


def test_known_manoeuvres_tighter_than_per_leg() -> None:
    """Knowing when and how the target manoeuvred carries the earlier legs across the turn, so
    the bound is at least as tight as the per-leg diagnostic, and defined where that is not."""
    t, ox, oy, tx, ty, vx, vy, _theta, _mans = _turning_target()
    own, tgt, obs = _arrays(t, ox, oy, tx, ty, vx, vy)
    span = [{"start_index": 121, "end_index": 124, "kind": "course"}]
    rows = [122, 140, 170]
    km = crb_rows(own, tgt, obs, 0.0175, 90, span, rows, "known_manoeuvres", [TURN])
    pl = crb_rows(own, tgt, obs, 0.0175, 90, span, rows, "per_leg")
    for a, b in zip(km, pl, strict=True):
        assert not a.singular
        assert b.singular or a.sd_range_rel <= b.sd_range_rel * (1 + 1e-9)
    assert pl[0].singular  # inside the turn the per-leg bound has nothing
