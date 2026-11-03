"""Nominate-then-confirm segmentation (docs/research/07 §4, 08).

A nominating statistic (the steady-leg split statistic, the Gate D GLR, …) raises alarm episodes.
At an episode's first row a, the physics layer solves the history [0, a] with the knots accepted so
far, and once more with each candidate knot c in the window (every ``step`` rows of
[a − W + 1, a], none within ``step`` rows of an accepted knot). The candidate with the lowest cost
is accepted if it lowers the cost by more than τ (the cost is Σ (r/σ)², so τ is a χ² value with 2
degrees of freedom, the velocity increment). An accepted knot is used from row a on.

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
) -> list[list[Accepted]]:
    """Accepted knots per scenario, in time order, for alarms ``stats[i] > threshold``."""
    eps = [episodes(s > threshold, 10.0, merge_s=0.0) for s in stats]
    acc: list[list[Accepted]] = [[] for _ in data]
    for p in range(max((len(e) for e in eps), default=0)):
        items: list[tuple[BearingData, int, LayerInputs]] = []
        tags: list[tuple[int, int, int, int]] = []
        for i, d in enumerate(data):
            if p >= len(eps[i]):
                continue
            al, al_end = eps[i][p]
            cur = [a.row for a in acc[i]]
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
                inp = knot_inputs(d, al, [*cur, c], False)
                assert inp is not None
                items.append((d, al, inp))
                tags.append((i, al, al_end, c))
        best: dict[int, dict[str, Any]] = {}
        for (i, al, al_end, c), cst in zip(tags, layer_costs(layer, items, r_max), strict=True):
            b = best.setdefault(i, {})
            if c < 0:
                b["base"] = cst
            elif cst < b.get("cost", math.inf):
                b.update(cost=cst, row=c, alarm=al, alarm_end=al_end)
        for i, b in best.items():
            if "row" in b and b["base"] - b["cost"] > tau:
                acc[i].append(
                    Accepted(
                        int(b["alarm"]), int(b["alarm_end"]), int(b["row"]), b["base"] - b["cost"]
                    )
                )
    return acc


def knots_at(acc: list[Accepted], k: int) -> list[int]:
    """The knots in use at row k: those whose nominating alarm began at or before k."""
    return [a.row for a in acc if a.alarm <= k]
