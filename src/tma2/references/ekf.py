"""Extended Kalman filter, ported from gitma ``packages/classical/src/ekf.ts``.

Constant-velocity state (x, y, vx, vy), white-noise-acceleration process noise σ_a, bearings-only
update with the wrapped innovation, Joseph-form covariance update. Initialised at ``zig_index``
from the batch least-squares solution and its covariance σ²(JᵀJ)⁻¹, then run per timestep;
re-initialised after an implausible state. Numba kernels over per-scenario arrays.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from numba import njit

from tma2.data.canonical import js_number
from tma2.sim.geometry import bearing_of, f32, f32_angle

from .classical import PLAUSIBLE_MAX_RANGE_M, PLAUSIBLE_MAX_SPEED_MPS, BearingData
from .lsq import MAX_ITERATIONS, angle_diff, normal_equations, solve4, solve_batch

EKF = "ekf"
EKF_MIN_SIGMA_RAD = 1e-4
EKF_REINIT_EVERY = 6


def scale_suffix(p0_scale: float, r_scale: float) -> str:
    return (f"-p{js_number(p0_scale)}" if p0_scale != 1 else "") + (
        f"-r{js_number(r_scale)}" if r_scale != 1 else ""
    )


def ekf_name(sigma_a: float, p0_scale: float = 1.0, r_scale: float = 1.0) -> str:
    return f"{EKF}-sa{js_number(sigma_a)}{scale_suffix(p0_scale, r_scale)}"


@njit(cache=True)
def _symmetrise(p: np.ndarray) -> np.ndarray:
    n = p.shape[0]
    s = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            s[i, j] = (p[i, j] + p[j, i]) / 2.0
    return s


@njit(cache=True)
def _mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Row-major product in gitma's loop order (no BLAS: the arithmetic order must match)."""
    n = a.shape[0]
    c = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += a[i, k] * b[k, j]
            c[i, j] = s
    return c


@njit(cache=True)
def _transpose(a: np.ndarray) -> np.ndarray:
    n = a.shape[0]
    t = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            t[i, j] = a[j, i]
    return t


@njit(cache=True)
def _transition4(tau: float) -> np.ndarray:
    f = np.eye(4)
    f[0, 2] = tau
    f[1, 3] = tau
    return f


@njit(cache=True)
def _inverse4(a: np.ndarray) -> tuple[bool, np.ndarray]:
    inv = np.empty((4, 4))
    for c in range(4):
        e = np.zeros(4)
        e[c] = 1.0
        ok, col = solve4(a, e)
        if not ok:
            return False, inv
        for r in range(4):
            inv[r, c] = col[r]
    return True, inv


@njit(cache=True)
def plausible_state4(ox: float, oy: float, x: np.ndarray) -> bool:
    px, py, vx, vy = x[0], x[1], x[2], x[3]
    for k in range(4):
        if not math.isfinite(x[k]):
            return False
    rng = math.hypot(px - ox, py - oy)
    return (
        math.hypot(vx, vy) <= PLAUSIBLE_MAX_SPEED_MPS and rng > 0 and rng <= PLAUSIBLE_MAX_RANGE_M
    )


@njit(cache=True)
def ekf_initialise(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    i: int,
    sigma: float,
    p0_scale: float,
) -> tuple[bool, float, np.ndarray, np.ndarray]:
    """State at sample i from the batch solution on [0, i], propagated to t_i, with covariance
    σ²(JᵀJ)⁻¹ propagated likewise. (ok, t, x, P)."""
    x = np.zeros(4)
    p = np.zeros((4, 4))
    found, theta, _conv, _it, _c = solve_batch(t, ox, oy, z, valid, i + 1, MAX_ITERATIONS)
    if not found:
        return False, 0.0, x, p
    ti = t[i]
    f = _transition4(ti)
    for r in range(4):
        s = 0.0
        for k in range(4):
            s += f[r, k] * theta[k]
        x[r] = s
    if not plausible_state4(ox[i], oy[i], x):
        return False, ti, x, p
    jtj, _jtr = normal_equations(t, ox, oy, z, valid, theta, i + 1)
    ok, info = _inverse4(jtj)
    if not ok:
        return False, ti, x, p
    r2 = max(sigma, EKF_MIN_SIGMA_RAD) ** 2 * p0_scale
    p0 = _mul(_mul(f, info * r2), _transpose(f))
    return True, ti, x, _symmetrise(p0)


