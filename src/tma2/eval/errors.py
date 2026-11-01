"""Per-row errors of an estimate against truth (gitma ``packages/eval/src/errors.ts``)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.references.lsq import angle_diff
from tma2.sim.geometry import mps_to_kt, rad_to_deg

GROSS_RANGE_REL = 0.5


@dataclass
class RowError:
    t_since_zig_s: float
    range_rel: float
    course_deg: float
    speed_kt: float
    position_m: float
    gross: bool
    converged: bool


@dataclass
class Truth:
    """One scenario's truth as arrays (from a pack block or a record)."""

    index: int
    samples: int
    dt: float
    zig_time_s: float
    zig_index: int
    meta: dict[str, Any]
    own: np.ndarray  # [S,5] t,x,y,course,speed
    tgt: np.ndarray  # [S,5]

    @classmethod
    def from_block(cls, meta: dict[str, Any], own: np.ndarray, tgt: np.ndarray) -> Truth:
        return cls(
            index=int(meta["index"]),
            samples=int(meta["samples"]),
            dt=float(meta["parameters"]["dt_s"]),
            zig_time_s=float(meta["zig_time_s"]),
            zig_index=int(meta["zig_index"]),
            meta=meta,
            own=own.astype(np.float64),
            tgt=tgt.astype(np.float64),
        )

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> Truth:
        own = np.array(
            [
                [s["timestamp_s"], s["x_m"], s["y_m"], s["course_rad"], s["speed_mps"]]
                for s in record["ownship"]["states"]
            ]
        )
        tgt = np.array(
            [
                [s["timestamp_s"], s["x_m"], s["y_m"], s["course_rad"], s["speed_mps"]]
                for s in record["target"]["states"]
            ]
        )
        return cls.from_block(record["metadata"], own, tgt)

    def row_index(self, timestamp_s: float) -> int:
        i = int(math.floor(timestamp_s / self.dt + 0.5))
        if not 0 <= i < self.samples:
            raise ValueError(f"scenario {self.index}: no truth at t={timestamp_s}")
        return i


def row_error(truth: Truth, row: dict[str, Any]) -> RowError:
    """gitma ``rowError``: a non-converged row scores +∞ on every metric and is gross."""
    i = truth.row_index(float(row["timestamp_s"]))
    t_since_zig = float(row["timestamp_s"]) - truth.zig_time_s
    if not row["converged"]:
        return RowError(t_since_zig, math.inf, math.inf, math.inf, math.inf, True, False)
    o = truth.own[i]
    t = truth.tgt[i]
    rng = math.hypot(t[1] - o[1], t[2] - o[2])
    range_rel = abs(float(row["range_m"]) - rng) / rng
    return RowError(
        t_since_zig_s=t_since_zig,
        range_rel=range_rel,
        course_deg=abs(rad_to_deg(angle_diff(float(row["course_rad"]), float(t[3])))),
        speed_kt=abs(mps_to_kt(float(row["speed_mps"]) - float(t[4]))),
        position_m=math.hypot(float(row["x_m"]) - t[1], float(row["y_m"]) - t[2]),
        gross=not (range_rel <= GROSS_RANGE_REL),
        converged=True,
    )
