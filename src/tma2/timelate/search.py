"""A search over manoeuvre histories scored by evidence (spec 013, owner decision 2026-11-12).

A history is a set of manoeuvres (when, how long, which changes). Its score is the log
evidence of the bearings under Annex B's prior (``retest.log_evidence`` at a fit to the
posterior). From a starting history the search repeatedly evaluates every single addition the
score test proposes and every single removal, moves to the best if it raises the evidence, and
stops when nothing does. Every history it evaluates is kept: the best few, with probabilities
from their evidence, are the **candidate tracks** the period supports.

Classical; nothing trained. The prior is the simulator's own, so what this measures is what
exact knowledge of how targets manoeuvre is worth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .arc import TURN_STARTS, fit_arc
from .retest import (
    CLEAR,
    NEW_DURATION,
    TOP,
    Problem,
    Structure,
    candidates,
    joint_fit,
    log_evidence,
)

KINDS = ((True, False), (False, True), (True, True))  # turn, speed change, both
SAME_S = 120.0  # two histories whose manoeuvres pair up within this are one candidate


@dataclass
class History:
    fit: Structure
    kinds: np.ndarray  # [M, 2]
    evidence: float
    parts: dict[str, float]


def _score(
    pb: Problem, theta: np.ndarray, spans: np.ndarray, kinds: np.ndarray, prior: Any
) -> History:
    th = theta.copy()
    th[4:][~kinds.reshape(-1)] = 0.0
    for i in range(spans.shape[0]):  # a change switched on starts off zero
        for j in range(2):
            if kinds[i, j] and th[4 + 2 * i + j] == 0.0:
                th[4 + 2 * i + j] = 0.5 if j == 0 else 1.0
    g = joint_fit(pb, th, spans, free_changes=kinds, prior=prior)
    ev = log_evidence(pb, g, kinds, prior)
    total = ev["total"] if np.isfinite(ev["total"]) else -np.inf
    return History(g, kinds.copy(), float(total), ev)


def _additions(pb: Problem, h: History, prior: Any) -> list[History]:
    t, ox, oy, z, v, sigma = pb
    picked: list[float] = []
    for _s, c in candidates(pb, h.fit):
        if all(abs(c - q) >= 2 * CLEAR for q in picked):
            picked.append(c)
        if len(picked) == TOP:
            break
    out: list[History] = []
    for c in picked:
        a, b = c - NEW_DURATION / 2, c + NEW_DURATION / 2
        m = h.fit.spans.shape[0]
        k = int(np.searchsorted(h.fit.spans[:, 0], a)) if m else 0
        spans = np.insert(h.fit.spans, k, [a, b], axis=0)
        best = None
        for dc in TURN_STARTS:  # the new turn's size and sign, times fixed, bearings only
            th = np.insert(h.fit.theta, 4 + 2 * k, [dc, 0.0])
            g = fit_arc(t, ox, oy, z, v, sigma, spans, th)
            if best is None or g.cost < best.cost:
                best = g
        assert best is not None
        scored = []
        for kind in KINDS:
            kinds = np.insert(h.kinds, k, kind, axis=0)
            scored.append(_score(pb, best.theta, spans, kinds, prior))
        out += scored
    return out


def _removals(pb: Problem, h: History, prior: Any) -> list[History]:
    out = []
    for i in range(h.fit.spans.shape[0]):
        th = np.delete(h.fit.theta, [4 + 2 * i, 5 + 2 * i])
        out.append(
            _score(pb, th, np.delete(h.fit.spans, i, axis=0), np.delete(h.kinds, i, axis=0), prior)
        )
    return out


def _rekind(pb: Problem, h: History, prior: Any) -> list[History]:
    out = []
    for i in range(h.fit.spans.shape[0]):
        for kind in KINDS:
            if tuple(bool(x) for x in h.kinds[i]) == kind:
                continue
            kinds = h.kinds.copy()
            kinds[i] = kind
            out.append(_score(pb, h.fit.theta, h.fit.spans, kinds, prior))
    return out


def evidence_search(
    pb: Problem,
    theta0: np.ndarray,
    spans0: np.ndarray,
    prior: Any,
    max_manoeuvres: int = 10,
    steps: int = 12,
) -> tuple[History, list[History]]:
    """The best history found from a start, and every history evaluated on the way."""
    m = spans0.shape[0]
    kinds = np.zeros((m, 2), dtype=bool)
    kinds[:, 0] = True
    cur = _score(pb, theta0, spans0, kinds, prior)
    seen = [cur]
    for _ in range(steps):
        moves = _removals(pb, cur, prior) + _rekind(pb, cur, prior)
        if cur.fit.spans.shape[0] < max_manoeuvres:
            moves += _additions(pb, cur, prior)
        seen += moves
        if not moves:
            break
        best = max(moves, key=lambda x: x.evidence)
        if best.evidence <= cur.evidence + 1e-6:
            break
        cur = best
    return cur, seen


def _same(a: History, b: History) -> bool:
    sa, sb = a.fit.spans, b.fit.spans
    if sa.shape[0] != sb.shape[0]:
        return False
    return bool(sa.shape[0] == 0 or float(np.abs(sa.mean(axis=1) - sb.mean(axis=1)).max()) < SAME_S)


def candidate_set(seen: list[History], top: int = 5) -> list[tuple[History, float]]:
    """The distinct histories with the most evidence and their probabilities (the evidence
    normalised over the set: a probability among the candidates found, not over all histories)."""
    kept: list[History] = []
    for h in sorted(seen, key=lambda x: -x.evidence):
        if not np.isfinite(h.evidence):
            continue
        if any(_same(h, k) for k in kept):
            continue
        kept.append(h)
        if len(kept) == top:
            break
    if not kept:
        return []
    ev = np.array([h.evidence for h in kept])
    w = np.exp(ev - ev.max())
    w = w / w.sum()
    return [(h, float(p)) for h, p in zip(kept, w, strict=True)]
