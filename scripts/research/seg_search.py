"""Spec 005 research R1: segmenter C's search stage, prototype and timing.

Segment costs are independent constant-velocity fits (gitma's LM, ``references.lsq``) on candidate
legs whose ends lie on a grid of every ``GRID`` rows. For a fixed start, the leg grows one grid
step at a time, warm-started from the previous fit propagated forward, with a grid restart every
``RESTART`` steps. The cost is Σ (r / σ)² over the leg's valid bearings.

Dynamic programming then tiles the prefix [0, k] with legs (at least ``L_MIN`` rows) and
transitions (``T_MIN`` to ``T_MAX`` rows). A transition's bearings are excluded from the fit but
charged ``TRANS_COST`` each, about the χ² a bearing would contribute to a fitting leg, so leaving a
bearing out pays only where it fits badly. Each leg after the first costs ``penalty``. The prefix
may end inside a transition (a turn in progress).

    uv run python scripts/research/seg_search.py --validation data/gd-val/validation.f32pack \\
        --start 500 --count 200 --out /tmp/seg.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from typing import Any

import numpy as np
from numba import njit

from tma2.references import lsq
from tma2.references.classical import BearingData

GRID = 3
L_MIN = 12  # 2 min at 10 s
T_MIN = 3  # 30 s
T_MAX = 18  # 3 min
TRANS_COST = 1.0
RESTART = 4
MAX_ITER = 20


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
    the leg is shorter than ``l_min`` rows or has fewer than 6 valid bearings)."""
    g = grid.shape[0]
    cost = np.full((g, g), np.inf)
    s2 = sigma * sigma
    for i in range(g):
        a = grid[i]
        have = False
        prev = np.zeros(4)
        tprev = 0.0
        steps = 0
        for j in range(i + 1, g):
            b = grid[j]
            if b - a + 1 < l_min:
                continue
            m = b - a + 1
            nv = 0
            for r in range(a, b + 1):
                nv += valid[r]
            if nv < 6:
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
            if not have or steps % RESTART == 0:
                found, st = lsq.grid_start(tt, oxs, oys, zs, vs, m)
                if found:
                    th2, c2 = _lm(tt, oxs, oys, zs, vs, st, m)
                    if c2 < c:
                        th, c = th2, c2
            steps += 1
            if math.isfinite(c):
                cost[i, j] = c / s2
                prev = th
                tprev = t[b]
                have = True
    return cost


@njit(cache=True)
def search(
    cost: np.ndarray,
    grid: np.ndarray,
    valid: np.ndarray,
    penalty: float,
    t_min: int,
    t_max: int,
    trans_cost: float,
) -> tuple[float, np.ndarray]:
    """Minimum total cost and the segmentation as rows [leg_start, leg_end, ...]; a final odd
    entry is the start of a transition still open at the prefix end."""
    g = grid.shape[0]
    f = np.full(g, np.inf)  # best cost of [0, grid[j]] ending with a leg ending at grid[j]
    back_i = np.full(g, -1, dtype=np.int64)  # that leg's start index
    back_p = np.full(g, -1, dtype=np.int64)  # the previous leg's end index (−1: none)
    cv = np.zeros(grid[g - 1] + 2)
    for r in range(grid[g - 1] + 1):
        cv[r + 1] = cv[r] + valid[r]
    for j in range(1, g):
        if cost[0, j] < f[j]:
            f[j] = cost[0, j]
            back_i[j] = 0
            back_p[j] = -1
        for i in range(1, j):
            if not math.isfinite(cost[i, j]):
                continue
            for p in range(i):
                gap = grid[i] - grid[p] - 1
                if gap < t_min:
                    break
                if gap > t_max or not math.isfinite(f[p]):
                    continue
                nt = cv[grid[i]] - cv[grid[p] + 1]
                v = f[p] + trans_cost * nt + cost[i, j] + penalty
                if v < f[j]:
                    f[j] = v
                    back_i[j] = i
                    back_p[j] = p
    # end: a leg ending at the last grid point, or an open transition after an earlier leg
    best = f[g - 1]
    end_p = -1
    last = grid[g - 1]
    for p in range(g - 1):
        gap = last - grid[p]
        if gap < t_min or gap > t_max or not math.isfinite(f[p]):
            continue
        nt = cv[last + 1] - cv[grid[p] + 1]
        v = f[p] + trans_cost * nt + penalty  # an open transition is a hypothesis too
        if v < best:
            best = v
            end_p = p
    out = []
    j = end_p if end_p >= 0 else g - 1
    while j >= 0 and back_i[j] >= 0:
        out.append(grid[j])
        out.append(grid[back_i[j]])
        j = back_p[j]
    res = np.empty(len(out) + (1 if end_p >= 0 else 0), dtype=np.int64)
    m = len(out)
    for q in range(m):
        res[q] = out[m - 1 - q]
    if end_p >= 0:
        res[m] = grid[end_p] + 1
    return best, res


