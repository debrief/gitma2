"""Segmentation metrics (spec 005 FR-060, FR-061, research R7).

All functions take per-row codes (``STEADY``, ``TRANSITION``, ``UNKNOWN``) for one vessel of one
scenario on a prefix [0, k], or lists of transitions as inclusive (start, end) rows. Rows the
truth marks unknown are excluded from contamination and coverage.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from . import STEADY, TRANSITION, Interval, from_codes


def contamination(pred: np.ndarray, truth: np.ndarray) -> float:
    """Fraction of rows labelled steady (and truly steady or transition) that are truly
    transition; NaN when nothing scored is labelled steady."""
    scored = truth != 2
    steady = (pred == STEADY) & scored
    n = int(steady.sum())
    if n == 0:
        return math.nan
    return float(((truth == TRANSITION) & steady).sum()) / n


def coverage(pred: np.ndarray, truth: np.ndarray) -> float:
    """Fraction of truly steady rows labelled steady; NaN when no row is truly steady."""
    ts = truth == STEADY
    n = int(ts.sum())
    if n == 0:
        return math.nan
    return float(((pred == STEADY) & ts).sum()) / n


def transitions_of(codes: np.ndarray) -> list[tuple[int, int]]:
    return [(iv.start, iv.end) for iv in from_codes(codes) if iv.kind == TRANSITION]


def false_split(pred_transitions: Sequence[tuple[int, int]], truth_changes: int) -> bool | None:
    """True when a transition is reported on a prefix with no target change; None when the prefix
    contains a change (the measure does not apply)."""
    if truth_changes > 0:
        return None
    return len(pred_transitions) > 0


def leg_count(codes: np.ndarray) -> int:
    return sum(1 for iv in from_codes(codes) if iv.kind == STEADY)


def match_transitions(
    pred: Sequence[tuple[int, int]], truth: Sequence[tuple[int, int]]
) -> list[int | None]:
    """For each truth transition, the index of the predicted transition matched to it, or None.

    Greedy one-to-one matching by boundary error (``boundary_error``), smallest first; a pair is
    eligible only if the intervals overlap or their nearest ends are within the larger of the two
    lengths, so a far transition is never matched."""
    pairs: list[tuple[int, int, int]] = []
    for i, (a, b) in enumerate(truth):
        for j, (c, d) in enumerate(pred):
            gap = max(c - b, a - d, 0)
            if gap <= max(b - a + 1, d - c + 1):
                pairs.append((boundary_error((a, b), (c, d)), i, j))
    pairs.sort()
    out: list[int | None] = [None] * len(truth)
    used: set[int] = set()
    for _e, i, j in pairs:
        if out[i] is None and j not in used:
            out[i] = j
            used.add(j)
    return out


def boundary_error(truth: tuple[int, int], pred: tuple[int, int]) -> int:
    """Rows between the boundaries: max(|start − start|, |end − end|)."""
    return max(abs(truth[0] - pred[0]), abs(truth[1] - pred[1]))


def boundary_hits(
    pred: Sequence[tuple[int, int]], truth: Sequence[tuple[int, int]], tol_rows: int
) -> list[bool]:
    """Per truth transition: matched, with both boundaries within ``tol_rows``."""
    m = match_transitions(pred, truth)
    return [
        j is not None and boundary_error(truth[i], pred[j]) <= tol_rows for i, j in enumerate(m)
    ]


def gap_recovered(e_one_leg: float, e_seg: float, e_oracle: float) -> float:
    """(one leg − segmentation) ÷ (one leg − oracle), from medians (FR-061); NaN when the oracle
    is no better than one leg."""
    den = e_one_leg - e_oracle
    if not den > 0:
        return math.nan
    return (e_one_leg - e_seg) / den


# --- live metrics (FR-060: reported, not gated) --------------------------------------------


def detection_delays(
    seq: Sequence[tuple[int, list[tuple[int, int]]]],
    truth: Sequence[tuple[int, int]],
    tol_rows: int,
) -> list[int | None]:
    """For each truth transition (a, b), the rows from a to the first prefix k ≥ a on which a
    transition matched to it is reported within ``tol_rows`` of a at its start; None if never.
    ``seq`` is (k, transitions on [0, k]) in increasing k."""
    out: list[int | None] = []
    for a, _b in truth:
        delay: int | None = None
        for k, pred in seq:
            if k < a:
                continue
            for c, _d in pred:
                if abs(c - a) <= tol_rows:
                    delay = k - a
                    break
            if delay is not None:
                break
        out.append(delay)
    return out


def false_transitions(
    seq: Sequence[tuple[int, list[tuple[int, int]]]],
    truth: Sequence[tuple[int, int]],
    tol_rows: int,
) -> int:
    """Distinct reported transitions, over all prefixes, whose start is not within ``tol_rows``
    of a truth transition's start (a transition reappearing on later prefixes with the same start,
    to ``tol_rows``, is counted once)."""
    seen: list[int] = []
    n = 0
    for _k, pred in seq:
        for c, _d in pred:
            if any(abs(c - a) <= tol_rows for a, _b in truth):
                continue
            if any(abs(c - s) <= tol_rows for s in seen):
                continue
            seen.append(c)
            n += 1
    return n


def boundary_moves(
    seq: Sequence[tuple[int, list[tuple[int, int]]]], tol_rows: int
) -> tuple[int, int]:
    """(moves, tracked): of the closed transitions reported on one prefix (ending before its last
    row; an open one still grows) and tracked to the next (the next prefix's transition
    overlapping it), how many have a boundary that moves by more than ``tol_rows``."""
    moves = tracked = 0
    for (k0, p0), (_k1, p1) in zip(seq, seq[1:], strict=False):
        for c, d in p0:
            if d >= k0:
                continue
            nxt = [(e, f) for e, f in p1 if e <= d and f >= c]
            if not nxt:
                continue
            tracked += 1
            e, f = min(nxt, key=lambda x: boundary_error((c, d), x))
            if boundary_error((c, d), (e, f)) > tol_rows:
                moves += 1
    return moves, tracked


def steady_hours(truth: np.ndarray, dt_s: float) -> float:
    return float((truth == STEADY).sum()) * dt_s / 3600.0


def intervals_rows(intervals: Sequence[Interval]) -> int:
    return sum(iv.end - iv.start + 1 for iv in intervals)
