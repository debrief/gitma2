"""Batch least-squares bearings-only solver, ported from gitma ``packages/classical/src/lsq.ts``.

Levenberg–Marquardt-damped Gauss–Newton on θ = (x0, y0, vx, vy) at window start with a
constant-velocity target. Every function is a numba kernel over plain arrays; the arithmetic
order follows gitma's so that results agree to float32 after up to 50 iterations.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from tma2.sim.geometry import TWO_PI, bearing_of

MAX_ITERATIONS = 50
GRID_EVERY = 6
LAMBDA0 = 1e-3
LAMBDA_MAX = 1e12
GRID_SPEEDS = (2.0, 5.0, 9.0)


@njit(cache=True)
def angle_diff(a: float, b: float) -> float:
    """Signed smallest difference a − b in (−π, π] (gitma ``angleDiff``)."""
    return math.atan2(math.sin(a - b), math.cos(a - b))


@njit(cache=True)
def cost(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    th: np.ndarray,
    upto: int,
) -> float:
    """Sum of squared wrapped bearing residuals over valid samples [0, upto)."""
    c = 0.0
    x0, y0, vx, vy = th[0], th[1], th[2], th[3]
    for i in range(upto):
        if valid[i] != 1:
            continue
        ti = t[i]
        h = bearing_of(x0 + vx * ti - ox[i], y0 + vy * ti - oy[i])
        r = angle_diff(z[i], h)
        c += r * r
    return c


@njit(cache=True)
def normal_equations(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    th: np.ndarray,
    upto: int,
) -> tuple[np.ndarray, np.ndarray]:
    """JᵀJ (4×4) and Jᵀr for residuals r = z − h."""
    jtj = np.zeros((4, 4))
    jtr = np.zeros(4)
    x0, y0, vx, vy = th[0], th[1], th[2], th[3]
    g = np.zeros(4)
    for i in range(upto):
        if valid[i] != 1:
            continue
        ti = t[i]
        dx = x0 + vx * ti - ox[i]
        dy = y0 + vy * ti - oy[i]
        rho2 = dx * dx + dy * dy
        g[0] = dy / rho2
        g[1] = -dx / rho2
        g[2] = ti * g[0]
        g[3] = ti * g[1]
        r = angle_diff(z[i], bearing_of(dx, dy))
        for a in range(4):
            ga = g[a]
            jtr[a] = jtr[a] + ga * r
            for b in range(4):
                jtj[a, b] = jtj[a, b] + ga * g[b]
    return jtj, jtr


@njit(cache=True)
def solve4(a: np.ndarray, b: np.ndarray) -> tuple[bool, np.ndarray]:
    """Solve the 4×4 system A x = b by Gaussian elimination with partial pivoting."""
    m = a.copy()
    x = b.copy()
    for c in range(4):
        p = c
        for r in range(c + 1, 4):
            if abs(m[r, c]) > abs(m[p, c]):
                p = r
        pivot = m[p, c]
        if not math.isfinite(pivot) or abs(pivot) < 1e-300:
            return False, x
        if p != c:
            for k in range(4):
                tmp = m[c, k]
                m[c, k] = m[p, k]
                m[p, k] = tmp
            tb = x[c]
            x[c] = x[p]
            x[p] = tb
        for r in range(c + 1, 4):
            f = m[r, c] / pivot
            for k in range(c, 4):
                m[r, k] = m[r, k] - f * m[c, k]
            x[r] = x[r] - f * x[c]
    for r in range(3, -1, -1):
        s = x[r]
        for k in range(r + 1, 4):
            s -= m[r, k] * x[k]
        x[r] = s / m[r, r]
    for k in range(4):
        if not math.isfinite(x[k]):
            return False, x
    return True, x


@njit(cache=True)
def levenberg_marquardt(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    start: np.ndarray,
    upto: int,
    max_iterations: int,
) -> tuple[np.ndarray, bool, int, float]:
    """LM from ``start`` on valid samples [0, upto): (theta, converged, iterations, cost)."""
    th = start.copy()
    c = cost(t, ox, oy, z, valid, th, upto)
    lam = LAMBDA0
    for it in range(1, max_iterations + 1):
        jtj, jtr = normal_equations(t, ox, oy, z, valid, th, upto)
        accepted = False
        while lam <= LAMBDA_MAX:
            damped = jtj.copy()
            for k in range(4):
                damped[k, k] = jtj[k, k] * (1.0 + lam)
            ok, step = solve4(damped, jtr)
            if ok:
                nxt = th + step
                cn = cost(t, ox, oy, z, valid, nxt, upto)
                if cn <= c:
                    done = (c - cn <= 1e-12 * c) or (cn < 1e-24)
                    th = nxt
                    c = cn
                    lam = max(lam / 10.0, 1e-12)
                    accepted = True
                    if done:
                        return th, True, it, c
                    break
            lam *= 10.0
        if not accepted:
            return th, True, it, c
    return th, False, max_iterations, c


@njit(cache=True)
def first_valid(valid: np.ndarray, upto: int) -> int:
    for i in range(upto):
        if valid[i] == 1:
            return i
    return -1


@njit(cache=True)
def grid_start(
    t: np.ndarray, ox: np.ndarray, oy: np.ndarray, z: np.ndarray, valid: np.ndarray, upto: int
) -> tuple[bool, np.ndarray]:
    """Coarse grid start: 12 log-spaced ranges 1–40 km along the first valid bearing × 8
    courses × 3 speeds; the lowest-cost state (gitma ``gridStart``)."""
    best = np.zeros(4)
    i0 = first_valid(valid, upto)
    if i0 < 0:
        return False, best
    t0 = t[i0]
    b0 = z[i0]
    best_cost = math.inf
    th = np.zeros(4)
    found = False
    for ri in range(12):
        r = 1000.0 * math.pow(40.0, ri / 11.0)
        px = ox[i0] + r * math.sin(b0)
        py = oy[i0] + r * math.cos(b0)
        for ci in range(8):
            course = (ci * TWO_PI) / 8.0
            for si in range(3):
                speed = GRID_SPEEDS[si]
                vx = speed * math.sin(course)
                vy = speed * math.cos(course)
                th[0] = px - vx * t0
                th[1] = py - vy * t0
                th[2] = vx
                th[3] = vy
                c = cost(t, ox, oy, z, valid, th, upto)
                if c < best_cost:
                    best_cost = c
                    best = th.copy()
                    found = True
    return found, best


@njit(cache=True)
def solve_batch(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    upto: int,
    max_iterations: int,
) -> tuple[bool, np.ndarray, bool, int, float]:
    """Grid start then LM on samples [0, upto): (found, theta, converged, iterations, cost)."""
    found, start = grid_start(t, ox, oy, z, valid, upto)
    if not found:
        return False, start, False, 0, math.inf
    th, conv, it, c = levenberg_marquardt(t, ox, oy, z, valid, start, upto, max_iterations)
    return True, th, conv, it, c
