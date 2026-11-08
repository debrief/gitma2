"""The stated uncertainty of an estimate (spec 008, research R2).

A row's covariance is that of the state (x, y, vx, vy) at the row: east and north positions in
metres and velocities in m/s, as ``PhysicsOutputs.cov`` and the trackers state it. It is stored
as its 10-entry upper triangle, row-major (``cov_xyvv``). The standard deviations of log range,
course and speed come by first-order propagation:

- log range = ½ log(Δx² + Δy²), with Δ relative to ownship at the row;
- course = atan2(vx, vy), clockwise from north;
- speed = hypot(vx, vy).
"""

from __future__ import annotations

import math

import numpy as np

IU = np.triu_indices(4)  # row-major upper triangle: (0,0) (0,1) (0,2) (0,3) (1,1) … (3,3)
MIN_RANGE_M = 1.0  # as PhysicsOutputs.cov_ok: a target on ownship has degenerate information


def pack_cov(p: np.ndarray) -> list[float]:
    """The 10-entry upper triangle, row-major, of a 4 × 4 covariance (symmetrised)."""
    q = 0.5 * (np.asarray(p, dtype=np.float64) + np.asarray(p, dtype=np.float64).T)
    return [float(v) for v in q[IU]]


def unpack_cov(v: list[float] | np.ndarray) -> np.ndarray:
    """The 4 × 4 covariance from its packed upper triangle."""
    a = np.asarray(v, dtype=np.float64)
    if a.shape != (10,):
        raise ValueError(f"a packed covariance has 10 entries, not {a.shape}")
    p = np.zeros((4, 4))
    p[IU] = a
    return p + np.triu(p, 1).T


def gradients(state: np.ndarray, own_xy: tuple[float, float]) -> np.ndarray:
    """[3, 4] gradients of (log range, course, speed) with respect to (x, y, vx, vy)."""
    x, y, vx, vy = (float(v) for v in state)
    dx, dy = x - own_xy[0], y - own_xy[1]
    r2 = dx * dx + dy * dy
    s2 = vx * vx + vy * vy
    s = math.sqrt(s2)
    g = np.zeros((3, 4))
    if r2 > 0:
        g[0, 0], g[0, 1] = dx / r2, dy / r2
    if s2 > 0:
        g[1, 2], g[1, 3] = vy / s2, -vx / s2
        g[2, 2], g[2, 3] = vx / s, vy / s
    return g


def derived_sds(
    state: np.ndarray, p: np.ndarray, own_xy: tuple[float, float]
) -> tuple[float, float, float]:
    """First-order standard deviations of log range (natural log), course (rad) and speed (m/s);
    NaN where the propagated variance is not finite and positive."""
    g = gradients(state, own_xy)
    var = np.einsum("ij,jk,ik->i", g, p, g)
    out = [math.sqrt(v) if np.isfinite(v) and v > 0 else math.nan for v in var]
    return out[0], out[1], out[2]


def cov_usable(p: np.ndarray, state: np.ndarray, own_xy: tuple[float, float]) -> bool:
    """Finite, symmetric positive definite, and the target not on ownship."""
    p = np.asarray(p, dtype=np.float64)
    if p.shape != (4, 4) or not np.isfinite(p).all() or not np.isfinite(state).all():
        return False
    if math.hypot(float(state[0]) - own_xy[0], float(state[1]) - own_xy[1]) <= MIN_RANGE_M:
        return False
    try:
        np.linalg.cholesky(0.5 * (p + p.T))
    except np.linalg.LinAlgError:
        return False
    return True


def row_fields(state: np.ndarray, p: np.ndarray, own_xy: tuple[float, float]) -> dict[str, object]:
    """The prediction row's uncertainty fields (``PredictionRow``, schema 0.26.0)."""
    ok = cov_usable(p, state, own_xy)
    lr, cr, sp = derived_sds(state, p, own_xy) if ok else (math.nan, math.nan, math.nan)
    out: dict[str, object] = {"cov_ok": ok}
    if np.isfinite(np.asarray(p)).all():
        out["cov_xyvv"] = pack_cov(p)
    if ok:
        out.update({"log_range_sd": lr, "course_sd_rad": cr, "speed_sd_mps": sp})
    return out


# Spec 008 research R5 (as amended): the calibration rescales the covariance in local
# coordinates. ``LOCAL`` orders them; the head's or temperature's scales follow it.
LOCAL = ("log_range", "bearing", "speed", "course")


def local_jacobian(state: np.ndarray, own_xy: tuple[float, float]) -> np.ndarray:
    """[4, 4] T: d(log range, bearing, speed, course) / d(x, y, vx, vy) at the state. Block
    diagonal (position, velocity); invertible while the target is off ownship and moving."""
    x, y, vx, vy = (float(v) for v in state)
    dx, dy = x - own_xy[0], y - own_xy[1]
    r2, s2 = dx * dx + dy * dy, vx * vx + vy * vy
    s = math.sqrt(s2)
    t = np.zeros((4, 4))
    t[0, 0], t[0, 1] = dx / r2, dy / r2
    t[1, 0], t[1, 1] = dy / r2, -dx / r2
    t[2, 2], t[2, 3] = vx / s, vy / s
    t[3, 2], t[3, 3] = vy / s2, -vx / s2
    return t


def local_rescale(
    state: np.ndarray, p: np.ndarray, own_xy: tuple[float, float], s: np.ndarray
) -> np.ndarray:
    """The covariance with its local-coordinate standard deviations scaled by e^s (``LOCAL``
    order; correlations kept): A P Aᵀ with A = T⁻¹ diag(e^s) T. A scalar s (all four equal)
    gives e^(2s) P exactly."""
    t = local_jacobian(state, own_xy)
    a = np.linalg.solve(t, np.diag(np.exp(np.asarray(s, dtype=np.float64))) @ t)
    q: np.ndarray = a @ np.asarray(p, dtype=np.float64) @ a.T
    out: np.ndarray = 0.5 * (q + q.T)
    return out
