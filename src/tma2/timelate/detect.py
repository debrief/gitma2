"""How detectable each true manoeuvre is, and references told only the detectable ones
(spec 017, research R1 and R2).

The **detectability** of a true manoeuvre is the rise in the bearings' cost (χ², the stated
sd) when the true history is refitted without it, every other manoeuvre's times held. It
uses nothing but the bearings and the true structure: no prior, no evidence approximation,
no search. A manoeuvre whose omission costs less than the evidence needs to declare one
cannot be found by a system that weighs fit against complexity, whatever its search.

The **detectable-only reference** at a threshold is the true history without the
manoeuvres below it, fitted with its times held and the prior, exactly as the full
reference with times held is. These read the truth; they are readings, never systems.
"""

from __future__ import annotations

import numpy as np

from .arc import fit_arc_search
from .prior import ManoeuvrePrior
from .retest import Problem, Structure, joint_fit
from .run import nominal_starts


def held_fit(pb: Problem, spans: np.ndarray, kinds: np.ndarray) -> tuple[np.ndarray, float]:
    """(θ, cost) of the bearings-only fit of a history with its times held, from the nominal
    starts (the lowest cost kept), as ``run.history_reference`` fits its first track."""
    t, ox, oy, z, v, sigma = pb
    m = spans.shape[0]
    best = None
    for q0 in nominal_starts(pb):
        th0 = np.concatenate([q0, np.zeros(2 * m)])
        for i in range(m):
            th0[4 + 2 * i] = 0.5 if kinds[i, 0] else 0.0
            th0[5 + 2 * i] = 1.0 if (kinds[i, 1] and not kinds[i, 0]) else 0.0
        f, _n = fit_arc_search(t, ox, oy, z, v, sigma, spans, th0, kinds if m else None)
        if best is None or f.cost < best.cost:
            best = f
    assert best is not None
    return best.theta, float(best.cost)


def detectability(pb: Problem, spans: np.ndarray, kinds: np.ndarray) -> tuple[np.ndarray, float]:
    """([M] the cost each manoeuvre's omission adds, the full history's cost). An omission
    that fits better than the full history (a fit that found a lower minimum) reads 0."""
    _theta, full = held_fit(pb, spans, kinds)
    m = spans.shape[0]
    out = np.zeros(m)
    for i in range(m):
        keep = np.arange(m) != i
        _th, cost = held_fit(pb, spans[keep], kinds[keep])
        out[i] = max(cost - full, 0.0)
    return out, full


def detectable_reference(
    pb: Problem,
    spans: np.ndarray,
    kinds: np.ndarray,
    det: np.ndarray,
    threshold: float,
    prior: ManoeuvrePrior,
) -> Structure:
    """The fit told only the manoeuvres whose detectability is at least ``threshold``: times
    held, fitted to the posterior. ``threshold`` 0 is the full reference with times held."""
    keep = det >= threshold
    sp, kd = spans[keep], kinds[keep]
    theta, _cost = held_fit(pb, sp, kd)
    return joint_fit(pb, theta, sp, free_changes=kd, free_times=False, prior=prior)
