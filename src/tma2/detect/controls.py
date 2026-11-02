"""Non-learned manoeuvre detectors for Gate D (spec 004 FR-022–FR-024; Annex A §A.2; research R6).

Each returns a statistic per row of a scenario (0 where it is not defined); a row is an alarm
where the statistic exceeds the tuned threshold h.

* **CUSUM** (gated, Annex A §A.2 as written) on the normalised innovations of the per-timestep
  batch least squares: with the estimate at row k − 1 (position p, velocity v, from the
  warm-started per-timestep solve), b̂_k = atan2 of (p + v·(t_k − t_{k−1}) − ownship_k),
  ν_k = wrap(z_k − b̂_k) / σ and S_k = max(0, S_{k−1} + ν_k² − 1 − δ), δ = 0.5; rows without a
  bearing or without a usable estimate at k − 1 leave S unchanged. The single-leg fit is wrong
  after a scenario's first manoeuvre, so its innovations stay biased and S grows on later held
  legs (measured on validation seed 304: h = 72 at a 5% held-leg false-alarm rate, 10% of spans
  detected); this is a property of the Annex's definition and is reported as such.
* **CUSUM on the EKF's innovations** (reported, not gated): the same recursion on the frozen
  EKF's normalised innovation squared ν² / (H P Hᵀ + σ²) (Bar-Shalom's χ² detector); the filter
  re-converges after a manoeuvre.
* **GLR** for a velocity change in the last W = 30 samples (Annex A §A.2: a windowed fit of one
  versus two constant-velocity legs; Ru, Jilkov, Li and Bashi), linearised at the per-timestep
  least-squares estimate θ̂_k: on the window's valid rows, r_i = wrap(z_i − b_i(θ̂_k)) / σ, the
  one-leg columns A_i = (g_i, (t_i − t_k) g_i) with g_i = (dy_i, −dx_i) / (ρ_i² σ), and the change
  columns J_i(τ) = (t_i − t_τ)⁺ g_i. The one-leg fit over the window is projected out
  (P = I − U Uᵀ, U an orthonormal basis of A's well-determined directions), so only a change inside
  the window counts; Λ(τ) = (Pr)ᵀPJ (JᵀPJ)⁻¹ JᵀP r, the statistic the maximum over τ with at least
  two valid rows after it. (R6 first wrote Λ without the projection; on manoeuvring data that
  tests the whole-window fit's error, not a change in the window.) Measured on seed 304: 57% of
  spans detected at a 5% held-leg false-alarm rate (W = 60: 29%).
* **IMM mode probability**: the frozen IMM's coordinated-turn probability μ_CT per row
  (``imm_predict(mu_ct_out=…)``), 0 where the filter is not running (44% at 5%).

Alarm episodes less than 60 s apart are merged when counting rising edges, for every detector
alike (``matching``).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from numba import njit

from tma2.eval.errors import plausible_row
from tma2.references.classical import BearingData
from tma2.references.ekf import ekf_predict
from tma2.references.imm import ImmParams, imm_predict

CUSUM_DRIFT = 0.5
GLR_WINDOW = 30
TWO_PI = 2.0 * math.pi


def ls_states(d: BearingData, rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    """Per-row (x, y, vx, vy) from a per-timestep prediction's rows and a usable flag
    (``plausible_row``); rows the prediction does not cover are unusable."""
    n = d.n
    state = np.zeros((n, 4))
    ok = np.zeros(n, dtype=np.bool_)
    dt = float(d.t[1] - d.t[0]) if n > 1 else 10.0
    for r in rows:
        k = int(math.floor(float(r["timestamp_s"]) / dt + 0.5))
        if not 0 <= k < n or not plausible_row(r):
            continue
        c, s = float(r["course_rad"]), float(r["speed_mps"])
        state[k] = (float(r["x_m"]), float(r["y_m"]), s * math.sin(c), s * math.cos(c))
        ok[k] = True
    return state, ok


@njit(cache=True)
def _wrap(x: float) -> float:
    return x - TWO_PI * math.floor(x / TWO_PI + 0.5)


@njit(cache=True)
def cusum_from_nis(nis: np.ndarray, drift: float) -> np.ndarray:
    """S_k from per-row NIS values (NaN: no bearing, S unchanged)."""
    n = nis.shape[0]
    s = np.zeros(n)
    cur = 0.0
    for k in range(n):
        q = nis[k]
        if q == q:  # not NaN
            cur = max(0.0, cur + q - 1.0 - drift)
        s[k] = cur
    return s


@njit(cache=True)
def cusum_ls_stat(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    state: np.ndarray,
    ok: np.ndarray,
    drift: float,
) -> np.ndarray:
    """The gated CUSUM (Annex A §A.2) from per-row least-squares states (``ls_states``)."""
    n = t.shape[0]
    nis = np.full(n, np.nan)
    for k in range(1, n):
        if valid[k] != 0 and ok[k - 1]:
            tau = t[k] - t[k - 1]
            px = state[k - 1, 0] + state[k - 1, 2] * tau
            py = state[k - 1, 1] + state[k - 1, 3] * tau
            nu = _wrap(z[k] - math.atan2(px - ox[k], py - oy[k])) / sigma
            nis[k] = nu * nu
    return cusum_from_nis(nis, drift)


def cusum_ekf_stat(d: BearingData, sigma_a: float, p0_scale: float, r_scale: float) -> np.ndarray:
    """The reported CUSUM on the frozen EKF's innovations (0 before its first row)."""
    nis: list[float] = []
    pred = ekf_predict(d, sigma_a, p0_scale, r_scale, nis_out=nis)
    full = np.full(d.n, np.nan)
    dt = float(d.t[1] - d.t[0]) if d.n > 1 else 10.0
    for r, q in zip(pred["rows"], nis, strict=True):
        k = int(math.floor(float(r["timestamp_s"]) / dt + 0.5))
        if 0 <= k < d.n:
            full[k] = q
    return cusum_from_nis(full, CUSUM_DRIFT)


