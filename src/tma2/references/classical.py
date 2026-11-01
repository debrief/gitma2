"""The classical estimator driver, ported from gitma ``packages/classical/src/estimate.ts``:
per-scenario bearing arrays, prediction rows, plausibility bounds and the per-timestep restart
rule (grid start at the first row, every 6th row, and whenever the warm solution is missing,
non-converged or implausible)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.sim.geometry import bearing_of, f32, f32_angle

from . import lsq

CLASSICAL = "classical"
PLAUSIBLE_MAX_SPEED_MPS = 25.0
PLAUSIBLE_MAX_RANGE_M = 100_000.0


@dataclass
class BearingData:
    t: np.ndarray
    ox: np.ndarray
    oy: np.ndarray
    z: np.ndarray
    valid: np.ndarray  # uint8
    zig_index: int
    sigma: float
    index: int

    @property
    def n(self) -> int:
        return int(self.t.shape[0])


@dataclass
class Solution:
    theta: np.ndarray
    converged: bool
    iterations: int
    cost: float


def bearing_data_from_record(record: dict[str, Any]) -> BearingData:
    """From a scenario dict (NDJSON record or decoded pack block)."""
    own = record["ownship"]["states"]
    obs = record["observations"]
    md = record["metadata"]
    return BearingData(
        t=np.array([s["timestamp_s"] for s in own], dtype=np.float64),
        ox=np.array([s["x_m"] for s in own], dtype=np.float64),
        oy=np.array([s["y_m"] for s in own], dtype=np.float64),
        z=np.array([o["bearing_rad"] for o in obs], dtype=np.float64),
        valid=np.array([1 if o["valid"] else 0 for o in obs], dtype=np.uint8),
        zig_index=int(md["zig_index"]),
        sigma=float(md["parameters"]["noise_sigma_rad"]),
        index=int(md["index"]),
    )


def bearing_data_from_arrays(meta: dict[str, Any], own: np.ndarray, obs: np.ndarray) -> BearingData:
    """From a pack block's arrays own [S,5] and obs [S,3] (float32 exact values)."""
    return BearingData(
        t=own[:, 0].astype(np.float64),
        ox=own[:, 1].astype(np.float64),
        oy=own[:, 2].astype(np.float64),
        z=obs[:, 1].astype(np.float64),
        valid=(obs[:, 2] != 0).astype(np.uint8),
        zig_index=int(meta["zig_index"]),
        sigma=float(meta["parameters"]["noise_sigma_rad"]),
        index=int(meta["index"]),
    )


def row_at(d: BearingData, sol: Solution, i: int) -> dict[str, Any]:
    """The target estimate implied by a solution at sample i, float32-rounded."""
    x0, y0, vx, vy = (float(v) for v in sol.theta)
    t = float(d.t[i])
    x = x0 + vx * t
    y = y0 + vy * t
    return {
        "timestamp_s": f32(t),
        "range_m": f32(math.hypot(x - d.ox[i], y - d.oy[i])),
        "course_rad": f32_angle(bearing_of(vx, vy)),
        "speed_mps": f32(math.hypot(vx, vy)),
        "x_m": f32(x),
        "y_m": f32(y),
        "converged": bool(sol.converged),
        "iterations": int(sol.iterations),
    }


def plausible(d: BearingData, sol: Solution, i: int) -> bool:
    x0, y0, vx, vy = (float(v) for v in sol.theta)
    t = float(d.t[i])
    rng = math.hypot(x0 + vx * t - d.ox[i], y0 + vy * t - d.oy[i])
    return math.hypot(vx, vy) <= PLAUSIBLE_MAX_SPEED_MPS and rng <= PLAUSIBLE_MAX_RANGE_M


def _better(d: BearingData, a: Solution, b: Solution, i: int) -> bool:
    pa, pb = plausible(d, a, i), plausible(d, b, i)
    if pa != pb:
        return pa
    return a.cost < b.cost


def empty_row(d: BearingData, i: int) -> dict[str, Any]:
    return {
        "timestamp_s": f32(float(d.t[i])),
        "range_m": 0.0,
        "course_rad": 0.0,
        "speed_mps": 0.0,
        "x_m": 0.0,
        "y_m": 0.0,
        "converged": False,
        "iterations": 0,
    }


def solve_batch(
    d: BearingData, upto: int, max_iterations: int = lsq.MAX_ITERATIONS
) -> Solution | None:
    found, th, conv, it, c = lsq.solve_batch(d.t, d.ox, d.oy, d.z, d.valid, upto, max_iterations)
    if not found:
        return None
    return Solution(theta=np.array(th), converged=bool(conv), iterations=int(it), cost=float(c))


def lm(
    d: BearingData, start: np.ndarray, upto: int, max_iterations: int = lsq.MAX_ITERATIONS
) -> Solution:
    th, conv, it, c = lsq.levenberg_marquardt(
        d.t, d.ox, d.oy, d.z, d.valid, start, upto, max_iterations
    )
    return Solution(theta=np.array(th), converged=bool(conv), iterations=int(it), cost=float(c))


def classical_predict(
    d: BearingData,
    mode: str,
    max_iterations: int = lsq.MAX_ITERATIONS,
    grid_every: int = lsq.GRID_EVERY,
) -> dict[str, Any]:
    """gitma ``classicalPredict``: a Prediction dict for one scenario."""
    n = d.n
    rows: list[dict[str, Any]] = []

    def emit(sol: Solution | None, i: int) -> None:
        if sol is None:
            rows.append(empty_row(d, i))
            return
        row = row_at(d, sol, i)
        if not plausible(d, sol, i):
            row["converged"] = False
        rows.append(row)

    if mode == "final":
        emit(solve_batch(d, n, max_iterations), n - 1)
    else:
        prev: Solution | None = None
        first = d.zig_index + 1
        for i in range(first, n):
            warm = None if prev is None else lm(d, prev.theta, i + 1, max_iterations)
            sol = warm
            need_grid = (
                warm is None
                or not warm.converged
                or not plausible(d, warm, i)
                or (grid_every > 0 and (i - first) % grid_every == 0)
            )
            if need_grid:
                fresh = solve_batch(d, i + 1, max_iterations)
                if fresh is not None and (sol is None or _better(d, fresh, sol, i)):
                    sol = fresh
            emit(sol, i)
            prev = sol if (sol is not None and plausible(d, sol, i)) else None
    return {
        "record": "prediction",
        "scenario_index": d.index,
        "estimator": CLASSICAL,
        "mode": mode,
        "rows": rows,
    }
