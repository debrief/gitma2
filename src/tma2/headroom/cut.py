"""Spec 039 part 3 (research R6): the time-late control cut at a scored row.

``ctl-d1-q0.01`` (spec 016; ``timelate.carry.solve_ctl``, started from nothing: wild bearings
edited, an effective sd, the evidence search under Annex B's manoeuvre prior and a broadened
one, a declared history) is run on the bearings up to row k and read at its last moment. A
causal estimator told the generator's manoeuvre statistics; it reads no truth. The time-late
code is used as registered, unchanged.
"""

from __future__ import annotations

import math
from functools import cache
from typing import Any

import numpy as np

from tma2.references.classical import BearingData


@cache
def _settings() -> tuple[dict[str, Any], dict[str, Any]]:
    from tma2.long.timelate import settings_and_priors

    settings, priors, *_ = settings_and_priors()
    return settings, priors


def cut_state(d: BearingData, k: int) -> tuple[np.ndarray, tuple[float, float, float], int] | None:
    """(state x, y, vx, vy at row k; (range, course, speed); manoeuvres declared), or None when
    the searches give no candidate."""
    from tma2.timelate.carry import solve_ctl

    settings, priors = _settings()
    n = k + 1
    x0, y0 = float(d.ox[0]), float(d.oy[0])
    pb = (
        d.t[:n] - d.t[0],
        d.ox[:n] - x0,
        d.oy[:n] - y0,
        d.z[:n],
        np.asarray(d.valid[:n]) > 0,
        float(d.sigma),
    )
    res = solve_ctl(pb, priors, np.full((n, 4), np.nan), np.zeros((0, 2)), settings)
    if res is None:
        return None
    st, spans = res
    x, y, vx, vy = (float(v) for v in st[-1])
    if not all(math.isfinite(v) for v in (x, y, vx, vy)):
        return None
    state = np.array([x + x0, y + y0, vx, vy])
    rng = math.hypot(state[0] - float(d.ox[k]), state[1] - float(d.oy[k]))
    course = math.atan2(vx, vy) % (2.0 * math.pi)
    return state, (rng, course, math.hypot(vx, vy)), int(np.asarray(spans).shape[0])
