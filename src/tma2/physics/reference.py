"""NumPy reference implementation of the physics layer (the documentation of record).

The physics layer is a piecewise-constant-velocity bearings-only batch solve whose *inputs* a
learned component may supply and whose *estimate* is produced by physics (constitution III).

Model (per scenario, rows i ≤ k, times t_i, ownship o_i, bearings z_i with validity v_i, σ):

- Parameters θ = (p0, u0, d_1 … d_M): position at window start, velocity on the first leg, and
  M velocity increments at candidate knot rows r_1 … r_M (the M rows with the largest changepoint
  weight c among rows ≤ k; TopK is a standard operator, so the graph has no control flow).
- Position at row i: p_i = p0 + u0 · t_i + Σ_m c_m d_m (t_i − t_{r_m})⁺, with (x)⁺ = max(x, 0).
  Velocity at row i: u_i = u0 + Σ_m c_m d_m [t_{r_m} ≤ t_i]. With every c_m = 0 the increments are
  inert and the model is gitma's constant-velocity θ = (x0, y0, vx, vy) exactly.
- Residuals: bearing r_i = √w_i · wrap(z_i − atan2(dx_i, dy_i)) / σ with w_i = v_i · exp(logw_i);
  ridge prior on each increment r_m^ridge = √c_m · d_m / τ_r (per component); speed-continuity
  prior r_m^speed = √(c_m s_m) · (‖u_after,m‖ − ‖u_before,m‖) / τ_s.
- Solve: K fixed Gauss-Newton iterations with Levenberg damping (JᵀJ)ᵢᵢ(1 + λ). Each iteration
  tries T damping values λ, 10λ, …, 10^(T−1)λ and takes the first step that does not increase the
  cost, as gitma's inner retry loop does; λ ← max(λ_used/10, 1e-12) on accept, min(10^T λ, 1e12)
  when no trial is accepted (gitma's constants). Start: θ0 = (grid start, increments 0).
- Output: state at row k, s_k = (p_k, u_k), its covariance G (JᵀJ)⁻¹ Gᵀ with G = ∂s_k/∂θ (the
  residuals are σ-normalised, so no σ² factor), the
  final cost and gitma's plausibility flag.

This file is plain NumPy and loops; ``layer.py`` is the batched tensor version with identical
arithmetic order where it matters (tested to 1e-6).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

TAU_RIDGE_MPS = 3.0
TAU_SPEED_MPS = 1.0
LAMBDA0 = 1e-3
# Damping values tried per iteration (λ, 10λ, …) and the fixed iteration count. P0 panel round 1
# measured them on every fixture row against the cold-start solver: 40 × 1 stopped short on 159
# rows, 40 × 4 on 8, 60 × 2 and 100 × 1 on none; 100 × 1 was the fastest (202 s against 261 s).
TRIALS = 1
ITERATIONS = 100
LAMBDA_MIN = 1e-12
LAMBDA_MAX = 1e12
MAX_SPEED_MPS = 25.0
MAX_RANGE_M = 100_000.0
MIN_SIGMA_RAD = 1e-4


@dataclass
class PhysicsResult:
    state: np.ndarray  # (x, y, vx, vy) at row k
    cov: np.ndarray  # 4×4
    cost: float
    plausible: bool
    theta: np.ndarray  # full parameter vector
    knots: np.ndarray  # candidate knot rows
    knot_weights: np.ndarray


def wrap(a: np.ndarray) -> np.ndarray:
    return np.arctan2(np.sin(a), np.cos(a))


def select_knots(changepoint: np.ndarray, k: int, m: int) -> tuple[np.ndarray, np.ndarray]:
    """The M rows (≤ k, > 0) with the largest changepoint weight (ties: lower row first), padded
    with weight 0 at row k when fewer than M rows exist."""
    c = np.array(changepoint[: k + 1], dtype=np.float64)
    c[0] = -1.0  # row 0 cannot be a knot (no leg before it)
    order = np.argsort(-c, kind="stable")[:m]
    rows = np.array(order, dtype=np.int64)
    weights = np.clip(c[rows], 0.0, 1.0)
    if rows.shape[0] < m:
        pad = m - rows.shape[0]
        rows = np.concatenate([rows, np.full(pad, k, dtype=np.int64)])
        weights = np.concatenate([weights, np.zeros(pad)])
    return rows, weights


def spd_solve(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Jacobi-scaled Gauss–Jordan elimination without pivoting, the same arithmetic as the tensor
    layer's ``spd_solve`` (so both implementations follow the same iteration path)."""
    p = a.shape[0]
    dinv = 1.0 / np.sqrt(np.maximum(np.diag(a), 1e-300))
    m = a * dinv[:, None] * dinv[None, :]
    rhs = b * dinv
    rows = [m[i].copy() for i in range(p)]
    r = [float(v) for v in rhs]
    for j in range(p):
        pivot = rows[j][j]
        for i in range(p):
            if i == j:
                continue
            f = rows[i][j] / pivot
            rows[i] = rows[i] - f * rows[j]
            r[i] = r[i] - f * r[j]
    y = np.array([r[j] / rows[j][j] for j in range(p)])
    return y * dinv


