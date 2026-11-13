"""Controls that need no new evidence (spec 016, research R1, R2 and R5): a hedged track, a
cautious declaration, and pooling of searches run under different priors.

* **Hedged track**: the mean of the candidates' tracks in Cartesian state, weighted by their
  evidence at a temperature. It is the posterior-mean track under the search's own
  posterior, which is what an error-minimising learned model approximates; the control for
  hedging.
* **Declaration**: from the first candidate, manoeuvres are removed one at a time (always the
  one whose removal costs least evidence, each removal refitted) down to none: the
  *elimination path*. A history is declared at the first point on the path where every
  remaining manoeuvre is worth more than a margin. A stated probability ``q`` that the
  target never manoeuvres changes only the weight of the path's last step.
* **Pooling**: candidates of searches under two priors, each prior equally likely beforehand,
  are one candidate set; the difference of their best evidences is the Bayes factor between
  the priors (the prior-mismatch diagnostic).

Nothing is trained and no truth is read.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .retest import Problem
from .search import History, _removals, _same


def weights(evidence: np.ndarray, temperature: float) -> np.ndarray:
    """Probabilities ∝ exp(evidence / temperature) (non-finite evidence gets none)."""
    e = np.asarray(evidence, dtype=np.float64)
    ok = np.isfinite(e)
    w = np.zeros(e.size)
    if ok.any():
        w[ok] = np.exp((e[ok] - e[ok].max()) / temperature)
        w /= w.sum()
    return w


def hedged(tracks: list[np.ndarray], evidence: np.ndarray, temperature: float) -> np.ndarray:
    """[R, 4] the weighted mean of the candidates' states (x, y, vx, vy)."""
    w = weights(evidence, temperature)
    out = np.zeros_like(tracks[0], dtype=np.float64)
    for wk, tr in zip(w, tracks, strict=True):
        if wk > 0.0:
            out += wk * tr
    return out


def pool(sets: list[list[tuple[History, str]]], top: int) -> list[tuple[History, str]]:
    """Candidates of several searches as one set, best first, a history kept once (the
    version with more evidence)."""
    every = sorted((x for s in sets for x in s), key=lambda x: -x[0].evidence)
    kept: list[tuple[History, str]] = []
    for h, tag in every:
        if not np.isfinite(h.evidence) or any(_same(h, k) for k, _ in kept):
            continue
        kept.append((h, tag))
        if len(kept) == top:
            break
    return kept


def with_quiet(h: History, q: float) -> float:
    """``h``'s evidence when the target never manoeuvres with probability ``q`` and otherwise
    follows the prior ``h`` was scored under (``prior`` kind "mix" with ``QUIET`` = q)."""
    if q <= 0.0:
        return h.evidence
    if h.fit.spans.shape[0]:
        return h.evidence + math.log(1.0 - q)
    legs = float(h.parts["legs"])
    return h.evidence - legs + math.log(q + (1.0 - q) * math.exp(legs))


def elimination_path(pb: Problem, top: History, prior: Any) -> list[History]:
    """``top`` and then, repeatedly, the best history with one manoeuvre fewer (each refitted
    and scored), down to no manoeuvre."""
    path = [top]
    while path[-1].fit.spans.shape[0]:
        moves = [h for h in _removals(pb, path[-1], prior) if np.isfinite(h.evidence)]
        if not moves:
            break
        path.append(max(moves, key=lambda x: x.evidence))
    return path


def declared(path: list[History], margin: float, q: float = 0.0) -> int:
    """The index on the path of the declared history: the first whose cheapest removal
    costs at least ``margin`` in evidence (the last if none does)."""
    i = 0
    while i + 1 < len(path) and with_quiet(path[i], q) - with_quiet(path[i + 1], q) < margin:
        i += 1
    return i
