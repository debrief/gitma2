"""Segmenter C (spec 005 FR-020–FR-025): nominators, coupled confirmation, and the
segmentation of each scored prefix. L adds per-row evidence to the search (``evidence``); with
none, the result is C's.

Per scenario:
1. **GLR statistic** (spec 004 control, note 08) on per-timestep batch least squares.
2. **Search** on prefixes every ``search_every_rows`` on a grid of ``search_step_rows`` anchored on
   the scored rows, from one cost table (``search.py``).
3. **Confirmation** (``confirm.py``) of both nominators' candidates.
4. **Segmentation** of each scored prefix k from what was accepted by row k: accepted transitions
   are transitions (unknown when their score is below ``margin``), near misses unknown, the rest
   steady; a steady piece shorter than L_min is unknown (FR-023, Definitions).
5. **Cost** of the segmentation on [0, k] in the hand-over mode, and its margin (the smallest
   score among the transitions in use).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.detect.confirm import layer_costs
from tma2.detect.controls import glr_stat, ls_states
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData, classical_predict
from tma2.types.generated.tma import SegmentParameters

from . import STEADY, TRANSITION, UNKNOWN, Interval, from_codes, validate
from .confirm import Confirmed, Nomination, confirm, glr_nominations, search_nominations
from .inputs import segmentation_inputs
from .search import anchored_grid, cost_table, run_search


@dataclass
class PrefixSegmentation:
    k: int
    intervals: list[Interval]
    cost: float
    margin: float | None


def glr(d: BearingData, window: int) -> np.ndarray:
    lst, lok = ls_states(d, classical_predict(d, "per_timestep")["rows"])
    return np.asarray(glr_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, lst, lok, window))


def search_by_prefix(
    d: BearingData,
    anchor: int,
    p: SegmentParameters,
    evidence: np.ndarray | None = None,
    k_max: int | None = None,
) -> list[tuple[int, list[tuple[int, int, bool]]]]:
    """The search's transitions on every ``search_every_rows`` prefix congruent to ``anchor``
    (from the first that holds two legs) up to ``k_max``, from one cost table."""
    k_max = d.n - 1 if k_max is None else k_max
    grid = anchored_grid(k_max, anchor, p.search_step_rows)
    table = (grid, cost_table(d, grid, p.l_min_rows))
    t_max = max(p.t_lengths_rows)
    first = anchor % p.search_every_rows
    out = []
    for k in range(first, k_max + 1, p.search_every_rows):
        if k < 2 * p.l_min_rows + p.t_min_rows or k not in set(grid.tolist()):
            continue
        _c, _legs, trans = run_search(
            d, k, p.search_penalty, p.l_min_rows, p.t_min_rows, t_max, p.search_step_rows,
            table=table, evidence=evidence,
        )  # fmt: skip
        out.append((k, trans))
    return out


def nominations_for(
    d: BearingData,
    anchor: int,
    p: SegmentParameters,
    stat: np.ndarray | None = None,
    evidence: np.ndarray | None = None,
) -> list[Nomination]:
    noms: list[Nomination] = []
    if math.isfinite(p.glr_threshold):
        s = glr(d, p.glr_window) if stat is None else stat
        noms += glr_nominations(s, p.glr_threshold, p)
    noms += search_nominations(search_by_prefix(d, anchor, p, evidence), p)
    return sorted(noms, key=lambda x: (x.row, x.source, x.lo))


def intervals_at(conf: Confirmed, k: int, p: SegmentParameters) -> list[Interval]:
    """The segmentation of [0, k] from what was decided by row k."""
    codes = np.full(k + 1, STEADY, dtype=np.int8)
    open_at_k = False
    for x in conf.transitions:
        if x.accepted_at > k:
            continue
        closed = x.end is not None and x.closed_at <= k
        e = min(x.end, k) if closed and x.end is not None else k
        if not closed:
            open_at_k = True
        codes[x.start : e + 1] = TRANSITION if x.score >= p.margin else UNKNOWN
    for nm in conf.near_misses:
        if nm.row <= k:
            sl = codes[nm.start : min(nm.end, k) + 1]
            sl[sl == STEADY] = UNKNOWN
    for iv in from_codes(codes):
        short_t = iv.kind == TRANSITION and iv.end - iv.start + 1 < p.t_min_rows
        if short_t and not (open_at_k and iv.end == k):
            codes[iv.start : iv.end + 1] = UNKNOWN  # cannot occur: lengths ≥ T_min
    for iv in from_codes(codes):
        if iv.kind == STEADY and iv.end - iv.start + 1 < p.l_min_rows:
            codes[iv.start : iv.end + 1] = UNKNOWN
    ivs = from_codes(codes)
    if open_at_k and ivs[-1].kind == TRANSITION:
        ivs[-1] = Interval(TRANSITION, ivs[-1].start, ivs[-1].end, True)
    validate(ivs, k, p.l_min_rows, p.t_min_rows)
    return ivs


def segment(
    layer: PhysicsLayer,
    data: list[BearingData],
    metas: list[dict[str, Any]],
    rows: list[list[int]],
    p: SegmentParameters,
    stats: list[np.ndarray] | None = None,
    evidence: list[np.ndarray] | None = None,
) -> list[list[PrefixSegmentation]]:
    """C (or L, with ``evidence``) on each scenario's scored rows, scenarios batched. The search
    grid is anchored on each scenario's first scored row (G5 rows are 30 rows apart)."""
    noms = []
    for i, d in enumerate(data):
        anchor = rows[i][0] if rows[i] else int(metas[i]["zig_index"])
        noms.append(
            nominations_for(
                d,
                anchor,
                p,
                None if stats is None else stats[i],
                None if evidence is None else evidence[i],
            )
        )
    r_max = max(d.n for d in data)
    confs = confirm(layer, data, noms, p, r_max)
    items: list[tuple[BearingData, int, LayerInputs]] = []
    owners: list[tuple[int, int]] = []
    segs: list[list[PrefixSegmentation]] = []
    for i, (d, conf) in enumerate(zip(data, confs, strict=True)):
        out = []
        for k in rows[i]:
            ivs = intervals_at(conf, k, p)
            trs = [(iv.start, iv.end) for iv in ivs if iv.kind == TRANSITION]
            scores = [x.score for x in conf.transitions if x.accepted_at <= k]
            out.append(PrefixSegmentation(k, ivs, math.nan, min(scores) if scores else None))
            inp = segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, trs, p.mode, True)
            if inp is not None:
                items.append((d, k, inp))
                owners.append((i, len(out) - 1))
        segs.append(out)
    for (i, q), cst in zip(owners, layer_costs(layer, items, r_max), strict=True):
        segs[i][q].cost = cst
    return segs