def _positions(
    theta: np.ndarray, t: np.ndarray, t_knots: np.ndarray, c: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """p_i (n×2) and the design A (n × M) with A[i, m] = c_m (t_i − t_rm)⁺."""
    p0 = theta[0:2]
    u0 = theta[2:4]
    d = theta[4:].reshape(-1, 2)
    a = c[None, :] * np.maximum(t[:, None] - t_knots[None, :], 0.0)  # n × M
    p = p0[None, :] + u0[None, :] * t[:, None] + a @ d
    return p, a


def _velocity_at(theta: np.ndarray, tk: float, t_knots: np.ndarray, c: np.ndarray) -> np.ndarray:
    u0 = theta[2:4]
    d = theta[4:].reshape(-1, 2)
    active = (c * (t_knots <= tk)).reshape(-1, 1)
    out: np.ndarray = u0 + (active * d).sum(axis=0)
    return out


def _residuals_and_jacobian(
    theta: np.ndarray,
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    w: np.ndarray,
    sigma: float,
    t_knots: np.ndarray,
    c: np.ndarray,
    s: np.ndarray,
    tau_r: float,
    tau_s: float,
    skip: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    n = t.shape[0]
    m = t_knots.shape[0]
    npar = 4 + 2 * m
    p, a = _positions(theta, t, t_knots, c)
    dx = p[:, 0] - ox
    dy = p[:, 1] - oy
    rho2 = dx * dx + dy * dy
    sw = np.sqrt(w) / sigma
    r_b = sw * wrap(z - np.arctan2(dx, dy))
    # ∂h/∂px = dy/ρ², ∂h/∂py = −dx/ρ²; residual r = z − h, so ∂r/∂θ = −∂h/∂θ.
    gx = dy / rho2
    gy = -dx / rho2
    jac = np.zeros((n + 2 * m + m, npar))
    jac[:n, 0] = -sw * gx
    jac[:n, 1] = -sw * gy
    jac[:n, 2] = -sw * gx * t
    jac[:n, 3] = -sw * gy * t
    for mm in range(m):
        jac[:n, 4 + 2 * mm] = -sw * gx * a[:, mm]
        jac[:n, 5 + 2 * mm] = -sw * gy * a[:, mm]
    # Ridge on increments.
    d = theta[4:].reshape(-1, 2)
    r_ridge = np.zeros(2 * m)
    for mm in range(m):
        wgt = math.sqrt(c[mm]) / tau_r
        r_ridge[2 * mm] = wgt * d[mm, 0]
        r_ridge[2 * mm + 1] = wgt * d[mm, 1]
        jac[n + 2 * mm, 4 + 2 * mm] = wgt
        jac[n + 2 * mm + 1, 5 + 2 * mm] = wgt
    # Speed continuity across each knot: ‖u_after‖ − ‖u_ref‖, u_ref = u_before with the previous
    # knot's increment removed in proportion to skip.
    if skip is None:
        skip = np.zeros(m)
    r_speed = np.zeros(m)
    order = np.argsort(t_knots, kind="stable")
    u = theta[2:4].copy()
    prev_idx = -1
    for idx in order:
        u_before = u.copy()
        u_ref = u_before - (skip[idx] * c[prev_idx] * d[prev_idx] if prev_idx >= 0 else 0.0)
        u_after = u_before + c[idx] * d[idx]
        wgt = math.sqrt(c[idx] * s[idx]) / tau_s
        nr = math.hypot(u_ref[0], u_ref[1])
        na = math.hypot(u_after[0], u_after[1])
        r_speed[idx] = wgt * (na - nr)
        row = n + 2 * m + idx
        gr = u_ref / nr if nr > 0 else np.zeros(2)
        ga = u_after / na if na > 0 else np.zeros(2)
        jac[row, 2:4] = wgt * (ga - gr)
        for prev in order:
            if t_knots[prev] < t_knots[idx] or (t_knots[prev] == t_knots[idx] and prev < idx):
                share = 1.0 - (skip[idx] if prev == prev_idx else 0.0)
                jac[row, 4 + 2 * prev : 6 + 2 * prev] = wgt * c[prev] * (ga - share * gr)
        jac[row, 4 + 2 * idx : 6 + 2 * idx] = wgt * c[idx] * ga
        u = u_after
        if c[idx] > 0:
            prev_idx = idx  # predecessors are counted among active knots only
    # Signs: residual convention r = (target − model) for bearings; priors are "model" terms, and
    # GN uses J = ∂r/∂θ consistently, so we negate the prior Jacobians to match r = −model.
    jac[n:, :] *= -1.0
    r = np.concatenate([r_b, -r_ridge, -r_speed])
    return r, jac


def solve(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    k: int,
    changepoint: np.ndarray,
    speed_weight: np.ndarray,
    log_weight: np.ndarray,
    theta0: np.ndarray,
    iterations: int = ITERATIONS,
    knots_m: int = 8,
    tau_r: float = TAU_RIDGE_MPS,
    tau_s: float = TAU_SPEED_MPS,
    speed_skip: np.ndarray | None = None,
    trials: int = TRIALS,
) -> PhysicsResult:
    """The physics layer for one scenario at row k (see the module docstring)."""
    sigma = max(float(sigma), MIN_SIGMA_RAD)
    rows, c = select_knots(changepoint, k, knots_m)
    s = np.clip(np.array([speed_weight[r] for r in rows], dtype=np.float64), 0.0, 1.0)
    sk = (
        np.clip(np.array([speed_skip[r] for r in rows], dtype=np.float64), 0.0, 1.0)
        if speed_skip is not None
        else np.zeros(knots_m)
    )
    t_knots = np.array([t[r] for r in rows], dtype=np.float64)
    tt = t[: k + 1].astype(np.float64)
    w = valid[: k + 1].astype(np.float64) * np.exp(log_weight[: k + 1].astype(np.float64))
    oxx, oyy, zz = (
        ox[: k + 1].astype(np.float64),
        oy[: k + 1].astype(np.float64),
        z[: k + 1].astype(np.float64),
    )
    theta = np.concatenate([np.asarray(theta0, dtype=np.float64), np.zeros(2 * knots_m)])

    def cost_of(th: np.ndarray) -> float:
        r, _ = _residuals_and_jacobian(
            th, tt, oxx, oyy, zz, w, sigma, t_knots, c, s, tau_r, tau_s, sk
        )
        return float(r @ r)

    cost = cost_of(theta)
    lam = LAMBDA0
    for _ in range(iterations):
        r, jac = _residuals_and_jacobian(
            theta, tt, oxx, oyy, zz, w, sigma, t_knots, c, s, tau_r, tau_s, sk
        )
        jtj = jac.T @ jac
        jtr = -(jac.T @ r)
        # Inert parameters (knot weight 0) have an empty row: regularise so the solve is defined.
        inert = np.diag((np.diag(jtj) == 0).astype(np.float64))
        # gitma's inner retry, truncated at `trials`: try λ, 10λ, 100λ, … and take the first
        # step that does not increase the cost (the layer evaluates them side by side).
        accepted = False
        for j in range(trials):
            lam_j = min(lam * 10.0**j, LAMBDA_MAX)
            step = spd_solve(jtj + np.diag(np.diag(jtj) * lam_j) + inert, jtr)
            cand = theta + step
            cand_cost = cost_of(cand)
            if cand_cost <= cost and math.isfinite(cand_cost):
                theta, cost = cand, cand_cost
                lam = max(lam_j / 10.0, LAMBDA_MIN)
                accepted = True
                break
        if not accepted:
            lam = min(lam * 10.0**trials, LAMBDA_MAX)
    # State at row k and its covariance.
    tk = float(tt[k])
    pk, _ = _positions(theta, np.array([tk]), t_knots, c)
    uk = _velocity_at(theta, tk, t_knots, c)
    state = np.array([pk[0, 0], pk[0, 1], uk[0], uk[1]])
    g = np.zeros((4, theta.shape[0]))
    g[0, 0] = 1.0
    g[1, 1] = 1.0
    g[0, 2] = tk
    g[1, 3] = tk
    g[2, 2] = 1.0
    g[3, 3] = 1.0
    for mm in range(knots_m):
        dtm = c[mm] * max(tk - t_knots[mm], 0.0)
        act = c[mm] * (1.0 if t_knots[mm] <= tk else 0.0)
        g[0, 4 + 2 * mm] = dtm
        g[1, 5 + 2 * mm] = dtm
        g[2, 4 + 2 * mm] = act
        g[3, 5 + 2 * mm] = act
    _, jac = _residuals_and_jacobian(
        theta, tt, oxx, oyy, zz, w, sigma, t_knots, c, s, tau_r, tau_s, sk
    )
    jtj = jac.T @ jac + np.diag((np.abs(jac).sum(axis=0) == 0).astype(np.float64))
    cov = g @ np.stack([spd_solve(jtj, g[i]) for i in range(4)], axis=1)  # σ-normalised residuals
    rng = math.hypot(state[0] - oxx[k], state[1] - oyy[k])
    speed = math.hypot(state[2], state[3])
    plausible = bool(np.all(np.isfinite(state)) and speed <= MAX_SPEED_MPS and rng <= MAX_RANGE_M)
    return PhysicsResult(
        state=state,
        cov=cov,
        cost=cost,
        plausible=plausible,
        theta=theta,
        knots=rows,
        knot_weights=c,
    )