def grid_for(k: int) -> np.ndarray:
    g = list(range(0, k + 1, GRID))
    if g[-1] != k:
        g.append(k)
    return np.asarray(g, dtype=np.int64)


def segment(
    d: BearingData, k: int, penalties: list[float]
) -> tuple[list[tuple[float, list[int]]], float, float]:
    """For the prefix [0, k]: per penalty (cost, segmentation rows); the cost-table seconds; the
    search seconds (all penalties)."""
    t0 = time.perf_counter()
    grid = grid_for(k)
    v = d.valid.astype(np.int64)
    cost = segment_costs(d.t, d.ox, d.oy, d.z, v, d.sigma, grid, L_MIN)
    t1 = time.perf_counter()
    out = []
    for pen in penalties:
        best, seg = search(cost, grid, v, pen, T_MIN, T_MAX, TRANS_COST)
        out.append((float(best), [int(x) for x in seg]))
    return out, t1 - t0, time.perf_counter() - t1


def _task(args: tuple[str, int, int, list[float]]) -> list[dict[str, Any]]:
    import sys

    sys.path.insert(0, "scripts/research")
    import leg_spike as ls  # type: ignore[import-not-found]

    from tma2.references.classical import bearing_data_from_arrays

    path, start, count, pens = args
    out: list[dict[str, Any]] = []
    for j, meta, own, _tgt, obs in ls.iter_selected(path, start, count):
        d = bearing_data_from_arrays(meta, own, obs)
        res, t_cost, t_search = segment(d, d.n - 1, pens)
        out.append(
            {
                "ordinal": j,
                "n": d.n,
                "manoeuvres": [
                    [int(s["start_index"]), int(s["end_index"])]
                    for s in meta.get("manoeuvres") or []
                ],
                "kinds": [s["kind"] for s in meta.get("manoeuvres") or []],
                "zig_index": int(meta["zig_index"]),
                "cost_seconds": t_cost,
                "search_seconds": t_search,
                "by_penalty": {
                    f"{p:g}": {"cost": c, "seg": sg} for p, (c, sg) in zip(pens, res, strict=True)
                },
            }
        )
    return out


def main() -> int:
    from concurrent.futures import ProcessPoolExecutor

    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    ap.add_argument("--start", type=int, default=500)
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--penalties", default="20,30,45,60,80")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pens = [float(x) for x in a.penalties.split(",")]
    chunk = 10
    tasks = [
        (a.validation, s, min(chunk, a.start + a.count - s), pens)
        for s in range(a.start, a.start + a.count, chunk)
    ]
    out: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for part in ex.map(_task, tasks):
            out.extend(part)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f)
    secs = [r["cost_seconds"] for r in out[1:]]  # the first includes numba compilation
    ns = [r["n"] for r in out]
    print(
        f"{len(out)} scenarios; n {min(ns)}–{max(ns)}; cost table s median {np.median(secs):.2f},"
        f" max {max(secs):.2f}; search s (all penalties) max {max(r['search_seconds'] for r in out[1:]):.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