@njit(cache=True)
def ekf_predict_step(
    t_prev: float, x: np.ndarray, p: np.ndarray, t: float, sigma_a: float
) -> tuple[np.ndarray, np.ndarray]:
    tau = t - t_prev
    f = _transition4(tau)
    xn = np.array([x[0] + x[2] * tau, x[1] + x[3] * tau, x[2], x[3]])
    q = np.zeros((4, 4))
    q2 = sigma_a * sigma_a
    a = (q2 * tau**4) / 4.0
    b = (q2 * tau**3) / 2.0
    c = q2 * tau * tau
    q[0, 0] = a
    q[1, 1] = a
    q[0, 2] = b
    q[2, 0] = b
    q[1, 3] = b
    q[3, 1] = b
    q[2, 2] = c
    q[3, 3] = c
    pn = _mul(_mul(f, p), _transpose(f)) + q
    return xn, _symmetrise(pn)


@njit(cache=True)
def ekf_update(
    x: np.ndarray, p: np.ndarray, z: float, ox: float, oy: float, r2: float
) -> tuple[np.ndarray, np.ndarray]:
    dx = x[0] - ox
    dy = x[1] - oy
    rho2 = dx * dx + dy * dy
    h = np.array([dy / rho2, -dx / rho2, 0.0, 0.0])
    ph = np.zeros(4)
    for i in range(4):
        s = 0.0
        for k in range(4):
            s += p[i, k] * h[k]
        ph[i] = s
    s = r2
    for k in range(4):
        s += h[k] * ph[k]
    kg = ph / s
    nu = angle_diff(z, bearing_of(dx, dy))
    xn = x + kg * nu
    ikh = np.empty((4, 4))
    for i in range(4):
        for j in range(4):
            ikh[i, j] = (1.0 if i == j else 0.0) - kg[i] * h[j]
    pn = _mul(_mul(ikh, p), _transpose(ikh))
    for i in range(4):
        for j in range(4):
            pn[i, j] = pn[i, j] + r2 * kg[i] * kg[j]
    return xn, _symmetrise(pn)


def _state_row(d: BearingData, x: np.ndarray, i: int, converged: bool) -> dict[str, Any]:
    px, py, vx, vy = (float(v) for v in x)
    return {
        "timestamp_s": f32(float(d.t[i])),
        "range_m": f32(math.hypot(px - d.ox[i], py - d.oy[i])),
        "course_rad": f32_angle(bearing_of(vx, vy)),
        "speed_mps": f32(math.hypot(vx, vy)),
        "x_m": f32(px),
        "y_m": f32(py),
        "converged": converged,
        "iterations": 0,
    }


def _empty_row(d: BearingData, i: int) -> dict[str, Any]:
    return {
        "timestamp_s": f32(float(d.t[i])),
        "range_m": 0.0,
        "course_rad": 0.0,
        "speed_mps": 0.0,
        "x_m": 0.0,
        "y_m": 0.0,
        "converged": False,
        "iterations": 0,
    }


def ekf_predict(
    d: BearingData, sigma_a: float, p0_scale: float = 1.0, r_scale: float = 1.0
) -> dict[str, Any]:
    """gitma ``ekfPredict``: one row per sample from zig_index + 1."""
    if not sigma_a >= 0:
        raise ValueError(f"EKF process noise must be ≥ 0, got {sigma_a}")
    if not (p0_scale > 0 and r_scale > 0):
        raise ValueError("EKF scales must be > 0")
    n = d.n
    sigma = d.sigma
    r2 = max(sigma, EKF_MIN_SIGMA_RAD) ** 2 * r_scale
    rows: list[dict[str, Any]] = []
    first = d.zig_index + 1
    have = False
    t_prev = 0.0
    x = np.zeros(4)
    p = np.zeros((4, 4))
    if first - 1 < n:
        have, t_prev, x, p = ekf_initialise(
            d.t, d.ox, d.oy, d.z, d.valid, first - 1, sigma, p0_scale
        )
    last_try = first - 1
    for i in range(first, n):
        if have:
            x, p = ekf_predict_step(t_prev, x, p, float(d.t[i]), sigma_a)
            t_prev = float(d.t[i])
            if d.valid[i] == 1:
                x, p = ekf_update(x, p, float(d.z[i]), float(d.ox[i]), float(d.oy[i]), r2)
            if plausible_state4(float(d.ox[i]), float(d.oy[i]), x):
                rows.append(_state_row(d, x, i, True))
                continue
            rows.append(_state_row(d, x, i, False))
            have = False
            last_try = i - EKF_REINIT_EVERY
        else:
            rows.append(_empty_row(d, i))
        if i - last_try >= EKF_REINIT_EVERY:
            have, t_prev, x, p = ekf_initialise(d.t, d.ox, d.oy, d.z, d.valid, i, sigma, p0_scale)
            last_try = i
    return {
        "record": "prediction",
        "scenario_index": d.index,
        "estimator": ekf_name(sigma_a, p0_scale, r_scale),
        "mode": "per_timestep",
        "rows": rows,
    }
