"""Fisher information and Cramér–Rao bounds for bearings-only estimation.

For a model in which the target position at each sample is linear in parameters θ,
pᵢ = Bᵢ θ, with independent bearing noise σ, the Fisher information from valid bearings i ≤ k at
the true trajectory is I = Σ gᵢgᵢᵀ / σ², gᵢ = Bᵢᵀ (dy/ρ², −dx/ρ²). Bounds on range, course and speed
at row k follow by the delta method: var(f) ≥ ∇fᵀ I⁻¹ ∇f, with ∇f taken through the state map.

Three models (``CrbModel``):

- *full window*: constant velocity, θ = (x0, y0, vx, vy), all bearings up to k; the bound for a
  held-course target (Gate 1).
- *known manoeuvres*: the generator's manoeuvre kinematics (an arc at constant speed for a course
  change, constant acceleration for a speed change) with θ = (x0, y0, vx0, vy0, change_1 …): each
  manoeuvre's start time, duration and kind known, its size unknown; all bearings up to k. The
  bound for an estimator that knows when and how the target manoeuvred (the oracle's regime):
  position continuity carries the earlier legs across the manoeuvre. (Leaving the positions inside
  a manoeuvre free instead decouples the legs, which is no better than per leg.) Defined inside
  manoeuvres too; the positions' Jacobian is taken by central differences.
- *per leg*: constant velocity on the current leg's bearings only. A diagnostic: it ignores the
  earlier legs, so an estimator that knows the manoeuvre times can beat it (panel round 1).

Before the zig the information is singular. Singularity is judged on the Jacobi-scaled matrix
(condition number above 1e12), and directions the bearings cannot see (a dropout inside a
manoeuvre) are allowed only when the state at k does not depend on them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

SINGULAR_COND = 1e12
MIN_SIGMA_RAD = 1e-4


@dataclass
class CrbRow:
    sd_range_rel: float
    sd_course_deg: float
    sd_speed_kt: float
    singular: bool
    # Bound on the covariance of (x, y, vx, vy) at the row, for losses normalised per component.
    state_cov: np.ndarray | None = None


def _information(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    valid: np.ndarray,
    start: int,
    k: int,
    t_ref: float,
    sigma: float,
) -> np.ndarray:
    info = np.zeros((4, 4))
    s2 = max(sigma, MIN_SIGMA_RAD) ** 2
    for i in range(start, k + 1):
        if valid[i] == 0:
            continue
        dx = tx[i] - ox[i]
        dy = ty[i] - oy[i]
        rho2 = dx * dx + dy * dy
        tau = t[i] - t_ref
        g = np.array([dy / rho2, -dx / rho2, tau * dy / rho2, -tau * dx / rho2])
        info += np.outer(g, g) / s2
    return info


def crb_at_row(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    tvx: float,
    tvy: float,
    valid: np.ndarray,
    start: int,
    k: int,
    sigma: float,
) -> CrbRow:
    """Bounds at row k from bearings in [start, k], anchored at t[start] (truth given)."""
    t_ref = float(t[start])
    info = _information(t, ox, oy, tx, ty, valid, start, k, t_ref, sigma)
    tau = float(t[k]) - t_ref
    # state map: p_k = (x0 + vx τ, y0 + vy τ), u_k = (vx, vy)
    g = np.array([[1.0, 0.0, tau, 0.0], [0.0, 1.0, 0.0, tau], [0.0, 0.0, 1.0, 0.0], [0, 0, 0, 1.0]])
    return _bound(info, g, tx[k] - ox[k], ty[k] - oy[k], tvx, tvy)


def _bound(info: np.ndarray, g: np.ndarray, dx: float, dy: float, tvx: float, tvy: float) -> CrbRow:
    """Delta-method bounds at row k from the information ``info`` [P,P] and the state map ``g``
    [4,P] (∂(p_k, u_k)/∂θ), at the true relative position (dx, dy) and velocity (tvx, tvy)."""
    singular = CrbRow(math.nan, math.nan, math.nan, True)
    d = np.diag(info).copy()
    if not np.all(np.isfinite(info)):
        return singular
    seen = d > 0
    if not seen.any():
        return singular
    # Parameters no bearing touches: the state must not depend on them.
    if np.any(np.abs(g[:, ~seen]) > 0):
        return singular
    sub = info[np.ix_(seen, seen)]
    scale = 1.0 / np.sqrt(d[seen])
    scaled = sub * np.outer(scale, scale)
    w, v = np.linalg.eigh(scaled)
    if w[-1] <= 0:
        return singular
    weak = w <= w[-1] / SINGULAR_COND
    gs = g[:, seen] * scale  # state map in scaled coordinates
    if weak.any():
        # Unseen combinations (e.g. a dropout inside a manoeuvre) are allowed only if the state
        # at k does not move along them.
        leak = np.abs(gs @ v[:, weak]).max()
        if leak > 1e-9 * max(np.abs(gs).max(), 1.0):
            return singular
    inv_w = np.where(weak, 0.0, 1.0 / np.where(weak, 1.0, w))
    cov_scaled = (v * inv_w) @ v.T
    cov_state = gs @ cov_scaled @ gs.T  # [4,4] covariance of (p_k, u_k)
    rng = math.hypot(dx, dy)
    speed = math.hypot(tvx, tvy)
    g_r = np.array([dx / rng, dy / rng, 0.0, 0.0])
    # course c = atan2(vx, vy): ∂c/∂vx = vy/s², ∂c/∂vy = −vx/s²
    g_c = np.array([0.0, 0.0, tvy / (speed * speed), -tvx / (speed * speed)])
    g_s = np.array([0.0, 0.0, tvx / speed, tvy / speed])
    var_r = float(g_r @ cov_state @ g_r)
    var_c = float(g_c @ cov_state @ g_c)
    var_s = float(g_s @ cov_state @ g_s)
    if min(var_r, var_c, var_s) < 0:
        return singular
    return CrbRow(
        sd_range_rel=math.sqrt(var_r) / rng,
        sd_course_deg=math.degrees(math.sqrt(var_c)),
        sd_speed_kt=math.sqrt(var_s) / (1852.0 / 3600.0),
        singular=False,
        state_cov=cov_state,
    )


def _pos_vel(
    theta: np.ndarray, t: float, mans: list[tuple[str, float, float]]
) -> tuple[float, float, float, float]:
    """Target position and velocity at time t for θ = (x0, y0, vx0, vy0, change_1 …) under the
    generator's manoeuvre kinematics (0.5.0): a course change is an arc at constant speed, a speed
    change constant acceleration on a constant course; ``mans`` holds (kind, start s, duration s)
    in time order and the j-th change is θ[4 + j]."""
    x, y = float(theta[0]), float(theta[1])
    s = math.hypot(float(theta[2]), float(theta[3]))
    c = math.atan2(float(theta[2]), float(theta[3]))
    now = 0.0
    for j, (kind, ts, dur) in enumerate(mans):
        if t <= ts:
            break
        x += s * math.sin(c) * (ts - now)
        y += s * math.cos(c) * (ts - now)
        tau = min(t - ts, dur)
        ch = float(theta[4 + j])
        if kind == "course":
            w = ch / dur
            if abs(w) < 1e-15:
                x += s * math.sin(c) * tau
                y += s * math.cos(c) * tau
            else:
                x += (s / w) * (math.cos(c) - math.cos(c + w * tau))
                y += (s / w) * (math.sin(c + w * tau) - math.sin(c))
                c += w * tau
        else:
            a = ch / dur
            dist = s * tau + 0.5 * a * tau * tau
            x += dist * math.sin(c)
            y += dist * math.cos(c)
            s += a * tau
        now = ts + tau
        if t <= ts + dur:
            return x, y, s * math.sin(c), s * math.cos(c)
    x += s * math.sin(c) * (t - now)
    y += s * math.cos(c) * (t - now)
    return x, y, s * math.sin(c), s * math.cos(c)


def manoeuvre_model(
    manoeuvres: list[dict[str, Any]], tx0: float, ty0: float, tvx0: float, tvy0: float
) -> tuple[np.ndarray, list[tuple[str, float, float]]]:
    """θ at the truth and the (kind, start, duration) list from a scenario's
    ``parameters.target_manoeuvres`` (duration = |change| / rate)."""
    mans = sorted(manoeuvres, key=lambda m: float(m["start_time_s"]))
    theta = np.array([tx0, ty0, tvx0, tvy0] + [float(m["change"]) for m in mans])
    spec = [
        (str(m["kind"]), float(m["start_time_s"]), abs(float(m["change"])) / float(m["rate"]))
        for m in mans
    ]
    return theta, spec


_FD_STEP = (1.0, 1.0, 1e-3, 1e-3)  # m, m, m/s, m/s; changes: 1e-6 rad or 1e-4 m/s


def _model_jacobian(
    theta: np.ndarray, times: np.ndarray, mans: list[tuple[str, float, float]]
) -> np.ndarray:
    """∂(x, y, vx, vy)(t_i)/∂θ by central differences: [N, 4, P]."""
    n_p = theta.shape[0]
    out = np.empty((times.shape[0], 4, n_p))
    for p in range(n_p):
        h = _FD_STEP[p] if p < 4 else (1e-6 if mans[p - 4][0] == "course" else 1e-4)
        up = theta.copy()
        dn = theta.copy()
        up[p] += h
        dn[p] -= h
        for i, ti in enumerate(times):
            a = _pos_vel(up, float(ti), mans)
            b = _pos_vel(dn, float(ti), mans)
            out[i, :, p] = [(a[q] - b[q]) / (2 * h) for q in range(4)]
    return out


def crb_known_manoeuvres(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    tvx: np.ndarray,
    tvy: np.ndarray,
    valid: np.ndarray,
    manoeuvres: list[dict[str, Any]],
    rows: list[int],
    sigma: float,
) -> list[CrbRow]:
    """The known-manoeuvres bound (module docstring) at each of ``rows``: one pass builds the
    per-bearing information and accumulates it, so all rows of a scenario cost one Jacobian."""
    theta, mans = manoeuvre_model(
        manoeuvres, float(tx[0]), float(ty[0]), float(tvx[0]), float(tvy[0])
    )
    last = max(rows) if rows else -1
    jac = _model_jacobian(theta, t[: last + 1], mans)
    s2 = max(sigma, MIN_SIGMA_RAD) ** 2
    n_p = theta.shape[0]
    info = np.zeros((n_p, n_p))
    want = set(rows)
    out: dict[int, CrbRow] = {}
    for i in range(last + 1):
        if valid[i] != 0:
            dx = tx[i] - ox[i]
            dy = ty[i] - oy[i]
            rho2 = dx * dx + dy * dy
            gi = (dy / rho2) * jac[i, 0] - (dx / rho2) * jac[i, 1]
            info += np.outer(gi, gi) / s2
        if i in want:
            out[i] = _bound(
                info, jac[i], tx[i] - ox[i], ty[i] - oy[i], float(tvx[i]), float(tvy[i])
            )
    return [out[k] for k in rows]


def leg_start(spans: list[dict[str, Any]], k: int) -> int:
    """First row of the current leg: 0, or the end of the last manoeuvre that ended at or before k.
    A manoeuvre in progress at k makes the leg start at k (no information yet)."""
    start = 0
    for s in spans:
        if s["start_index"] <= k < s["end_index"]:
            return k
        if s["end_index"] <= k:
            start = max(start, int(s["end_index"]))
    return start


def crb_rows(
    own: np.ndarray,
    tgt: np.ndarray,
    obs: np.ndarray,
    sigma: float,
    zig_index: int,
    spans: list[dict[str, Any]] | None,
    rows: list[int],
    model: str | bool = "full_window",
    target_manoeuvres: list[dict[str, Any]] | None = None,
) -> list[CrbRow]:
    """Bounds at the given rows from pack arrays own/tgt [S,5] and obs [S,3]."""
    t = own[:, 0].astype(np.float64)
    ox = own[:, 1].astype(np.float64)
    oy = own[:, 2].astype(np.float64)
    tx = tgt[:, 1].astype(np.float64)
    ty = tgt[:, 2].astype(np.float64)
    course = tgt[:, 3].astype(np.float64)
    speed = tgt[:, 4].astype(np.float64)
    valid = (obs[:, 2] != 0).astype(np.uint8)
    out = []
    if isinstance(model, bool):  # legacy flag: per_leg
        model = "per_leg" if model else "full_window"
    if model not in ("full_window", "known_manoeuvres", "per_leg"):
        raise ValueError(f"unknown CRB model {model}")
    if model == "known_manoeuvres":
        if spans and not target_manoeuvres:
            # Data with manoeuvres but no drawn plan (generator 0.4.0's single turn): the bound
            # would silently be the constant-velocity one (P0 panel round 2).
            raise ValueError("known_manoeuvres needs the scenario's target_manoeuvres plan")
        tvx = speed * np.sin(course)
        tvy = speed * np.cos(course)
        return crb_known_manoeuvres(
            t, ox, oy, tx, ty, tvx, tvy, valid, list(target_manoeuvres or []), rows, sigma
        )
    for k in rows:
        vx = speed[k] * math.sin(course[k])
        vy = speed[k] * math.cos(course[k])
        start = leg_start(spans or [], k) if model == "per_leg" else 0
        out.append(crb_at_row(t, ox, oy, tx, ty, vx, vy, valid, start, k, sigma))
    return out
