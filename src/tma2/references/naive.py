"""Naive baseline (SRD §5), ported from gitma ``packages/classical/src/naive.ts``: predict the
training-set means of log range, course vector and speed."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tma2.sim.geometry import bearing_of, f32, f32_angle
from tma2.types import SCHEMA_VERSION

NAIVE = "naive"


class _Acc:
    def __init__(self) -> None:
        self.log_range = 0.0
        self.sin = 0.0
        self.cos = 0.0
        self.speed = 0.0
        self.n = 0

    def add(self, own: np.ndarray, tgt: np.ndarray, i: int) -> None:
        self.log_range += math.log(
            math.hypot(tgt[i, 1] - own[i, 1], tgt[i, 2] - own[i, 2]) / 1000.0
        )
        self.sin += math.sin(float(tgt[i, 3]))
        self.cos += math.cos(float(tgt[i, 3]))
        self.speed += float(tgt[i, 4])
        self.n += 1

    def means(self) -> dict[str, Any]:
        return {
            "log_range_km": self.log_range / self.n,
            "course_sin": self.sin / self.n,
            "course_cos": self.cos / self.n,
            "speed_mps": self.speed / self.n,
            "n": self.n,
        }


def fit_naive(blocks: Any, train_digest: str) -> dict[str, Any]:
    """Fit on training blocks (index, meta, own, tgt, obs): final = last-sample labels;
    per_timestep = every post-zig label."""
    fin, per = _Acc(), _Acc()
    for _, meta, own, tgt, _obs in blocks:
        n = int(meta["samples"])
        o = own.astype(np.float64)
        t = tgt.astype(np.float64)
        fin.add(o, t, n - 1)
        for i in range(int(meta["zig_index"]) + 1, n):
            per.add(o, t, i)
    if fin.n == 0:
        raise ValueError("cannot fit naive baseline on an empty training set")
    return {
        "schema_version": SCHEMA_VERSION,
        "train_digest": train_digest,
        "final": fin.means(),
        "per_timestep": per.means(),
    }


def _last_bearing(obs: np.ndarray, i: int) -> float:
    for k in range(i, -1, -1):
        if obs[k, 2] != 0:
            return float(obs[k, 1])
    return 0.0


def _row(own: np.ndarray, obs: np.ndarray, m: dict[str, Any], i: int) -> dict[str, Any]:
    rng = 1000.0 * math.exp(float(m["log_range_km"]))
    b = _last_bearing(obs, i)
    return {
        "timestamp_s": float(own[i, 0]),
        "range_m": f32(rng),
        "course_rad": f32_angle(bearing_of(float(m["course_sin"]), float(m["course_cos"]))),
        "speed_mps": f32(float(m["speed_mps"])),
        "x_m": f32(float(own[i, 1]) + rng * math.sin(b)),
        "y_m": f32(float(own[i, 2]) + rng * math.cos(b)),
        "converged": True,
    }


def naive_predict(
    meta: dict[str, Any], own: np.ndarray, obs: np.ndarray, model: dict[str, Any], mode: str
) -> dict[str, Any]:
    n = int(meta["samples"])
    o = own.astype(np.float64)
    ob = obs.astype(np.float64)
    if mode == "final":
        rows = [_row(o, ob, model["final"], n - 1)]
    else:
        rows = [_row(o, ob, model["per_timestep"], i) for i in range(int(meta["zig_index"]) + 1, n)]
    return {
        "record": "prediction",
        "scenario_index": int(meta["index"]),
        "estimator": NAIVE,
        "mode": mode,
        "rows": rows,
    }
