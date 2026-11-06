"""Segmenter C's coupled nominate-and-confirm stage (spec 005 FR-021–FR-023, research R2).

**Nominations** are (row a, candidate starts [lo, hi], source):
* **GLR:** each alarm episode of the GLR statistic above ``glr_threshold``, at its first row and
  again every ``retest_rows`` while it stays raised (note 08 §5 item 10); candidate starts in the
  last ``window_rows`` rows.
* **Search:** the additive search (``search.py``), run on prefixes every ``search_every_rows``
  rows; a closed transition (s, e) it reports with e + ``search_horizon_rows`` ≤ k is nominated at
  that prefix's row k, with starts within ± ``window_rows`` / 2 of s. A transition already
  nominated (start within ``candidate_step_rows``) is not nominated again.

**Confirmation** runs on the prefix [0, a] with the transitions accepted so far:
1. Starts c on a ``candidate_step_rows`` grid, not touching an accepted transition, each with the
   middle length of ``t_lengths_rows``.
2. At the best start, every length.
3. The best candidate is accepted if its cost drop exceeds the χ² point for its degrees of
   freedom: 4 for a closed transition (two velocity increments, ``tau_4dof``), 2 for one still open
   at a (its start knot only, ``tau``). With L's evidence, the point is shifted by twice the
   evidence summed over the candidate's rows, capped at ± τ/2 (zero evidence: C).
4. **Polish:** a closed transition's start, then its end, is re-optimised within ± ``polish_rows``
   under the same coupled cost.

An accepted open transition is **closed** at row c + max(``t_lengths_rows``) − 1, where every
length is closed: the length with the lowest cost on that prefix is kept and polished. Until then
it is reported open.

Everything a nomination at row a decides uses bearings at rows ≤ a only, and is used for prefixes
k ≥ a only, so a prefix's segmentation does not depend on later bearings (FR-002).

Each scenario's confirmation is a coroutine that yields batches of physics-layer requests (prefix
row, transitions) and receives their costs; ``confirm`` drives all scenarios side by side so
every solve is batched, as note 08's ``confirm_knots`` does.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Generator, Sequence
from dataclasses import dataclass, field

import numpy as np

from tma2.detect.confirm import layer_costs, tau_4dof
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData
from tma2.types.generated.tma import SegmentParameters

from .inputs import segmentation_inputs

OPEN_END = 1 << 30  # an open transition's end: beyond any prefix, so only its start knot is used

Request = tuple[int, list[tuple[int, int]]]  # (prefix row k, transitions as inclusive rows)


@dataclass(frozen=True)
class Nomination:
    row: int  # a: the prefix the test runs on
    lo: int  # candidate starts lo … hi
    hi: int
    source: str  # "glr" | "search" | "close"


@dataclass
class Transition:
    start: int
    end: int | None  # None while open
    accepted_at: int  # in use for prefixes k ≥ this row
    closed_at: int  # the end is in use for prefixes k ≥ this row (≥ accepted_at)
    drop: float  # cost drop at acceptance
    score: float  # drop − threshold at acceptance
    source: str
    # The start as accepted. Closing an open transition polishes its start with bearings up to
    # the closing row, so prefixes before the close must keep this one (FR-002).
    accepted_start: int | None = None

    def __post_init__(self) -> None:
        if self.accepted_start is None:
            self.accepted_start = self.start

    def start_at(self, k: int) -> int:
        """The start in use for prefix k (≥ accepted_at)."""
        closed = self.end is not None and self.closed_at <= k
        return self.start if closed or self.accepted_start is None else self.accepted_start


@dataclass
class NearMiss:
    """A rejected candidate whose score was within the margin (FR-023: its rows are unknown)."""

    start: int
    end: int
    row: int
    score: float


@dataclass
class Confirmed:
    transitions: list[Transition] = field(default_factory=list)
    near_misses: list[NearMiss] = field(default_factory=list)
    solves: int = 0


def glr_nominations(stat: np.ndarray, threshold: float, p: SegmentParameters) -> list[Nomination]:
    """GLR alarm episodes, at their first row and every ``retest_rows`` while raised."""
    out: list[Nomination] = []
    raised = stat > threshold
    n = int(stat.shape[0])
    r = 0
    while r < n:
        if not raised[r]:
            r += 1
            continue
        a0 = r
        while r < n and raised[r]:
            r += 1
        for a in range(a0, r, p.retest_rows):
            out.append(Nomination(a, max(1, a - p.window_rows + 1), a, "glr"))
    return out


def search_nominations(
    by_prefix: Sequence[tuple[int, Sequence[tuple[int, int, bool]]]], p: SegmentParameters
) -> list[Nomination]:
    """Nominations from the search's transitions on successive prefixes (k, transitions)."""
    out: list[Nomination] = []
    seen: list[int] = []
    half = p.window_rows // 2
    for k, trans in by_prefix:
        for s, e, is_open in trans:
            if is_open or e + p.search_horizon_rows > k:
                continue
            if any(abs(s - x) <= p.candidate_step_rows for x in seen):
                continue
            seen.append(s)
            out.append(Nomination(k, max(1, s - half), min(k, s + half), "search"))
    return out


