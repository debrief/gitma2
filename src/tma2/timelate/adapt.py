"""A manoeuvre prior that adapts to the period, and a hedged track with a spread (spec 018).

* **A family of priors**: the broadened prior with its leg length (how often the target
  manoeuvres), the leg length's spread and the largest turn each at a few values. The
  system is not told which is true.
* **Model evidence of a member**: the sum of the evidences, under that member, of one
  shared set of candidate histories (found by searches under the busiest and the quietest
  member, each history refitted under the member). A lower limit on the true sum, over
  the same histories for every member.
* **Choosing the member**: per period (empirical Bayes on one period), or by the summed
  log evidence of a group of periods taken to share their statistics (``pooled_choice``).
  The declared history is declared under the chosen member's prior by the standing
  control's rule.
* **Hedged track**: the candidates of every member are one mixture, each weighted by its
  member's weight and its own evidence (with the declaration's quiet probability). The
  track is the mixture's mean state. Its spread in range is the mixture's: each candidate's
  own Laplace sd of range (from the curvature of its posterior) and the disagreement
  between candidates.

Classical; nothing trained; no truth is read.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np

from .arc import arc_states
from .hedge import with_quiet
from .prior import ManoeuvrePrior, open_precision, prior_residuals
from .retest import Problem, _jacobian, _pack, _resid, _steps, _unpack
from .search import History, _same, _score


def rate_grid(
    base: ManoeuvrePrior, leg_means_s: list[float], sd_ratio: float
) -> dict[str, ManoeuvrePrior]:
    """``base`` with its leg length at each mean (sd in proportion), keyed ``rate<mean>``."""
    return {
        f"rate{m:g}": dataclasses.replace(base, leg_mean=float(m), leg_sd=float(sd_ratio * m))
        for m in leg_means_s
    }


def family(
    base: ManoeuvrePrior,
    leg_means_s: list[float],
    sd_ratios: list[float],
    angle_max_deg: list[float],
) -> dict[str, ManoeuvrePrior]:
    """Every combination of leg mean, leg sd (as a ratio of the mean) and largest turn,
    the rest of ``base`` kept: keyed ``L<mean>-s<ratio>-a<degrees>``."""
    out: dict[str, ManoeuvrePrior] = {}
    for m in leg_means_s:
        for r in sd_ratios:
            for a in angle_max_deg:
                out[f"L{m:g}-s{r:g}-a{a:g}"] = dataclasses.replace(
                    base,
                    leg_mean=float(m),
                    leg_sd=float(r * m),
                    angle=(base.angle[0], math.radians(float(a))),
                )
    return out


def rescore(pb: Problem, histories: list[History], prior: Any) -> list[History]:
    """Each history refitted and scored under ``prior``, best first (a history the prior
    does not allow has no evidence and is dropped)."""
    out = [_score(pb, h.fit.theta, h.fit.spans, h.kinds, prior) for h in histories]
    return sorted((h for h in out if np.isfinite(h.evidence)), key=lambda x: -x.evidence)


def union(sets: list[list[History]]) -> list[History]:
    """Distinct histories of several candidate sets (the first seen kept)."""
    kept: list[History] = []
    for s in sets:
        for h in s:
            if not any(_same(h, k) for k in kept):
                kept.append(h)
    return kept


def pooled_choice(log_z: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """[P] the member each period uses when the periods of a group share one prior: the
    member with the largest sum of log model evidence over the group. ``log_z`` is [P, K];
    non-finite entries count as a large penalty."""
    z = np.where(np.isfinite(log_z), log_z, -1e6)
    out = np.zeros(z.shape[0], dtype=np.int64)
    for g in np.unique(groups):
        m = groups == g
        out[m] = int(np.argmax(z[m].sum(axis=0)))
    return out


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
    sets: dict[str, list[History]], log_weights: dict[str, float], top: int, quiet: float = 0.0
) -> list[tuple[History, str, float]]:
    """The candidates of every member as one set, best first by weight × evidence, a history
    kept once (its heaviest version): (history, member key, log weight + evidence). With
    ``quiet``, the evidence is the one the declaration uses: the target never manoeuvres
    with that probability."""
    every = sorted(
        ((h, k, float(log_weights[k]) + with_quiet(h, quiet)) for k, s in sets.items() for h in s),
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
