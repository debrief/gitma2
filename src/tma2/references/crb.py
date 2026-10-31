"""Fisher information and Cramér–Rao bounds for bearings-only constant-velocity estimation.

For θ = (x0, y0, vx, vy) at a reference time with independent bearing noise σ, the Fisher
information from valid bearings i ≤ k at the true trajectory is I = Σ gᵢgᵢᵀ / σ², with gᵢ the
bearing's gradient (dy/ρ², −dx/ρ², t·dy/ρ², −t·dx/ρ²). Bounds on range, course and speed at row k
follow by the delta method: var(f) ≥ ∇fᵀ I⁻¹ ∇f.

Two variants (research R4): *full window* uses all bearings up to k with the CV model anchored at
window start (right for a constant-velocity target); *per leg* uses only bearings since the last
completed manoeuvre, anchored at that row (the bound for an estimator that knows the manoeuvre
times: the oracle's regime). Before the zig the information is singular.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

SINGULAR_COND = 1e12
MIN_SIGMA_RAD = 1e-4


@dataclass
class CrbRow:
    sd_range_rel: float
    sd_course_deg: float
    sd_speed_kt: float
    singular: bool


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
    try:
        cond = np.linalg.cond(info)
    except np.linalg.LinAlgError:
        cond = math.inf
    if not math.isfinite(cond) or cond > SINGULAR_COND:
        return CrbRow(math.nan, math.nan, math.nan, True)
    cov = np.linalg.inv(info)
    tau = float(t[k]) - t_ref
    dx = tx[k] - ox[k]
    dy = ty[k] - oy[k]
    rng = math.hypot(dx, dy)
    # range r = ||(x0 + vx τ − ox, y0 + vy τ − oy)||
    g_r = np.array([dx / rng, dy / rng, tau * dx / rng, tau * dy / rng])
    speed = math.hypot(tvx, tvy)
    # course c = atan2(vx, vy): ∂c/∂vx = vy/s², ∂c/∂vy = −vx/s²
    g_c = np.array([0.0, 0.0, tvy / (speed * speed), -tvx / (speed * speed)])
    g_s = np.array([0.0, 0.0, tvx / speed, tvy / speed])
    var_r = float(g_r @ cov @ g_r)
    var_c = float(g_c @ cov @ g_c)
    var_s = float(g_s @ cov @ g_s)
    if min(var_r, var_c, var_s) < 0:
        return CrbRow(math.nan, math.nan, math.nan, True)
    return CrbRow(
        sd_range_rel=math.sqrt(var_r) / rng,
        sd_course_deg=math.degrees(math.sqrt(var_c)),
        sd_speed_kt=math.sqrt(var_s) / (1852.0 / 3600.0),
        singular=False,
    )


def leg_start(spans: list[dict[str, int]], k: int) -> int:
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
    spans: list[dict[str, int]] | None,
    rows: list[int],
    per_leg: bool,
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
    for k in rows:
        start = leg_start(spans or [], k) if per_leg else 0
        vx = speed[k] * math.sin(course[k])
        vy = speed[k] * math.cos(course[k])
        out.append(crb_at_row(t, ox, oy, tx, ty, vx, vy, valid, start, k, sigma))
    return out
