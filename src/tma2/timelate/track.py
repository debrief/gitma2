"""A track from the physics layer's solution (spec 013 research R3).

The layer's model is p(t) = p0 + u0·t + Σ c_m d_m (t − t_m)⁺ and u(t) = u0 + Σ c_m d_m [t_m ≤ t]
(``physics/reference.py``). Given a solve's ``theta``, knot rows and knot weights, ``track``
evaluates it at any times.
"""

from __future__ import annotations

import numpy as np


def track(
    theta: np.ndarray, t_knots: np.ndarray, weights: np.ndarray, times: np.ndarray
) -> np.ndarray:
    """[N, 4] (x, y, vx, vy) at ``times`` (the layer's time axis)."""
    p0, u0 = theta[0:2], theta[2:4]
    d = theta[4:].reshape(-1, 2)[: t_knots.shape[0]]
    c = weights.astype(np.float64)
    lag = np.maximum(times[:, None] - t_knots[None, :], 0.0) * c[None, :]
    on = (t_knots[None, :] <= times[:, None]) * c[None, :]
    pos = p0[None, :] + u0[None, :] * times[:, None] + lag @ d
    vel = u0[None, :] + on @ d
    out: np.ndarray = np.concatenate([pos, vel], axis=1)
    return out
