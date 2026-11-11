"""Inputs and targets in the canonical frame (spec 012 research R1).

The frame is rotated so that the scenario's first valid bearing points north; the problem is
invariant to rotation and to translation (only ownship displacements are read). Per row:

    sin β′, cos β′, Δx′, Δy′ (ownship displacement since the previous row, ÷ 100 m),
    valid, ln(σ / 1°), Δt ÷ 10 s

with the bearing features zero on invalid rows. Targets per row: ln(range ÷ 10 km) and the
target's velocity in the frame ÷ 10 m/s. ``to_state`` maps a prediction back to the absolute
state [x, y, vx, vy] at that row using the row's own bearing.
"""

from __future__ import annotations

import math

import numpy as np

N_FEATURES = 7
N_TARGETS = 3
L_UNIT = 1.0e4  # m
V_UNIT = 10.0  # m/s
D_UNIT = 100.0  # m
DEG = math.pi / 180.0


def first_bearing(bearing: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """[B] the first valid bearing of each scenario (0 where there is none)."""
    has = valid.any(axis=1)
    j = valid.argmax(axis=1)
    return np.where(has, bearing[np.arange(bearing.shape[0]), j], 0.0).astype(np.float64)


def features(
    t: np.ndarray,
    own_xy: np.ndarray,
    bearing: np.ndarray,
    valid: np.ndarray,
    mask: np.ndarray,
    sigma: np.ndarray,
    ownship_only: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """([B, R, 7] float32 features, [B] frame rotation θ₀). ``mask``: rows that exist."""
    th = first_bearing(bearing, valid & mask)
    c, s = np.cos(th)[:, None], np.sin(th)[:, None]
    x = own_xy[..., 0].astype(np.float64)
    y = own_xy[..., 1].astype(np.float64)
    dx = np.diff(x, axis=1, prepend=x[:, :1])
    dy = np.diff(y, axis=1, prepend=y[:, :1])
    dt = np.diff(t.astype(np.float64), axis=1, prepend=t[:, :1].astype(np.float64))
    ok = (valid & mask).astype(np.float64)
    b = bearing.astype(np.float64) - th[:, None]
    f = np.zeros((*bearing.shape, N_FEATURES), dtype=np.float32)
    if not ownship_only:
        f[..., 0] = np.sin(b) * ok
        f[..., 1] = np.cos(b) * ok
        f[..., 4] = ok
    m = mask.astype(np.float64)
    f[..., 2] = (dx * c - dy * s) / D_UNIT * m
    f[..., 3] = (dy * c + dx * s) / D_UNIT * m
    f[..., 5] = np.log(np.maximum(sigma.astype(np.float64), 1e-6) / DEG)[:, None] * m
    f[..., 6] = dt / 10.0 * m
    return f, th


def targets(own_xy: np.ndarray, tgt: np.ndarray, th: np.ndarray) -> np.ndarray:
    """[B, R, 3] float32: ln(range ÷ 10 km), v′x ÷ 10, v′y ÷ 10. ``tgt``: x, y, course, speed."""
    dx = tgt[..., 0].astype(np.float64) - own_xy[..., 0]
    dy = tgt[..., 1].astype(np.float64) - own_xy[..., 1]
    rng = np.sqrt(dx * dx + dy * dy)
    crs = tgt[..., 2].astype(np.float64) - th[:, None]
    spd = tgt[..., 3].astype(np.float64)
    out = np.zeros((*rng.shape, N_TARGETS), dtype=np.float32)
    out[..., 0] = np.log(np.maximum(rng, 1.0) / L_UNIT)
    out[..., 1] = spd * np.sin(crs) / V_UNIT
    out[..., 2] = spd * np.cos(crs) / V_UNIT
    return out


def to_state(
    pred: np.ndarray, th: float, bearing_k: float, own_k: tuple[float, float]
) -> tuple[np.ndarray, tuple[float, float, float]]:
    """A prediction [3] at a row → (state [x, y, vx, vy], (range, course, speed)), using the
    row's measured bearing for the direction of the target."""
    rng = L_UNIT * math.exp(float(pred[0]))
    vxp, vyp = V_UNIT * float(pred[1]), V_UNIT * float(pred[2])
    c, s = math.cos(th), math.sin(th)
    vx = vxp * c + vyp * s
    vy = vyp * c - vxp * s
    x = own_k[0] + rng * math.sin(bearing_k)
    y = own_k[1] + rng * math.cos(bearing_k)
    course = math.atan2(vx, vy) % (2.0 * math.pi)
    return np.array([x, y, vx, vy]), (rng, course, math.hypot(vx, vy))
