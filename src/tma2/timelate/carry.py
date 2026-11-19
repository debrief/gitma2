"""Carrying state across a gap (spec 026).

``ctl`` (spec 016's combined control declared at margin 1 with quiet probability 0.01, as
``run4`` computes it) searches over manoeuvre histories from two starts: C″'s answer and a
start from nothing (the best of four nominal states). The carry replaces the start from
nothing with the carried state: the previous period's declared state at its last row, run
forward at constant velocity to this period's first row (spec 024's design for windows, where
C″'s start is kept). Everything else is ``ctl``'s: the edited, correlation-widened bearings,
the searches under Annex B's and the broadened prior, pooled, and the declaration.

``solve_ctl(..., carried=None)`` is ``ctl`` itself, line for line (tested against ``run4``'s
``ctl-d1-q0.01``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .arc import fit_arc, solve_arc
from .corr import MIN_SHARE, edited, effective, estimate
from .hedge import declared, elimination_path, pool
from .retest import Problem
from .run import nominal_starts
from .search import History, candidate_set, evidence_search

MARGIN, QUIET = 1.0, 0.01


@dataclass
class Carried:
    """A declared state handed on: [x, y, vx, vy] (engagement frame) at absolute time ``t_s``."""

    t_s: float
    state: np.ndarray


def carried_theta(c: Carried, t0_s: float) -> np.ndarray:
    """The arc model's θ (no manoeuvre) at absolute time ``t0_s``: the carried state run forward
    at constant velocity."""
    x, y, vx, vy = (float(u) for u in c.state)
    dt = t0_s - c.t_s
    return np.array([x + vx * dt, y + vy * dt, np.arctan2(vx, vy), np.hypot(vx, vy)])


def _search(
    pb: Problem,
    prior: Any,
    c_states: np.ndarray,
    spc: np.ndarray,
    settings: dict[str, Any],
    theta_carry: np.ndarray | None,
) -> list[tuple[History, float]]:
    """``run2._search`` with its start from nothing replaced by ``theta_carry`` when given."""
    t, ox, oy, z, v, sigma = pb
    steps, most = int(settings["steps"]), int(settings["max_manoeuvres"])
    seen: list[History] = []
    if np.isfinite(c_states).all():
        f0, _, _ = solve_arc(t, ox, oy, z, v, sigma, spc, c_states)
        seen += evidence_search(pb, f0.theta, spc, prior, most, steps)[1]
    none = np.zeros((0, 2))
    if theta_carry is None:
        b0 = None
        for q0 in nominal_starts(pb):
            f = fit_arc(t, ox, oy, z, v, sigma, none, q0)
            if b0 is None or f.cost < b0.cost:
                b0 = f
        assert b0 is not None
        start = b0.theta
    else:
        start = fit_arc(t, ox, oy, z, v, sigma, none, theta_carry).theta
    seen += evidence_search(pb, start, none, prior, most, steps)[1]
    return candidate_set(seen, top=int(settings["candidates"]))


def solve_ctl(
    pb: Problem,
    priors: dict[str, Any],
    c_states: np.ndarray,
    spc: np.ndarray,
    settings: dict[str, Any],
    carried: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    """``ctl-d1-q0.01`` on ``pb`` (``carried``: θ of the carried start, or None for ``ctl``).
    Returns the declared track [rows, 4] (the period's frame of ``pb``) and its spans, or None
    when the searches give no candidate."""
    pe, n_edit = edited(pb)
    share_e, tau_e = estimate(pe)
    px = effective(pe, share_e, tau_e) if share_e >= MIN_SHARE else pe
    which = "ctl" if share_e >= MIN_SHARE else ("edit" if n_edit else "plain")
    top = int(settings["candidates"])
    s = {**settings, "candidates": top}
    sets = [
        [(h, f"{which}/{key}") for h, _p in _search(px, priors[key], c_states, spc, s, carried)]
        for key in ("v3", "broad")
    ]
    cands = pool(sets, top)
    if not cands:
        return None
    h0, tag0 = cands[0]
    path = elimination_path(px, h0, priors[tag0.split("/")[1]])
    h = path[declared(path, MARGIN, QUIET)]
    return h.fit.states, h.fit.spans