@njit(cache=True)
def _basis(a: np.ndarray) -> np.ndarray:
    """Orthonormal basis [m, rank] of the column space of a [m, c]: columns scaled to unit norm,
    then modified Gram–Schmidt twice; a column whose remainder is below 1e-6 is dropped (the
    window's unobservable directions, e.g. range along the bearing)."""
    m, c = a.shape
    q = np.zeros((m, c))
    rank = 0
    for j in range(c):
        v = a[:, j].copy()
        nv = math.sqrt(np.sum(v * v))
        if not nv > 0:
            continue
        v = v / nv
        for _ in range(2):
            for i in range(rank):
                v = v - np.sum(q[:, i] * v) * q[:, i]
        nr = math.sqrt(np.sum(v * v))
        if nr > 1e-6:
            q[:, rank] = v / nr
            rank += 1
    return np.ascontiguousarray(q[:, :rank])


@njit(cache=True)
def _project_out(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """(I − U Uᵀ) v with explicit loops (numba's matrix products need SciPy)."""
    m, c = u.shape
    out = v.copy()
    for j in range(c):
        dot = 0.0
        for i in range(m):
            dot += u[i, j] * v[i]
        for i in range(m):
            out[i] -= dot * u[i, j]
    return out


@njit(cache=True)
def glr_stat(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    state: np.ndarray,
    ok: np.ndarray,
    window: int,
) -> np.ndarray:
    n = t.shape[0]
    out = np.zeros(n)
    r = np.zeros(window)
    gx = np.zeros(window)
    gy = np.zeros(window)
    tt = np.zeros(window)
    for k in range(n):
        if not ok[k]:
            continue
        a = max(0, k - window + 1)
        m = 0
        for i in range(a, k + 1):
            if valid[i] == 0:
                continue
            tau = t[i] - t[k]
            dx = state[k, 0] + state[k, 2] * tau - ox[i]
            dy = state[k, 1] + state[k, 3] * tau - oy[i]
            rho2 = dx * dx + dy * dy
            if not rho2 > 0:
                continue
            r[m] = _wrap(z[i] - math.atan2(dx, dy)) / sigma
            gx[m] = dy / (rho2 * sigma)
            gy[m] = -dx / (rho2 * sigma)
            tt[m] = t[i]
            m += 1
        if m < 4:
            continue
        amat = np.empty((m, 4))
        for i in range(m):
            h = tt[i] - t[k]
            amat[i, 0] = gx[i]
            amat[i, 1] = gy[i]
            amat[i, 2] = h * gx[i]
            amat[i, 3] = h * gy[i]
        ub = _basis(amat)
        rr = _project_out(ub, r[:m].copy())
        best = 0.0
        jm = np.empty((m, 2))
        for c in range(m - 2):
            t_tau = tt[c]
            for i in range(m):
                h = tt[i] - t_tau
                h = h if h > 0 else 0.0
                jm[i, 0] = h * gx[i]
                jm[i, 1] = h * gy[i]
            pj = np.empty((m, 2))
            pj[:, 0] = _project_out(ub, jm[:, 0].copy())
            pj[:, 1] = _project_out(ub, jm[:, 1].copy())
            a11 = a12 = a22 = b1 = b2 = 0.0
            for i in range(m):
                a11 += pj[i, 0] * pj[i, 0]
                a12 += pj[i, 0] * pj[i, 1]
                a22 += pj[i, 1] * pj[i, 1]
                b1 += pj[i, 0] * rr[i]
                b2 += pj[i, 1] * rr[i]
            det = a11 * a22 - a12 * a12
            if not det > 1e-12 * max(a11 * a22, 1e-300):
                continue
            lam = (a22 * b1 * b1 - 2.0 * a12 * b1 * b2 + a11 * b2 * b2) / det
            if lam > best:
                best = lam
        out[k] = best
    return out


def imm_mode_stat(d: BearingData, params: ImmParams) -> np.ndarray:
    """μ_CT per row of the window (0 before the IMM's first row and where it is not running)."""
    mu: list[float] = []
    pred = imm_predict(d, params, mu_ct_out=mu)
    out = np.zeros(d.n)
    dt = float(d.t[1] - d.t[0]) if d.n > 1 else 10.0
    for r, m in zip(pred["rows"], mu, strict=True):
        k = int(math.floor(float(r["timestamp_s"]) / dt + 0.5))
        if 0 <= k < d.n and math.isfinite(m):
            out[k] = m
    return out


def parse_imm_name(name: str) -> ImmParams:
    """Inverse of ``imm_name`` (imm-cv…-ct…-w…-s…[-p…][-r…])."""
    parts = name.split("-")
    if parts[0] != "imm":
        raise ValueError(f"not an IMM setting: {name}")
    vals: dict[str, float] = {}
    for p in parts[1:]:
        for key in ("cv", "ct", "w", "s", "p", "r"):
            if p.startswith(key) and _is_number(p[len(key) :]):
                vals[key] = float(p[len(key) :])
                break
        else:
            raise ValueError(f"{name}: unknown part {p}")
    return ImmParams(
        vals["cv"], vals["ct"], vals["w"], vals["s"], vals.get("p", 1.0), vals.get("r", 1.0)
    )


def _is_number(x: str) -> bool:
    try:
        float(x)
    except ValueError:
        return False
    return True


def tune_threshold(values: np.ndarray, target: float) -> tuple[float, float]:
    """The threshold h whose exceedance fraction (values > h) over ``values`` is closest to
    ``target`` (ties: the higher h), and that fraction."""
    v = np.sort(np.asarray(values, dtype=np.float64))
    n = v.size
    if n == 0:
        raise ValueError("no rows to tune on")
    cands = np.unique(np.concatenate([v, [v[0] - 1.0]]))
    best_h, best_f, best_gap = math.inf, 0.0, math.inf
    for h in cands[::-1]:
        f = float(n - np.searchsorted(v, h, side="right")) / n
        gap = abs(f - target)
        if gap < best_gap - 1e-15:
            best_h, best_f, best_gap = float(h), f, gap
    return best_h, best_f
