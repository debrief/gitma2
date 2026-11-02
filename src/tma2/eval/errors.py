"""Per-row errors of an estimate against truth (gitma ``packages/eval/src/errors.ts``)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.references.lsq import angle_diff
from tma2.sim.geometry import mps_to_kt, rad_to_deg

GROSS_RANGE_REL = 0.5
PLAUSIBLE_MAX_RANGE_M = 100_000.0  # gitma's plausibility bounds (references/classical.py)
PLAUSIBLE_MAX_SPEED_MPS = 25.0

# Why a row counts as gross (spec 004 FR-008): no estimate (missing row, empty row, non-finite or
# implausible values), or a range error above 50%. ``lm_flag`` counts rows that are usable under
# the plausibility definition but carry ``converged = false`` (least squares' LM did not converge):
# reported, never gross under that definition.
CAUSES = ("missing", "implausible", "range_error_over_50pct")


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


def plausible_row(row: dict[str, Any]) -> bool:
    """The one convergence definition (spec 004 FR-008, R11): finite estimate fields, range in
    (0, 100 km] and speed ≤ 25 m/s, for every estimator. An empty row (no solution: range 0) and a
    physics-layer row flagged implausible both fail; least squares' LM flag is not consulted."""
    vals = [float(row[k]) for k in ("range_m", "course_rad", "speed_mps", "x_m", "y_m")]
    if not all(math.isfinite(v) for v in vals):
        return False
    rng, speed = vals[0], vals[2]
    return 0.0 < rng <= PLAUSIBLE_MAX_RANGE_M and speed <= PLAUSIBLE_MAX_SPEED_MPS


def row_error(truth: Truth, row: dict[str, Any], convergence: str = "flag") -> RowError:
    """gitma ``rowError``: a non-converged row scores +∞ on every metric and is gross.

    ``convergence`` = ``flag`` reads the row's ``converged`` (gitma, P0 and Gate 1 as registered);
    ``plausible`` applies :func:`plausible_row` (spec 004 and later gates)."""
    i = truth.row_index(float(row["timestamp_s"]))
    t_since_zig = float(row["timestamp_s"]) - truth.zig_time_s
    ok = bool(row["converged"]) if convergence == "flag" else plausible_row(row)
    if not ok:
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


def gross_cause(truth: Truth, row: dict[str, Any] | None) -> str | None:
    """Cause of a gross row under the plausibility definition, or None when not gross."""
    if row is None:
        return "missing"
    if not plausible_row(row):
        return "implausible"
    e = row_error(truth, row, "plausible")
    return "range_error_over_50pct" if e.gross else None


def gross_by_cause(truth_rows: list[tuple[Truth, dict[str, Any] | None]]) -> dict[str, int]:
    """Counts of gross rows by cause, plus ``lm_flag`` (usable rows flagged non-converged) and
    ``flag_gross`` (gross under the row's own ``converged`` flag, as Gate 1 registered it)."""
    out = {c: 0 for c in CAUSES} | {"lm_flag": 0, "flag_gross": 0, "rows": len(truth_rows)}
    for truth, row in truth_rows:
        cause = gross_cause(truth, row)
        if cause is not None:
            out[cause] += 1
        if row is not None and plausible_row(row) and not row["converged"]:
            out["lm_flag"] += 1
        if row is None or row_error(truth, row, "flag").gross:
            out["flag_gross"] += 1
    return out
