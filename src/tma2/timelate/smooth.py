"""A fixed-interval smoother over the frozen EKF (spec 014 FR-017, research R8): the
conventional whole-period method, as a reference line. Named for what it is: a
constant-velocity filter with process noise, smoothed backwards (Rauch–Tung–Striebel); it has
no manoeuvre model.

The forward pass is the reference filter's own steps (``references.ekf``), started and
restarted as it is. Each stretch the filter runs without losing its state is smoothed on its
own; rows before a stretch's first state are given the smoothed first state run backwards at
constant velocity, up to the previous stretch.
"""

from __future__ import annotations

import numpy as np

from tma2.references.classical import BearingData
from tma2.references.ekf import (
    EKF_MIN_SIGMA_RAD,
    EKF_REINIT_EVERY,
    ekf_initialise,
    ekf_predict_step,
    ekf_update,
    plausible_state4,
)


def _f(tau: float) -> np.ndarray:
    f = np.eye(4)
    f[0, 2] = f[1, 3] = tau
    return f


def ekf_rts(
    d: BearingData, sigma_a: float, p0_scale: float = 1.0, r_scale: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """(states [n, 4] as x, y, vx, vy with NaN where no stretch covers a point; the filter's
    own states [n, 4], NaN where it has none). At a stretch's last point the two are equal."""
    n = d.n
    sigma = d.sigma
    r2 = max(sigma, EKF_MIN_SIGMA_RAD) ** 2 * r_scale
    smooth = np.full((n, 4), np.nan)
    filt = np.full((n, 4), np.nan)
    stretches: list[list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]] = []
    cur: list[tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    first = d.zig_index + 1
    have, t_prev = False, 0.0
    x, p = np.zeros(4), np.zeros((4, 4))
    if first - 1 < n:
        have, t_prev, x, p = ekf_initialise(
            d.t, d.ox, d.oy, d.z, d.valid, first - 1, sigma, p0_scale
        )
        if have:
            cur = [(first - 1, x.copy(), p.copy(), x.copy(), p.copy())]
    last_try = first - 1
    for i in range(first, n):
        if have:
            xp, pp = ekf_predict_step(t_prev, x, p, float(d.t[i]), sigma_a)
            t_prev = float(d.t[i])
            x, p = xp, pp
            if d.valid[i] == 1:
                x, p = ekf_update(x, p, float(d.z[i]), float(d.ox[i]), float(d.oy[i]), r2)
            if plausible_state4(float(d.ox[i]), float(d.oy[i]), x):
                cur.append((i, xp.copy(), pp.copy(), x.copy(), p.copy()))
                continue
            have = False
            last_try = i - EKF_REINIT_EVERY
            if cur:
                stretches.append(cur)
            cur = []
        if i - last_try >= EKF_REINIT_EVERY:
            have, t_prev, x, p = ekf_initialise(d.t, d.ox, d.oy, d.z, d.valid, i, sigma, p0_scale)
            last_try = i
            if have:
                cur = [(i, x.copy(), p.copy(), x.copy(), p.copy())]
    if cur:
        stretches.append(cur)
    covered = 0
    for st in stretches:
        xs = st[-1][3].copy()
        smooth[st[-1][0]] = xs
        filt[st[-1][0]] = st[-1][3]
        for k in range(len(st) - 2, -1, -1):
            i, _xp, _pp, xf, pf = st[k]
            j, xp1, pp1, _xf1, _pf1 = st[k + 1]
            f = _f(float(d.t[j] - d.t[i]))
            try:
                c = pf @ f.T @ np.linalg.inv(pp1)
            except np.linalg.LinAlgError:
                c = np.zeros((4, 4))
            xs = xf + c @ (xs - xp1)
            smooth[i] = xs
            filt[i] = xf
        i0 = st[0][0]
        for i in range(covered, i0):  # before the stretch: its first state run backwards
            tau = float(d.t[i] - d.t[i0])
            smooth[i] = [xs[0] + xs[2] * tau, xs[1] + xs[3] * tau, xs[2], xs[3]]
        covered = st[-1][0] + 1
    return smooth, filt


def rows_from_points(states: np.ndarray, point_rows: int, n_rows: int) -> np.ndarray:
    """A track at 10-second points as a track at the period's 5-second rows (each point held
    for its rows, as Gate T reads the filters)."""
    out = np.full((n_rows, 4), np.nan)
    for k in range(states.shape[0]):
        out[k * point_rows : (k + 1) * point_rows] = states[k]
    return out
