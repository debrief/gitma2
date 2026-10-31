"""Interacting-multiple-model tracker, ported from gitma ``packages/classical/src/imm.ts``.

Two extended Kalman filters on (x, y, vx, vy, ω): CV (ω carried, unused) and CT (coordinated
turn, ω random walk). Standard IMM cycle: mix, predict, wrapped-innovation update (Joseph form),
model probabilities from the innovation likelihoods, combine. Jacobians by central differences,
as gitma (an analytic Jacobian would change the numbers). Initialised at ``zig_index`` from the
batch solution (``ekf_initialise``); re-initialised after an implausible combined estimate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numba import njit

from tma2.data.canonical import js_number
from tma2.sim.geometry import bearing_of, f32, f32_angle

from .classical import PLAUSIBLE_MAX_RANGE_M, PLAUSIBLE_MAX_SPEED_MPS, BearingData
from .ekf import (
    EKF_MIN_SIGMA_RAD,
    EKF_REINIT_EVERY,
    _mul,
    _symmetrise,
    _transpose,
    ekf_initialise,
    scale_suffix,
)
from .lsq import angle_diff

IMM = "imm"
N = 5
IMM_OMEGA0_SD = 0.05
IMM_MU0 = (0.9, 0.1)


@dataclass(frozen=True)
class ImmParams:
    sigma_cv: float
    sigma_ct: float
    sigma_omega: float
    switch_per_s: float
    p0_scale: float = 1.0
    r_scale: float = 1.0


def imm_name(p: ImmParams) -> str:
    return (
        f"{IMM}-cv{js_number(p.sigma_cv)}-ct{js_number(p.sigma_ct)}-w{js_number(p.sigma_omega)}"
        f"-s{js_number(p.switch_per_s)}{scale_suffix(p.p0_scale, p.r_scale)}"
    )


@njit(cache=True)
def ct_motion(s: np.ndarray, tau: float) -> np.ndarray:
    x, y, vx, vy, w = s[0], s[1], s[2], s[3], s[4]
    th = w * tau
    if abs(th) < 1e-9:
        a = tau
        b = (w * tau * tau) / 2.0
    else:
        a = math.sin(th) / w
        b = (1.0 - math.cos(th)) / w
    c = math.cos(th)
    sn = math.sin(th)
    return np.array(
        [x + vx * a + vy * b, y - vx * b + vy * a, vx * c + vy * sn, -vx * sn + vy * c, w]
    )


@njit(cache=True)
def cv_motion(s: np.ndarray, tau: float) -> np.ndarray:
    return np.array([s[0] + s[2] * tau, s[1] + s[3] * tau, s[2], s[3], s[4]])


@njit(cache=True)
def _motion(kind: int, s: np.ndarray, tau: float) -> np.ndarray:
    return cv_motion(s, tau) if kind == 0 else ct_motion(s, tau)


@njit(cache=True)
def _jacobian(kind: int, s: np.ndarray, tau: float) -> np.ndarray:
    j = np.empty((N, N))
    for c in range(N):
        h = 1e-7 if c == 4 else 1e-4 * max(1.0, abs(s[c]))
        up = s.copy()
        dn = s.copy()
        up[c] = up[c] + h
        dn[c] = dn[c] - h
        fu = _motion(kind, up, tau)
        fd = _motion(kind, dn, tau)
        for r in range(N):
            j[r, c] = (fu[r] - fd[r]) / (2.0 * h)
    return j


@njit(cache=True)
def _process_noise(tau: float, sigma_a: float, sigma_omega: float) -> np.ndarray:
    q = np.zeros((N, N))
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
    q[4, 4] = sigma_omega * sigma_omega * tau
    return q


@njit(cache=True)
def _predict_model(
    kind: int, x: np.ndarray, p: np.ndarray, tau: float, q: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    f = _jacobian(kind, x, tau)
    pn = _mul(_mul(f, p), _transpose(f)) + q
    return _motion(kind, x, tau), _symmetrise(pn)


@njit(cache=True)
def _update_model(
    x: np.ndarray, p: np.ndarray, z: float, ox: float, oy: float, r2: float
) -> tuple[np.ndarray, np.ndarray, float, float]:
    dx = x[0] - ox
    dy = x[1] - oy
    rho2 = dx * dx + dy * dy
    h = np.array([dy / rho2, -dx / rho2, 0.0, 0.0, 0.0])
    ph = np.zeros(N)
    for i in range(N):
        s = 0.0
        for k in range(N):
            s += p[i, k] * h[k]
        ph[i] = s
    s = r2
    for k in range(N):
        s += h[k] * ph[k]
    kg = ph / s
    nu = angle_diff(z, bearing_of(dx, dy))
    xn = x + kg * nu
    ikh = np.empty((N, N))
    for i in range(N):
        for j in range(N):
            ikh[i, j] = (1.0 if i == j else 0.0) - kg[i] * h[j]
    pn = _mul(_mul(ikh, p), _transpose(ikh))
    for i in range(N):
        for j in range(N):
            pn[i, j] = pn[i, j] + r2 * kg[i] * kg[j]
    likelihood = math.exp((-0.5 * nu * nu) / s) / math.sqrt(2.0 * math.pi * s)
    return xn, _symmetrise(pn), likelihood, (nu * nu) / s


@njit(cache=True)
def _mix(
    x0: np.ndarray, p0: np.ndarray, x1: np.ndarray, p1: np.ndarray, w0: float, w1: float
) -> tuple[np.ndarray, np.ndarray]:
    x = np.zeros(N)
    for k in range(N):
        x[k] = w0 * x0[k] + w1 * x1[k]
    p = np.zeros((N, N))
    for a in range(N):
        for b in range(N):
            da0 = x0[a] - x[a]
            db0 = x0[b] - x[b]
            da1 = x1[a] - x[a]
            db1 = x1[b] - x[b]
            p[a, b] = w0 * (p0[a, b] + da0 * db0) + w1 * (p1[a, b] + da1 * db1)
    return x, _symmetrise(p)


@njit(cache=True)
def imm_step(
    t_prev: float,
    xcv: np.ndarray,
    pcv: np.ndarray,
    xct: np.ndarray,
    pct: np.ndarray,
    mu0: float,
    mu1: float,
    t: float,
    has_z: bool,
    z: float,
    ox: float,
    oy: float,
    r2: float,
    sigma_cv: float,
    sigma_ct: float,
    sigma_omega: float,
    switch_per_s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float, float]:
    """One IMM cycle; returns (xcv, pcv, xct, pct, mu0, mu1, nis) with nis = −1 when no bearing."""
    tau = t - t_prev
    sw = min(0.5, switch_per_s * tau)
    pi00, pi01, pi10, pi11 = 1.0 - sw, sw, sw, 1.0 - sw
    c0 = mu0 * pi00 + mu1 * pi10
    c1 = mu0 * pi01 + mu1 * pi11
    d0 = c0 if c0 > 0 else 1.0
    d1 = c1 if c1 > 0 else 1.0
    # mixed estimate for model j: weights w_ij = pi_ij mu_i / c_j
    m0x, m0p = _mix(xcv, pcv, xct, pct, pi00 * mu0 / d0, pi10 * mu1 / d0)
    m1x, m1p = _mix(xcv, pcv, xct, pct, pi01 * mu0 / d1, pi11 * mu1 / d1)
    cvx, cvp = _predict_model(0, m0x, m0p, tau, _process_noise(tau, sigma_cv, 0.0))
    ctx, ctp = _predict_model(1, m1x, m1p, tau, _process_noise(tau, sigma_ct, sigma_omega))
    like0 = 1.0
    like1 = 1.0
    nis = -1.0
    if has_z:
        cvx, cvp, like0, nis0 = _update_model(cvx, cvp, z, ox, oy, r2)
        ctx, ctp, like1, nis1 = _update_model(ctx, ctp, z, ox, oy, r2)
        nis = c0 * nis0 + c1 * nis1
    u0 = like0 * c0
    u1 = like1 * c1
    total = u0 + u1
    if not (total > 0) or not math.isfinite(total):
        u0 = c0
        u1 = c1
    else:
        u0 /= total
        u1 /= total
    return cvx, cvp, ctx, ctp, u0, u1, nis


@njit(cache=True)
def imm_estimate(
    xcv: np.ndarray, pcv: np.ndarray, xct: np.ndarray, pct: np.ndarray, mu0: float, mu1: float
) -> np.ndarray:
    x, _p = _mix(xcv, pcv, xct, pct, mu0, mu1)
    return x


@njit(cache=True)
def _plausible5(ox: float, oy: float, x: np.ndarray) -> bool:
    for k in range(N):
        if not math.isfinite(x[k]):
            return False
    rng = math.hypot(x[0] - ox, x[1] - oy)
    return (
        math.hypot(x[2], x[3]) <= PLAUSIBLE_MAX_SPEED_MPS
        and rng > 0
        and rng <= PLAUSIBLE_MAX_RANGE_M
    )


def _row(d: BearingData, x: np.ndarray | None, i: int, converged: bool) -> dict[str, Any]:
    if not converged or x is None:
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
    px, py, vx, vy = (float(v) for v in x[:4])
    return {
        "timestamp_s": f32(float(d.t[i])),
        "range_m": f32(math.hypot(px - d.ox[i], py - d.oy[i])),
        "course_rad": f32_angle(bearing_of(vx, vy)),
        "speed_mps": f32(math.hypot(vx, vy)),
        "x_m": f32(px),
        "y_m": f32(py),
        "converged": True,
        "iterations": 0,
    }


def imm_initialise(
    d: BearingData, i: int, sigma: float, p0_scale: float
) -> tuple[bool, float, np.ndarray, np.ndarray]:
    ok, t, x4, p4 = ekf_initialise(d.t, d.ox, d.oy, d.z, d.valid, i, sigma, p0_scale)
    x = np.zeros(N)
    p = np.zeros((N, N))
    if not ok:
        return False, t, x, p
    x[:4] = x4
    p[:4, :4] = p4
    p[4, 4] = IMM_OMEGA0_SD * IMM_OMEGA0_SD
    return True, t, x, p


def imm_predict(
    d: BearingData, params: ImmParams, nis_out: list[float] | None = None
) -> dict[str, Any]:
    """gitma ``immPredict``: one row per sample from zig_index + 1."""
    for name in ("sigma_cv", "sigma_ct", "sigma_omega", "switch_per_s", "p0_scale", "r_scale"):
        v = getattr(params, name)
        if not (v >= 0):
            raise ValueError(f"IMM {name} must be ≥ 0")
    if params.p0_scale == 0 or params.r_scale == 0:
        raise ValueError("IMM scales must be > 0")
    n = d.n
    sigma = d.sigma
    r2 = max(sigma, EKF_MIN_SIGMA_RAD) ** 2 * params.r_scale
    rows: list[dict[str, Any]] = []
    first = d.zig_index + 1
    have = False
    t_prev = 0.0
    xcv = xct = np.zeros(N)
    pcv = pct = np.zeros((N, N))
    mu0, mu1 = IMM_MU0
    if first - 1 < n:
        have, t_prev, x0, p0 = imm_initialise(d, first - 1, sigma, params.p0_scale)
        xcv, xct, pcv, pct = x0.copy(), x0.copy(), p0.copy(), p0.copy()
        mu0, mu1 = IMM_MU0
    last_try = first - 1
    for i in range(first, n):
        if have:
            has_z = d.valid[i] == 1
            xcv, pcv, xct, pct, mu0, mu1, nis = imm_step(
                t_prev,
                xcv,
                pcv,
                xct,
                pct,
                mu0,
                mu1,
                float(d.t[i]),
                bool(has_z),
                float(d.z[i]),
                float(d.ox[i]),
                float(d.oy[i]),
                r2,
                params.sigma_cv,
                params.sigma_ct,
                params.sigma_omega,
                params.switch_per_s,
            )
            t_prev = float(d.t[i])
            if nis_out is not None:
                nis_out.append(float(nis))
            est = imm_estimate(xcv, pcv, xct, pct, mu0, mu1)
            if _plausible5(float(d.ox[i]), float(d.oy[i]), est):
                rows.append(_row(d, est, i, True))
                continue
            have = False
            last_try = i - EKF_REINIT_EVERY
        rows.append(_row(d, None, i, False))
        if i - last_try >= EKF_REINIT_EVERY:
            have, t_prev, x0, p0 = imm_initialise(d, i, sigma, params.p0_scale)
            if have:
                xcv, xct, pcv, pct = x0.copy(), x0.copy(), p0.copy(), p0.copy()
                mu0, mu1 = IMM_MU0
            last_try = i
    return {
        "record": "prediction",
        "scenario_index": d.index,
        "estimator": imm_name(params),
        "mode": "per_timestep",
        "rows": rows,
    }
