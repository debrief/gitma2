"""Nominate-then-confirm segmentation (docs/research/07 §4, 08).

A nominating statistic (the steady-leg split statistic, the Gate D GLR, …) raises alarm episodes.
At an episode's first row a, the physics layer solves the history [0, a] with the knots accepted so
far, and once more with each candidate knot c in the window (every ``step`` rows of
[a − W + 1, a], none within ``step`` rows of an accepted knot). The candidate with the lowest cost
is accepted if it lowers the cost by more than τ (the cost is Σ (r/σ)², so τ is a χ² value with 2
degrees of freedom, the velocity increment). An accepted knot is used from row a on.

With ``turn_rows`` > 0 a manoeuvre is not instantaneous: a candidate is a turn *window* [c, c + T]
with a knot at each end, and the target moves on the chord between them (docs/research/08 §6; the
2017 Debrief note "Identifying multiple target legs", whose 3-minute search window this borrows as a
fixed turn length; spec 005 estimates transition lengths instead). A window that has
ended by row a adds two velocity increments and is tested at the χ² point with 4 degrees of
freedom that has the same tail probability as τ; one still open at a adds only its start knot and
is tested at τ. An accepted window's end knot comes into use once the window has passed.

The scenarios are processed side by side: every scenario's p-th episode is solved in one batched
pass, so a pass costs (1 + candidates) layer solves per scenario that has a p-th episode.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.cli.oracle import run_layer
from tma2.detect.matching import episodes
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, trivial_inputs
from tma2.references.classical import BearingData

BATCH = 256


@dataclass(frozen=True)
class Accepted:
    """A confirmed knot: the episode (first, last row) that nominated it and the knot's row."""

    alarm: int
    alarm_end: int
    row: int
    cost_drop: float
    end: int = -1  # the turn window's end knot (−1: a point knot)


def tau_4dof(tau: float) -> float:
    """The χ² value with 4 degrees of freedom whose tail probability equals that of ``tau`` with 2
    (P₂(x) = e^(−x/2); P₄(x) = e^(−x/2)(1 + x/2)), by Newton's method."""
    p = math.exp(-tau / 2.0)
    x = tau + 4.0
    for _ in range(50):
        f = math.exp(-x / 2.0) * (1.0 + x / 2.0) - p
        df = -math.exp(-x / 2.0) * x / 4.0
        x -= f / df
    return x


def knot_inputs(d: BearingData, k: int, knots: list[int], prior: bool) -> LayerInputs | None:
    """Trivial inputs on [0, k] with a hard knot at each row in ``knots`` (0 < r ≤ k); with
    ``prior`` each knot also carries the speed-continuity weight and its skip."""
    base = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
    if base is None:
        return None
    cp = np.zeros(d.n)
    for r in knots:
        if 0 < r <= k:
            cp[r] = 1.0
    sw = cp.copy() if prior else np.zeros(d.n)
    return LayerInputs(cp, sw, base.log_weight, base.theta0, sw.copy())


def window_inputs(d: BearingData, k: int, acc: list[Accepted], prior: bool) -> LayerInputs | None:
    """Inputs on [0, k] for the knots in use at row k (alarm ≤ k). A point knot carries the
    speed-continuity weight on itself (as ``knot_inputs``); a turn window carries it on its end
    knot once that is in use, skipping the start knot's increment (the chord), as the oracle does
    across a course change, and on its start knot while the window is still open."""
    base = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, k)
    if base is None:
        return None
    cp = np.zeros(d.n)
    sw = np.zeros(d.n)
    for a in acc:
        if a.alarm > k or not 0 < a.row <= k:
            continue
        cp[a.row] = 1.0
        if 0 < a.end <= k:
            cp[a.end] = 1.0
            if prior:
                sw[a.end] = 1.0
        elif prior:
            sw[a.row] = 1.0
    return LayerInputs(cp, sw, base.log_weight, base.theta0, sw.copy())


def layer_costs(
    layer: PhysicsLayer, items: list[tuple[BearingData, int, LayerInputs]], r_max: int
) -> list[float]:
    out: list[float] = []
    for s in range(0, len(items), BATCH):
        res = run_layer(layer, items[s : s + BATCH], r_max)
        out.extend(float(c) for c in res.cost)
    return out


def confirm_knots(
    layer: PhysicsLayer,
    data: list[BearingData],
    stats: list[np.ndarray],
    threshold: float,
    tau: float,
    window: int,
    step: int,
    r_max: int,
    turn_rows: int = 0,
) -> list[list[Accepted]]:
    """Accepted knots per scenario, in time order, for alarms ``stats[i] > threshold``; turn
    windows of ``turn_rows`` rows when it is positive (module docstring)."""
    tau4 = tau_4dof(tau)
    eps = [episodes(s > threshold, 10.0, merge_s=0.0) for s in stats]
    acc: list[list[Accepted]] = [[] for _ in data]
    for p in range(max((len(e) for e in eps), default=0)):
        items: list[tuple[BearingData, int, LayerInputs]] = []
        tags: list[tuple[int, int, int, int]] = []
        for i, d in enumerate(data):
            if p >= len(eps[i]):
                continue
            al, al_end = eps[i][p]
            cur = [r for a in acc[i] for r in (a.row, a.end) if 0 < r <= al]
            cands = [
                c
                for c in range(max(1, al - window + 1), al + 1, step)
                if all(abs(c - r) > step for r in cur)
            ]
            base = knot_inputs(d, al, cur, False)
            if base is None or not cands:
                continue
            items.append((d, al, base))
            tags.append((i, al, al_end, -1))
            for c in cands:
                new = [c, c + turn_rows] if turn_rows > 0 else [c]
                inp = knot_inputs(d, al, [*cur, *new], False)
                assert inp is not None
                items.append((d, al, inp))
                tags.append((i, al, al_end, c))
        best: dict[int, dict[str, Any]] = {}
        for (i, al, al_end, c), cst in zip(tags, layer_costs(layer, items, r_max), strict=True):
            b = best.setdefault(i, {})
            if c < 0:
                b["base"] = cst
            else:
                # with turn windows the candidates differ in size: compare their excess over
                # their own threshold (the base row comes first, so b["base"] is set)
                t = tau4 if 0 < turn_rows and c + turn_rows <= al else tau
                score = b["base"] - cst - t
                if score > b.get("score", -math.inf):
                    b.update(score=score, cost=cst, row=c, alarm=al, alarm_end=al_end)
        for i, b in best.items():
            if "row" in b and b["score"] > 0:
                acc[i].append(
                    Accepted(
                        int(b["alarm"]),
                        int(b["alarm_end"]),
                        int(b["row"]),
                        b["base"] - b["cost"],
                        int(b["row"]) + turn_rows if turn_rows > 0 else -1,
                    )
                )
    return acc


def knots_at(acc: list[Accepted], k: int) -> list[int]:
    """The knot rows in use at row k: those whose nominating alarm began at or before k, with a
    turn window's end knot once it is ≤ k."""
    return [r for a in acc if a.alarm <= k for r in (a.row, a.end) if 0 < r <= k]
