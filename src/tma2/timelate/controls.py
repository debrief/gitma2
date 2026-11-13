"""The control that separates the search from its model and prior (spec 014 FR-003, research
R3): C″'s own transitions refitted over the whole period with the arc model and the manoeuvre
prior. Kinds are chosen by evidence and every time is free, but no manoeuvre is added, removed
or moved to another place: what the arc model, the prior and the whole period give without a
search over histories."""

from __future__ import annotations

from typing import Any

import numpy as np

from .arc import fit_arc_search, solve_arc
from .retest import MAX_DURATION, MIN_DURATION, Problem, Structure, choose_kinds, joint_fit


def c2_refit(
    pb: Problem,
    spans: np.ndarray,
    c_states: np.ndarray,
    prior: Any,
    starts: list[np.ndarray],
) -> tuple[Structure, np.ndarray, dict[str, float]]:
    """(fit, kinds, evidence by part) of C″'s transitions ``spans`` [M, 2], started from C″'s
    own track (when it has one) and from ``starts`` (states that use no truth); the start with
    the most evidence is kept."""
    t, ox, oy, z, v, sigma = pb
    m = spans.shape[0]
    sp = spans.astype(np.float64).copy()
    if m:
        sp[:, 1] = sp[:, 0] + np.clip(sp[:, 1] - sp[:, 0], MIN_DURATION, MAX_DURATION)
    turns = np.zeros((m, 2), dtype=bool)
    turns[:, 0] = True
    thetas: list[np.ndarray] = []
    if np.isfinite(c_states).all():
        f0, _, _ = solve_arc(t, ox, oy, z, v, sigma, sp, c_states)
        thetas.append(f0.theta)
    best_cold = None
    for q0 in starts:
        th0 = np.concatenate([q0, np.zeros(2 * m)])
        th0[4::2] = 0.5
        f, _n = fit_arc_search(t, ox, oy, z, v, sigma, sp, th0, turns if m else None)
        if best_cold is None or f.cost < best_cold.cost:
            best_cold = f
    if best_cold is not None:
        thetas.append(best_cold.theta)
    out: tuple[Structure, np.ndarray, dict[str, float]] | None = None
    for th in thetas:
        th = th.copy()
        th[5::2] = 0.0
        s = joint_fit(pb, th, sp, free_changes=turns, prior=prior)
        g, kinds, ev = choose_kinds(pb, s, prior)
        if np.isfinite(ev["total"]) and (out is None or ev["total"] > out[2]["total"]):
            out = (g, kinds, ev)
    if out is None:
        raise ValueError("no start gave a finite evidence")
    return out
