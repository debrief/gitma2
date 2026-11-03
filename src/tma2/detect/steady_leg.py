"""Steady-leg pre-processor (research trial after Gate D; docs/research/07).

On a window where target and ownship both hold course and speed, relative position is linear in
time, so the bearings follow an arctan law, tan b(τ) = (A + Bτ) / (C + Dτ): a 3-parameter curve
(range is a free scale). Ownship's motion is known exactly, so the general form subtracts it:
b(τ) = atan2(x + vx·τ − oₓ(τ), y + vy·τ − o_y(τ)), with (x, y, vx, vy) the target state at the
window's last row (τ = t − t_k). A target manoeuvre inside the window breaks the law.

Per row k and window W (rows k − W + 1 … k):

* **one-leg fit**: Levenberg–Marquardt on the window (gitma's LM, ``references.lsq``), warm-started
  from row k − 1's fit propagated by one step, or from gitma's grid start;
* **misfit**: the fit's cost / σ² / (n − 3), about 1 on a steady leg (3 effective parameters
  when ownship holds course, since range is a free scale);
* **split statistic**: the linearised two-leg test at the window's own fit. The one-leg columns
  are projected out, and Λ(τ) = (Pr)ᵀPJ(JᵀPJ)⁻¹JᵀPr for a velocity change at τ. It reports the
  maximum and the row where it occurs. This is the Gate D GLR with the linearisation point moved
  from the whole-history fit, wrong after the first manoeuvre, to the window's own fit.

All in numba; one scenario is about 360 rows × (one small LM + one W × W split scan).
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from tma2.detect.controls import _basis, _project_out, _wrap
from tma2.references import lsq

MAX_ITER = 20
RESTART_EVERY = 6


@njit(cache=True)
def _fit(
    tt: np.ndarray,
    oxs: np.ndarray,
    oys: np.ndarray,
    zs: np.ndarray,
    vs: np.ndarray,
    start: np.ndarray,
    m: int,
) -> tuple[np.ndarray, float]:
    """gitma's LM on the window; a solution collapsing onto ownship (zero range, a division by
    zero in the Jacobian) is a failed fit: NaN state, infinite cost."""
    try:
        th, _conv, _it, c = lsq.levenberg_marquardt(tt, oxs, oys, zs, vs, start, m, MAX_ITER)
    except Exception:  # noqa: BLE001
        return np.full(4, np.nan), math.inf
    return th, c


def ownship_legs(course: np.ndarray, speed: np.ndarray, tol: float = 1e-6) -> np.ndarray:
    """leg_start [R]: for each row, the first row of ownship's current steady leg, or −1 while
    ownship is turning (course or speed differs from the previous row's). Ownship motion is known
    exactly. Pass zeros to ``window_fits`` / ``split_stat`` for unrestricted windows; restricting
    windows to ownship legs (Debrief's practice) cost detection power here (note 07 §3)."""
    n = course.shape[0]
    out = np.full(n, -1, dtype=np.int64)
    change = np.zeros(n, dtype=np.bool_)
    for k in range(1, n):
        d = course[k] - course[k - 1]
        dc = abs(math.atan2(math.sin(d), math.cos(d)))
        if dc > tol or abs(speed[k] - speed[k - 1]) > tol:
            change[k] = True
    start = 0
    for k in range(n):
        if change[k]:
            start = k + 1
            continue
        out[k] = start
    return out


@njit(cache=True)
def window_fits(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    window: int,
    leg_start: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(state [R, 4] at each row's window end, ok [R], misfit [R]) for one scenario. Windows
    start no earlier than ``leg_start[k]`` (the first row of ownship's current steady leg, −1
    during an ownship turn: no fit), as Debrief's zig detector fits only within ownship legs."""
    n = t.shape[0]
    state = np.zeros((n, 4))
    ok = np.zeros(n, dtype=np.bool_)
    misfit = np.full(n, np.nan)
    have = False
    prev = np.zeros(4)
    s2 = max(sigma, 1e-4) ** 2
    for k in range(n):
        if leg_start[k] < 0:
            have = False
            continue
        a = max(leg_start[k], k - window + 1)
        m = k - a + 1
        nv = 0
        for i in range(a, k + 1):
            if valid[i] == 1:
                nv += 1
        if nv < 6:
            have = False
            continue
        tt = np.empty(m)
        for i in range(m):
            tt[i] = t[a + i] - t[k]
        oxs = ox[a : k + 1]
        oys = oy[a : k + 1]
        zs = z[a : k + 1]
        vs = valid[a : k + 1]
        if have:
            dt = t[k] - t[k - 1]
            start = prev.copy()
            start[0] += prev[2] * dt
            start[1] += prev[3] * dt
        else:
            found, start = lsq.grid_start(tt, oxs, oys, zs, vs, m)
            if not found:
                continue
        th, c = _fit(tt, oxs, oys, zs, vs, start, m)
        if have and k % RESTART_EVERY == 0:
            # a warm start can follow the previous leg into a poor minimum after a manoeuvre;
            # every few rows a grid restart competes, and the lower cost is kept
            found, g = lsq.grid_start(tt, oxs, oys, zs, vs, m)
            if found:
                th2, c2 = _fit(tt, oxs, oys, zs, vs, g, m)
                if c2 < c:
                    th, c = th2, c2
        good = math.isfinite(c)
        for j in range(4):
            if not math.isfinite(th[j]):
                good = False
        if not good:
            have = False
            continue
        state[k] = th
        ok[k] = True
        misfit[k] = c / s2 / max(nv - 3, 1)
        prev = th
        have = True
    return state, ok, misfit


@njit(cache=True)
def split_stat(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    state: np.ndarray,
    ok: np.ndarray,
    window: int,
    leg_start: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """(Λ_max [R], row of the best split [R], −1 where undefined) at each row's own fit."""
    n = t.shape[0]
    out = np.zeros(n)
    where = np.full(n, -1, dtype=np.int64)
    r = np.zeros(window)
    gx = np.zeros(window)
    gy = np.zeros(window)
    tt = np.zeros(window)
    rows = np.zeros(window, dtype=np.int64)
    for k in range(n):
        if not ok[k]:
            continue
        a = max(leg_start[k], k - window + 1)
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
            rows[m] = i
            m += 1
        if m < 6:
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
        best_row = -1
        jm = np.empty((m, 2))
        for c in range(1, m - 2):
            t_tau = tt[c]
            for i in range(m):
                h = tt[i] - t_tau
                h = h if h > 0 else 0.0
                jm[i, 0] = h * gx[i]
                jm[i, 1] = h * gy[i]
            p0 = _project_out(ub, jm[:, 0].copy())
            p1 = _project_out(ub, jm[:, 1].copy())
            a11 = a12 = a22 = b1 = b2 = 0.0
            for i in range(m):
                a11 += p0[i] * p0[i]
                a12 += p0[i] * p1[i]
                a22 += p1[i] * p1[i]
                b1 += p0[i] * rr[i]
                b2 += p1[i] * rr[i]
            det = a11 * a22 - a12 * a12
            if not det > 1e-12 * max(a11 * a22, 1e-300):
                continue
            lam = (a22 * b1 * b1 - 2.0 * a12 * b1 * b2 + a11 * b2 * b2) / det
            if lam > best:
                best = lam
                best_row = rows[c]
        out[k] = best
        where[k] = best_row
    return out, where