def _in_use(acc: list[Transition], a: int) -> list[tuple[int, int]]:
    """Transitions as the physics layer sees them at prefix a (open: start knot only)."""
    out = []
    for x in acc:
        if x.accepted_at > a:
            continue
        end = x.end if (x.end is not None and x.closed_at <= a) else OPEN_END
        out.append((x.start, end))
    return out


def _free(c: int, e: int, acc: list[Transition], gap: int) -> bool:
    """[c, e] keeps ``gap`` rows clear of every accepted transition."""
    for x in acc:
        xe = x.end if x.end is not None else x.start + 1
        if c <= xe + gap and e >= x.start - gap:
            return False
    return True


def _confirm_one(
    n: int, noms: list[Nomination], p: SegmentParameters, evidence: np.ndarray | None = None
) -> Generator[list[Request], list[float], Confirmed]:
    tau = p.tau
    tau4 = tau_4dof(tau)
    lengths = sorted(set(p.t_lengths_rows))
    l_mid = lengths[len(lengths) // 2]
    l_max = lengths[-1]
    gap = p.candidate_step_rows
    res = Confirmed()
    acc = res.transitions
    heap: list[tuple[int, int, Nomination]] = [(x.row, i, x) for i, x in enumerate(noms)]
    heapq.heapify(heap)
    seq = len(noms)

    ce = None if evidence is None else np.concatenate([[0.0], np.cumsum(evidence)])

    def thr(c: int, length: int, a: int) -> float:
        """The χ² point for the candidate's degrees of freedom, shifted by L's evidence over
        its rows (a prior log-odds: + steady raises it), capped at ± τ/2 (research R6)."""
        base = tau4 if c + length - 1 <= a else tau
        if ce is None:
            return base
        e = min(c + length - 1, a)
        shift = 2.0 * float(ce[e + 1] - ce[c])
        return base + max(-tau / 2.0, min(tau / 2.0, shift))

    def polish(
        a: int, others: list[tuple[int, int]], c: int, e: int, cost: float
    ) -> Generator[list[Request], list[float], tuple[int, int, float]]:
        for which in ("start", "end"):
            cands: list[tuple[int, int]] = []
            for dd in range(-p.polish_rows, p.polish_rows + 1):
                if dd == 0:
                    continue
                cs, ce = (c + dd, e) if which == "start" else (c, e + dd)
                if cs < 1 or ce > a or ce - cs + 1 < p.t_min_rows:
                    continue
                if not _free(cs, ce, [x for x in acc if x.start != c], gap):
                    continue
                cands.append((cs, ce))
            if not cands:
                continue
            costs = yield [(a, [*others, ce_]) for ce_ in cands]
            res.solves += len(cands)
            j = int(np.argmin(costs))
            if costs[j] < cost:
                (c, e), cost = cands[j], costs[j]
        return c, e, cost

    while heap:
        a, _i, nom = heapq.heappop(heap)
        if a >= n:
            continue
        if nom.source == "close":
            x = next(t for t in acc if t.start == nom.lo and t.end is None)
            others = [t for t in _in_use(acc, a) if t[0] != x.start]
            lens = [ln for ln in lengths if x.start + ln - 1 <= a]
            costs = yield [(a, [*others, (x.start, x.start + ln - 1)]) for ln in lens]
            res.solves += len(lens)
            j = int(np.argmin(costs))
            c, e, _cost = yield from polish(a, others, x.start, x.start + lens[j] - 1, costs[j])
            x.start, x.end, x.closed_at = c, e, a
            continue
        cur = _in_use(acc, a)
        starts = [
            c
            for c in range(nom.lo, nom.hi + 1, gap)
            if c >= 1 and _free(c, c + l_mid - 1, acc, gap)
        ]
        if not starts:
            continue
        costs = yield [(a, cur)] + [(a, [*cur, (c, c + l_mid - 1)]) for c in starts]
        res.solves += 1 + len(starts)
        base = costs[0]
        sc = [base - costs[1 + q] - thr(c, l_mid, a) for q, c in enumerate(starts)]
        q = int(np.argmax(sc))
        c = starts[q]
        rest = [ln for ln in lengths if ln != l_mid and _free(c, c + ln - 1, acc, gap)]
        best_len, best_score, best_cost = l_mid, sc[q], costs[1 + q]
        if rest:
            costs2 = yield [(a, [*cur, (c, c + ln - 1)]) for ln in rest]
            res.solves += len(rest)
            for ln, cst in zip(rest, costs2, strict=True):
                s = base - cst - thr(c, ln, a)
                if s > best_score:
                    best_len, best_score, best_cost = ln, s, cst
        e = c + best_len - 1
        if best_score <= 0.0:
            if best_score > -p.margin:
                res.near_misses.append(NearMiss(c, min(e, a), a, best_score))
            continue
        if e <= a:
            c, e, best_cost = yield from polish(a, cur, c, e, best_cost)
            acc.append(Transition(c, e, a, a, base - best_cost, best_score, nom.source))
        else:
            acc.append(Transition(c, None, a, a, base - best_cost, best_score, nom.source))
            seq += 1
            close = Nomination(c + l_max - 1, c, c, "close")
            heapq.heappush(heap, (close.row, seq, close))
    return res


def confirm(
    layer: PhysicsLayer,
    data: list[BearingData],
    nominations: list[list[Nomination]],
    p: SegmentParameters,
    r_max: int,
    speed_prior: bool = False,
    evidence: list[np.ndarray] | None = None,
) -> list[Confirmed]:
    """Run every scenario's confirmation side by side; each round batches all pending requests.
    The confirmation cost is the chord with no speed prior by default, as note 08's
    ``knot_inputs`` (the hand-over mode is applied afterwards)."""
    gens = [
        _confirm_one(d.n, noms, p, None if evidence is None else evidence[i])
        for i, (d, noms) in enumerate(zip(data, nominations, strict=True))
    ]
    out: list[Confirmed | None] = [None] * len(data)
    pending: dict[int, list[Request]] = {}
    for i, g in enumerate(gens):
        try:
            pending[i] = next(g)
        except StopIteration as stop:
            out[i] = stop.value
    while pending:
        items: list[tuple[BearingData, int, LayerInputs]] = []
        owners: list[int] = []
        for i, reqs in pending.items():
            d = data[i]
            for k, trs in reqs:
                inp = segmentation_inputs(
                    d.t, d.ox, d.oy, d.z, d.valid, k, trs, "chord", speed_prior
                )
                if inp is None:
                    raise ValueError(f"scenario {d.index}: no valid bearing on [0, {k}]")
                items.append((d, k, inp))
                owners.append(i)
        costs = layer_costs(layer, items, r_max)
        by: dict[int, list[float]] = {}
        for i, cst in zip(owners, costs, strict=True):
            by.setdefault(i, []).append(cst if math.isfinite(cst) else math.inf)
        nxt: dict[int, list[Request]] = {}
        for i in pending:
            try:
                nxt[i] = gens[i].send(by[i])
            except StopIteration as stop:
                out[i] = stop.value
        pending = nxt
    return [x if x is not None else Confirmed() for x in out]
