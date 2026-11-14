"""Read-outs of the learned whole-period model (spec 016 research R8). No truth is read here.

Two tracks per model. ``learned``: the model's direct output (``direct_track``), at every
5-second row of the period, in the convention of every other time-late system (absolute x, y
in the engagement's frame, vx, vy; what ``score.row_errors`` reads). ``learned-arc``: the arc
model fitted to the bearings with the manoeuvre prior, started from that track, with manoeuvre
spans from runs of the model's manoeuvre probability (``spans_from_logit``, ``arc_readout``):
no search over histories.

The model states range and velocity, not position. The direct track's position is the stated
range along the measured bearing (as spec 012's ``frame.to_state``), with the bearing smoothed
by a short running median: the model has no other statement of direction, a single bearing
carries its full error across the range (1° at 10 km is 175 m), and a median of 35 s does not
bias a steadily changing bearing and ignores a wild one. Range, course and speed, which the
registered comparison reads, do not depend on that choice.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.regress.frame import L_UNIT, V_UNIT, first_bearing

from .controls import c2_refit
from .periods import Period
from .retest import MIN_DURATION, Problem, Structure

SMOOTH_ROWS = 7  # rows of the bearing's running median (35 s at 5 s)


def token_rows(rows: int, patch: int) -> tuple[np.ndarray, np.ndarray]:
    """(first row [T], last existing row [T]) of the tokens of a period of ``rows`` rows."""
    start = np.arange(0, rows, patch)
    return start, np.minimum(start + patch - 1, rows - 1)


def token_times(rows: int, dt: float, patch: int) -> np.ndarray:
    """[T, 2] the time span a token's manoeuvre label speaks for, from the period's start: from
    the row before its first row (a manoeuvre's span starts one row before its first row
    inside, as the runners' true spans do) to its last existing row."""
    start, last = token_rows(rows, patch)
    out: np.ndarray = np.stack([np.maximum(start - 1, 0) * dt, last * dt], axis=1)
    return out


def smoothed_bearing(z: np.ndarray, valid: np.ndarray, width: int = SMOOTH_ROWS) -> np.ndarray:
    """[R] the bearing at every row: valid bearings unwrapped, interpolated over the rows
    without one, then a centred running median of ``width`` rows (the ends repeat)."""
    k = np.flatnonzero(valid)
    if k.size == 0:
        return np.full(z.shape, np.nan)
    zi = np.interp(np.arange(z.shape[0]), k, np.unwrap(z[k].astype(np.float64)))
    h = width // 2
    win = np.lib.stride_tricks.sliding_window_view(np.pad(zi, h, mode="edge"), 2 * h + 1)
    out: np.ndarray = np.median(win, axis=1)
    return out


def direct_track(mean: np.ndarray, period: Period, patch: int) -> np.ndarray:
    """The model's own track [rows, 4] (x, y, vx, vy). ``mean`` [T, 3]: the model's output for
    the period's tokens (ln(range ÷ 10 km), velocity ÷ 10 m/s in the frame rotated to the
    period's first valid bearing), each stated at its token's last existing row. Between those
    rows the three are interpolated linearly in time; before the first, ln range continues the
    first interval's slope and the velocity is held. All NaN for a period with no bearing."""
    a, b = period.first, period.first + period.rows
    z, valid = period.obs[a:b, 1].astype(np.float64), period.obs[a:b, 2] != 0
    ox, oy = period.own[a:b, 1].astype(np.float64), period.own[a:b, 2].astype(np.float64)
    _start, last = token_rows(period.rows, patch)
    m = np.asarray(mean, dtype=np.float64)[: last.shape[0]]
    if not valid.any() or m.shape[0] != last.shape[0]:
        return np.full((period.rows, 4), np.nan)
    k = np.arange(period.rows, dtype=np.float64)
    ln_r, vxp, vyp = (np.interp(k, last, m[:, c]) for c in range(3))
    if last.shape[0] > 1 and last[0] > 0:
        slope = (m[1, 0] - m[0, 0]) / (last[1] - last[0])
        head = k < last[0]
        ln_r[head] = m[0, 0] + slope * (k[head] - last[0])
    th = float(first_bearing(z[None, :], valid[None, :])[0])
    c, s = np.cos(th), np.sin(th)
    rng = L_UNIT * np.exp(ln_r)
    zs = smoothed_bearing(z, valid)
    out: np.ndarray = np.stack(
        [
            ox + rng * np.sin(zs),
            oy + rng * np.cos(zs),
            V_UNIT * (vxp * c + vyp * s),
            V_UNIT * (vyp * c - vxp * s),
        ],
        axis=1,
    )
    return out


def spans_from_logit(
    prob: np.ndarray,
    t_tokens: np.ndarray,
    threshold: float = 0.5,
    merge_s: float = 60.0,
    max_manoeuvres: int = 10,
) -> np.ndarray:
    """Manoeuvre spans [M, 2] (start s, end s, ascending, disjoint) from the model's manoeuvre
    probability per token ``prob`` [T] and the tokens' time spans ``t_tokens`` [T, 2]
    (``token_times``): every run of tokens above ``threshold``, runs closer than ``merge_s``
    merged; with more than ``max_manoeuvres`` the runs with the most probability above the
    threshold are kept. A span shorter than the arc fit's shortest manoeuvre is extended
    backwards to it (not past the previous span or the period's start)."""
    on = np.asarray(prob) > threshold
    runs: list[list[float]] = []  # start, end, probability above the threshold
    for j in np.flatnonzero(on):
        a, b = float(t_tokens[j, 0]), float(t_tokens[j, 1])
        w = float(prob[j]) - threshold
        if runs and a - runs[-1][1] <= merge_s:
            runs[-1][1] = b
            runs[-1][2] += w
        else:
            runs.append([a, b, w])
    if len(runs) > max_manoeuvres:
        keep = sorted(sorted(range(len(runs)), key=lambda i: -runs[i][2])[:max_manoeuvres])
        runs = [runs[i] for i in keep]
    out = np.array([r[:2] for r in runs], dtype=np.float64).reshape(-1, 2)
    for i in range(out.shape[0]):
        floor = out[i - 1, 1] if i else 0.0
        if out[i, 1] - out[i, 0] < MIN_DURATION:
            out[i, 0] = max(out[i, 1] - MIN_DURATION, floor)
    return out[out[:, 1] - out[:, 0] >= MIN_DURATION]


def arc_readout(
    pb: Problem,
    states: np.ndarray,
    spans: np.ndarray,
    prior: Any,
    starts: tuple[np.ndarray, ...] = (),
) -> tuple[Structure, np.ndarray, dict[str, float]]:
    """``learned-arc``: (fit, kinds, evidence by part) of the arc model with ``prior`` on the
    period's bearings ``pb``, for manoeuvres at ``spans`` (``spans_from_logit``), started from
    the model's track ``states`` (``direct_track``). This is spec 014's refit control
    (``controls.c2_refit``) given the model's spans and track in place of C″'s: kinds by
    evidence, every time free, no manoeuvre added, removed or moved elsewhere. ``starts``:
    further starting states that use no truth (the runner's nominal starts), none by default.
    Raises ``ValueError`` when no start gives a finite evidence (the runner then keeps the
    direct track)."""
    if not np.isfinite(states).all() and not starts:
        raise ValueError("the model's track has no state to start from")
    return c2_refit(pb, spans, states, prior, list(starts))
