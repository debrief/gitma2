"""A manoeuvre prior that adapts to the period, and a hedged track with a spread (spec 018).

* **Rate grid**: the broadened prior's ranges for what a manoeuvre is, with the leg length
  (how often the target manoeuvres) at each of a few values. The system is not told which
  is true.
* **Rate posterior**: each rate's model evidence is the sum of the evidences of the
  candidate histories its search found (a lower limit on the true sum, the same for every
  rate), times its weight beforehand. The inferred rate is the one with the most; the
  declared history is declared under that rate's prior by the standing control's rule.
  This is empirical Bayes over one hyperparameter.
* **Hedged track**: the candidates of every rate are one mixture, each weighted by its
  rate's weight and its own evidence. The track is the mixture's mean state. Its spread in
  range is the mixture's: each candidate's own Laplace sd of range (from the curvature of
  its posterior) and the disagreement between candidates.

Classical; nothing trained; no truth is read.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np

from .arc import arc_states
from .prior import ManoeuvrePrior, open_precision, prior_residuals
from .retest import Problem, _jacobian, _pack, _resid, _steps, _unpack
from .search import History, _same


def rate_grid(
    base: ManoeuvrePrior, leg_means_s: list[float], sd_ratio: float
) -> dict[str, ManoeuvrePrior]:
    """``base`` with its leg length at each mean (sd in proportion), keyed ``rate<mean>``."""
    return {
        f"rate{m:g}": dataclasses.replace(base, leg_mean=float(m), leg_sd=float(sd_ratio * m))
        for m in leg_means_s
    }


def log_sum(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return -math.inf
    top = float(x.max())
    return top + math.log(float(np.exp(x - top).sum()))


def rate_posterior(
    evidences: dict[str, np.ndarray], log_weights: dict[str, float]
) -> dict[str, float]:
    """Probability of each rate: ∝ its weight × the sum of its candidates' evidences."""
    z = {k: log_sum(e) + float(log_weights[k]) for k, e in evidences.items()}
    top = max(z.values())
    if not math.isfinite(top):
        return {k: 1.0 / len(z) for k in z}
    w = {k: math.exp(v - top) if math.isfinite(v) else 0.0 for k, v in z.items()}
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def range_sd(pb: Problem, h: History, prior: Any) -> np.ndarray:
    """[R] Laplace sd (m) of the range at every row of the period for one history: the
    curvature of its posterior (bearings and prior, as the evidence uses) carried to the
    range by the arc model. NaN where the curvature is singular."""
    t, ox, oy, *_ = pb
    s, kinds = h.fit, h.kinds
    m = s.spans.shape[0]
    x = _pack(s.theta, s.spans)
    mask = np.ones(x.size, dtype=bool)
    mask[4 : 4 + 2 * m] = kinds.reshape(-1)
    idx = np.flatnonzero(mask)

    def f(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        return np.concatenate([_resid(pb, th, sp), prior_residuals(prior, th, sp, kinds)])

    jac = _jacobian(f, x, f(x), idx, m)
    range0 = float(np.hypot(s.theta[0] - ox[0], s.theta[1] - oy[0]))
    stand_in = open_precision(prior, s.theta, s.spans, kinds, range0, float(t[-1]))
    hess = jac.T @ jac + np.diag(stand_in[idx])

    def rng(y: np.ndarray) -> np.ndarray:
        th, sp = _unpack(y, m)
        st = arc_states(th, t, sp)
        out: np.ndarray = np.hypot(st[:, 0] - ox, st[:, 1] - oy)
        return out

    r0 = rng(x)
    steps = _steps(m)
    g = np.empty((r0.size, idx.size))
    for q, p in enumerate(idx):
        up = x.copy()
        up[p] += steps[p]
        g[:, q] = (rng(up) - r0) / steps[p]
    try:
        cov = np.linalg.inv(hess)
    except np.linalg.LinAlgError:
        return np.full(r0.size, np.nan)
    var = np.einsum("rp,pq,rq->r", g, cov, g)
    out: np.ndarray = np.sqrt(np.where(var >= 0.0, var, np.nan))
    return out


def mixture(
    sets: dict[str, list[History]], log_weights: dict[str, float], top: int
) -> list[tuple[History, str, float]]:
    """The candidates of every rate as one set, best first by weight × evidence, a history
    kept once (its heaviest version): (history, rate key, log weight + evidence)."""
    every = sorted(
        ((h, k, float(log_weights[k]) + h.evidence) for k, s in sets.items() for h in s),
        key=lambda x: -x[2],
    )
    kept: list[tuple[History, str, float]] = []
    for h, k, score in every:
        if not np.isfinite(score) or any(_same(h, q) for q, _k, _s in kept):
            continue
        kept.append((h, k, score))
        if len(kept) == top:
            break
    return kept


def hedged_spread(
    pb: Problem,
    cands: list[tuple[History, str, float]],
    priors: dict[str, ManoeuvrePrior],
    temperature: float,
    floor: float = 0.01,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(states [R, 4] the mixture's mean; [R] the mean of the candidates' ranges; [R] the
    mixture's sd of range, m; the weights). Candidates under ``floor`` of the weight are
    left out of the spread (and of the mean), the rest renormalised."""
    _t, ox, oy, *_ = pb
    score = np.array([c[2] for c in cands])
    w = np.exp((score - score.max()) / temperature)
    w = w / w.sum()
    use = w >= floor
    w = np.where(use, w, 0.0)
    w = w / w.sum()
    states = np.zeros_like(cands[0][0].fit.states, dtype=np.float64)
    mean = np.zeros(states.shape[0])
    second = np.zeros(states.shape[0])
    for wk, (h, key, _s) in zip(w, cands, strict=True):
        if wk <= 0.0:
            continue
        st = h.fit.states
        r = np.hypot(st[:, 0] - ox, st[:, 1] - oy)
        sd = range_sd(pb, h, priors[key])
        sd = np.where(np.isfinite(sd), sd, 0.0)
        states += wk * st
        mean += wk * r
        second += wk * (sd**2 + r**2)
    spread: np.ndarray = np.sqrt(np.maximum(second - mean**2, 0.0))
    return states, mean, spread, w
