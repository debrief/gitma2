"""Segmenter C's search stage (spec 005 FR-022, research R1): the additive leg search, the
nominator alongside GLR alarms.

**Cost table.** Segment costs are independent constant-velocity fits (gitma's LM,
``references.lsq``) on candidate legs whose ends lie on a grid. For a fixed start the leg grows
one grid step at a time, warm-started from the previous fit propagated forward, with a grid
restart every ``RESTART`` steps. The cost is Σ (r / σ)² over the leg's valid bearings. An entry
uses only the rows of its own leg, so one table on a grid serves every prefix ending on the grid
(prefix invariance, FR-002): the grid is anchored on the scored rows (``anchored_grid``), which
for G5 rows (zig + 5/10/15/20 min) all lie on one grid when the step divides 30 rows.

**Search.** Dynamic programming tiles the prefix [0, k] with legs (at least ``l_min`` rows) and
transitions (``t_min`` to ``t_max`` rows between legs). A transition's bearings are excluded from
the fit but charged ``trans_cost`` each, about the χ² a bearing contributes to a fitting leg, so
leaving a bearing out pays only where it fits badly. Each leg after the first costs ``penalty``.
The prefix may end inside a transition (a turn in progress).

**Evidence (L, FR-040).** A per-row log-likelihood ratio e (steady against transition) enters as
−2 Σ e over a leg's rows and +2 Σ e over a transition's (a cost is −2 × a log-likelihood). With
e = 0, the default, the search is C's exactly (SC-003).

Moved from ``scripts/research/seg_search.py`` (R1), with the grid, lengths and evidence made
parameters for MAN2 (re-plan, 2026-11-04).
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

from tma2.physics.reference import MIN_SIGMA_RAD
from tma2.references import lsq
from tma2.references.classical import BearingData

RESTART = 4
MAX_ITER = 20
# A warm-started fit whose cost rises by more than JUMP_PER_ROW per added valid bearing plus
# JUMP_BASE (in χ² units) is re-tried from a fresh grid start (Gate S panel round 1, R4).
JUMP_PER_ROW = 9.0
JUMP_BASE = 30.0
MIN_VALID = 6
TRANS_COST = 1.0


@njit(cache=True)
def _lm(
    tt: np.ndarray,
    oxs: np.ndarray,
    oys: np.ndarray,
    zs: np.ndarray,
    vs: np.ndarray,
    start: np.ndarray,
    m: int,
) -> tuple[np.ndarray, float]:
    try:
        th, _conv, _it, c = lsq.levenberg_marquardt(tt, oxs, oys, zs, vs, start, m, MAX_ITER)
    except Exception:  # noqa: BLE001
        return np.full(4, np.nan), math.inf
    return th, c


@njit(cache=True)
def segment_costs(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    sigma: float,
    grid: np.ndarray,
    l_min: int,
) -> np.ndarray:
    """cost[i, j]: the χ² cost of one constant-velocity leg on rows grid[i] … grid[j] (inf where
    the leg is shorter than ``l_min`` rows or has fewer than ``MIN_VALID`` valid bearings).

    A longer leg nested in a shorter one's start cannot have a lower best-fit cost, so a table
    where cost[i, j − 1] > cost[i, j] holds a failed fit (Gate S panel round 1, R4: warm starts
    landing in a bad minimum). Two repairs: a warm-started fit that jumps by more than
    ``JUMP_PER_ROW`` per added bearing plus ``JUMP_BASE`` is re-tried from a grid start, and a
    backward pass re-fits each shorter leg from the longer leg's solution where the order is
    broken, keeping the lower cost."""
    g = grid.shape[0]
    cost = np.full((g, g), np.inf)
    theta = np.full((g, g, 4), np.nan)
    s2 = sigma * sigma
    for i in range(g):
        a = grid[i]
        have = False
        prev = np.zeros(4)
        tprev = 0.0
        cprev = 0.0
        nvprev = 0
        steps = 0
        for j in range(i + 1, g):
            b = grid[j]
            if b - a + 1 < l_min:
                continue
            m = b - a + 1
            nv = 0
            for r in range(a, b + 1):
                nv += valid[r]
            if nv < MIN_VALID:
                continue
            tt = np.empty(m)
            for r in range(m):
                tt[r] = t[a + r] - t[b]
            oxs = ox[a : b + 1]
            oys = oy[a : b + 1]
            zs = z[a : b + 1]
            vs = valid[a : b + 1]
            th = np.full(4, np.nan)
            c = math.inf
            if have:
                st = prev.copy()
                st[0] += prev[2] * (t[b] - tprev)
                st[1] += prev[3] * (t[b] - tprev)
                th, c = _lm(tt, oxs, oys, zs, vs, st, m)
            jump = have and c > cprev + s2 * (JUMP_PER_ROW * (nv - nvprev) + JUMP_BASE)
            if not have or steps % RESTART == 0 or jump or not math.isfinite(c):
                found, st = lsq.grid_start(tt, oxs, oys, zs, vs, m)
                if found:
                    th2, c2 = _lm(tt, oxs, oys, zs, vs, st, m)
                    if c2 < c:
                        th, c = th2, c2
            steps += 1
            if math.isfinite(c):
                cost[i, j] = c / s2
                theta[i, j] = th
                prev = th
                tprev = t[b]
                cprev = c
                nvprev = nv
                have = True
        # backward repair: a shorter leg costing more than its longer extension failed its fit
        for j in range(g - 1, i + 1, -1):
            if not (math.isfinite(cost[i, j]) and math.isfinite(cost[i, j - 1])):
                continue
            if cost[i, j - 1] <= cost[i, j]:
                continue
            b = grid[j - 1]
            m = b - a + 1
            tt = np.empty(m)
            for r in range(m):
                tt[r] = t[a + r] - t[b]
            st = theta[i, j].copy()
            st[0] -= st[2] * (t[grid[j]] - t[b])
            st[1] -= st[3] * (t[grid[j]] - t[b])
            th, c = _lm(tt, ox[a : b + 1], oy[a : b + 1], z[a : b + 1], valid[a : b + 1], st, m)
            if math.isfinite(c) and c / s2 < cost[i, j - 1]:
                cost[i, j - 1] = c / s2
                theta[i, j - 1] = th
    return cost


@njit(cache=True)
def search(
    cost: np.ndarray,
    grid: np.ndarray,
    valid: np.ndarray,
    evidence: np.ndarray,
    penalty: float,
    t_min: int,
    t_max: int,
    trans_cost: float,
) -> tuple[float, np.ndarray]:
    """Minimum total cost on [0, grid[-1]] and the segmentation as rows [leg_start, leg_end, …];
    a final odd entry is the first row of a transition still open at the prefix end. ``cost`` may
    be larger than ``grid`` (a table built for a longer grid): only its leading block is used."""
    g = grid.shape[0]
    last = grid[g - 1]
    f = np.full(g, np.inf)  # best cost of [0, grid[j]] ending with a leg ending at grid[j]
    back_i = np.full(g, -1, dtype=np.int64)  # that leg's start index
    back_p = np.full(g, -1, dtype=np.int64)  # the previous leg's end index (−1: none)
    cv = np.zeros(last + 2)
    ce = np.zeros(last + 2)
    for r in range(last + 1):
        cv[r + 1] = cv[r] + valid[r]
        ce[r + 1] = ce[r] + evidence[r]
    for j in range(1, g):
        if math.isfinite(cost[0, j]):
            v0 = cost[0, j] - 2.0 * (ce[grid[j] + 1] - ce[0])
            if v0 < f[j]:
                f[j] = v0
                back_i[j] = 0
                back_p[j] = -1
        for i in range(1, j):
            if not math.isfinite(cost[i, j]):
                continue
            leg = cost[i, j] - 2.0 * (ce[grid[j] + 1] - ce[grid[i]])
            for p in range(i):
                gap = grid[i] - grid[p] - 1
                if gap < t_min:
                    break
                if gap > t_max or not math.isfinite(f[p]):
                    continue
                nt = cv[grid[i]] - cv[grid[p] + 1]
                et = ce[grid[i]] - ce[grid[p] + 1]
                v = f[p] + trans_cost * nt + 2.0 * et + leg + penalty
                if v < f[j]:
                    f[j] = v
                    back_i[j] = i
                    back_p[j] = p
    # end: a leg ending at the last grid point, or an open transition after an earlier leg
    best = f[g - 1]
    end_p = -1
    for p in range(g - 1):
        gap = last - grid[p]
        if gap < t_min or gap > t_max or not math.isfinite(f[p]):
            continue
        nt = cv[last + 1] - cv[grid[p] + 1]
        et = ce[last + 1] - ce[grid[p] + 1]
        v = f[p] + trans_cost * nt + 2.0 * et + penalty  # an open transition is a hypothesis too
        if v < best:
            best = v
            end_p = p
    out = []
    j = end_p if end_p >= 0 else g - 1
    while j >= 0 and back_i[j] >= 0:
        out.append(grid[j])
        out.append(grid[back_i[j]])
        j = back_p[j]
    m = len(out)
    res = np.empty(m + (1 if end_p >= 0 else 0), dtype=np.int64)
    for q in range(m):
        res[q] = out[m - 1 - q]
    if end_p >= 0:
        res[m] = grid[end_p] + 1
    return best, res


def anchored_grid(k_max: int, anchor: int, step: int) -> np.ndarray:
    """Rows 0 and every ``anchor + i·step`` in [0, k_max] (i of either sign), so that each row
    congruent to ``anchor`` mod ``step`` is a grid point and a prefix ending there needs no table
    of its own."""
    first = anchor % step
    rows = list(range(first, k_max + 1, step))
    if not rows or rows[0] != 0:
        rows.insert(0, 0)
    return np.asarray(rows, dtype=np.int64)


def prefix_grid(grid: np.ndarray, k: int) -> np.ndarray:
    """The grid points of a prefix [0, k]; ``k`` must be a grid point."""
    m = int(np.searchsorted(grid, k, side="right"))
    if m == 0 or int(grid[m - 1]) != k:
        raise ValueError(f"row {k} is not on the grid")
    return grid[:m]


def cost_table(d: BearingData, grid: np.ndarray, l_min: int) -> np.ndarray:
    sigma = max(float(d.sigma), MIN_SIGMA_RAD)
    return segment_costs(d.t, d.ox, d.oy, d.z, d.valid.astype(np.int64), sigma, grid, l_min)


def legs_and_transitions(
    seg: np.ndarray, k: int
) -> tuple[list[tuple[int, int]], list[tuple[int, int, bool]]]:
    """Legs (first, last) and transitions (first, last, open) from ``search``'s row list."""
    rows = [int(x) for x in seg]
    legs = [(rows[q], rows[q + 1]) for q in range(0, len(rows) - 1, 2)]
    trans: list[tuple[int, int, bool]] = []
    for (_a0, b0), (a1, _b1) in zip(legs, legs[1:], strict=False):
        trans.append((b0 + 1, a1 - 1, False))
    if len(rows) % 2 == 1:
        trans.append((rows[-1], k, True))
    return legs, trans


def run_search(
    d: BearingData,
    k: int,
    penalty: float,
    l_min: int,
    t_min: int,
    t_max: int,
    step: int,
    anchor: int | None = None,
    table: tuple[np.ndarray, np.ndarray] | None = None,
    evidence: np.ndarray | None = None,
    trans_cost: float = TRANS_COST,
) -> tuple[float, list[tuple[int, int]], list[tuple[int, int, bool]]]:
    """Search the prefix [0, k]: (cost, legs, transitions). ``table`` is (grid, cost) from a
    ``cost_table`` call on a grid containing k (anchored at k by default); one table serves every
    prefix on its grid."""
    if table is None:
        grid = anchored_grid(k, k if anchor is None else anchor, step)
        table = (grid, cost_table(d, grid, l_min))
    grid_full, cost = table
    grid = prefix_grid(grid_full, k)
    v = d.valid.astype(np.int64)
    e = np.zeros(d.n) if evidence is None else np.asarray(evidence, dtype=np.float64)
    best, seg = search(cost, grid, v, e, penalty, t_min, t_max, trans_cost)
    legs, trans = legs_and_transitions(seg, k)
    return float(best), legs, trans
