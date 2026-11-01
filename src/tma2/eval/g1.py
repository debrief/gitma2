"""Gate 1 scoring (spec 003 FR-020, SRD §5; decision record `Gate1Decision`).

Rows: σ = 1° scenarios of the test split; for range and course the row at zig + 5 min, for speed
the row at zig + 10 min (a scenario whose window ends first contributes no row for that metric).
Each estimator is read at those rows from its per-timestep predictions; a missing or
non-converged row scores +∞ and counts as gross. Intervals are scenario-clustered paired
bootstraps at the decision's level and resamples.

Checks (all must pass):

* ``ratio-<metric>``: median model ÷ median batch least squares; pass when the point and the
  whole interval are below 1.1; fail when the interval's lower bound is at or above 1.1.
* ``gross``: model gross rate − batch least squares' at the zig + 5 min rows; pass when the
  interval's upper bound is ≤ 0; fail when its lower bound is > 0.
* ``efficiency-<metric>``: the model's median(|e| ÷ bound sd) ÷ 0.6745 (full-window Cramér–Rao
  bound; singular bounds excluded); pass when the point and the interval's upper bound are
  ≤ 1.25; fail when the lower bound is above 1.25.

Anything else is inconclusive. The naive baseline, the tuned EKF and IMM and the oracle are
scored on the same rows and reported beside the gate, never gated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .bootstrap import (
    bootstrap_clustered_quantile_ratio,
    bootstrap_clustered_rate_difference,
)
from .errors import Truth, row_error
from .metrics import GAUSS_MEDIAN_ABS

GATE_S = {"range_rel": 300.0, "course_deg": 300.0, "speed_kt": 600.0}
RATIO_LIMIT = 1.1
EFFICIENCY_LIMIT = 1.25
SIGMA_1 = math.radians(1.0)
BOUND_FIELD = {
    "range_rel": "sd_range_rel",
    "course_deg": "sd_course_deg",
    "speed_kt": "sd_speed_kt",
}
LABEL = {"range_rel": "range", "course_deg": "course", "speed_kt": "speed"}

Preds = dict[int, dict[float, dict[str, Any]]]


@dataclass
class GateRow:
    index: int  # scenario index (the bootstrap cluster)
    k: int
    timestamp_s: float


@dataclass
class GateCheck:
    name: str
    result: str  # pass | fail | inconclusive
    value: float
    lo: float
    hi: float
    limit: float
    rows: int
    detail: str = ""


@dataclass
class Gate1Result:
    checks: list[GateCheck]
    reported: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def result(self) -> str:
        results = {c.result for c in self.checks}
        if "fail" in results:
            return "fail"
        if results == {"pass"}:
            return "pass"
        return "inconclusive"


def gate_rows(truths: list[Truth], metric: str) -> list[GateRow]:
    """σ = 1° scenarios with a row ``GATE_S[metric]`` after the zig."""
    out = []
    for t in truths:
        if abs(float(t.meta["parameters"]["noise_sigma_rad"]) - SIGMA_1) > 1e-6:
            continue
        k = t.zig_index + int(round(GATE_S[metric] / t.dt))
        if k < t.samples:
            out.append(GateRow(t.index, k, float(t.own[k, 0])))
    return out


def errors_at(
    truths: dict[int, Truth], rows: list[GateRow], preds: Preds, metric: str
) -> tuple[np.ndarray, np.ndarray]:
    """(error, gross) per row; +∞ and gross where the estimator has no converged row."""
    err = np.empty(len(rows))
    gross = np.zeros(len(rows), dtype=np.int64)
    for i, g in enumerate(rows):
        r = preds.get(g.index, {}).get(g.timestamp_s)
        if r is None or not r["converged"]:
            err[i] = math.inf
            gross[i] = 1
            continue
        e = row_error(truths[g.index], r)
        err[i] = getattr(e, metric)
        gross[i] = int(e.gross)
    return err, gross


def _ratio_check(
    name: str, a: np.ndarray, b: np.ndarray, cluster: np.ndarray, level: float, resamples: int
) -> GateCheck:
    iv = bootstrap_clustered_quantile_ratio(a, b, cluster, 0.5, level, resamples)
    if iv.ratio < RATIO_LIMIT and iv.hi < RATIO_LIMIT:
        res = "pass"
    elif iv.lo >= RATIO_LIMIT:
        res = "fail"
    else:
        res = "inconclusive"
    return GateCheck(name, res, iv.ratio, iv.lo, iv.hi, RATIO_LIMIT, len(a))


def _efficiency_check(
    name: str, err: np.ndarray, sd: np.ndarray, cluster: np.ndarray, level: float, resamples: int
) -> GateCheck:
    keep = np.isfinite(sd) & (sd > 0)
    z = np.abs(err[keep]) / sd[keep]
    if z.size == 0:
        return GateCheck(name, "inconclusive", math.nan, math.nan, math.nan, EFFICIENCY_LIMIT, 0)
    iv = bootstrap_clustered_quantile_ratio(
        z / GAUSS_MEDIAN_ABS, np.ones_like(z), cluster[keep], 0.5, level, resamples
    )
    if iv.ratio <= EFFICIENCY_LIMIT and iv.hi <= EFFICIENCY_LIMIT:
        res = "pass"
    elif iv.lo > EFFICIENCY_LIMIT:
        res = "fail"
    else:
        res = "inconclusive"
    return GateCheck(name, res, iv.ratio, iv.lo, iv.hi, EFFICIENCY_LIMIT, int(z.size))


def score(
    truths: list[Truth],
    model: Preds,
    least_squares: Preds,
    bounds: dict[tuple[int, int], Any],
    others: dict[str, Preds],
    level: float = 0.95,
    resamples: int = 2000,
) -> Gate1Result:
    """The gate's checks for ``model`` against ``least_squares``; ``others`` (naive, EKF, IMM,
    oracle) are reported on the same rows. ``bounds[(index, k)]`` is a CrbRow."""
    by_index = {t.index: t for t in truths}
    checks: list[GateCheck] = []
    reported: dict[str, dict[str, Any]] = {}
    for metric in ("range_rel", "course_deg", "speed_kt"):
        rows = gate_rows(truths, metric)
        cluster = np.array([g.index for g in rows], dtype=np.int64)
        em, gm = errors_at(by_index, rows, model, metric)
        el, gl = errors_at(by_index, rows, least_squares, metric)
        label = LABEL[metric]
        checks.append(_ratio_check(f"ratio-{label}", em, el, cluster, level, resamples))
        if metric == "range_rel":
            d = bootstrap_clustered_rate_difference(gm, gl, cluster, level, resamples)
            res = "pass" if d.hi <= 0 else "fail" if d.lo > 0 else "inconclusive"
            checks.append(
                GateCheck(
                    "gross",
                    res,
                    d.difference,
                    d.lo,
                    d.hi,
                    0.0,
                    len(rows),
                    f"model {gm.mean():.4f}, least squares {gl.mean():.4f}",
                )
            )
        sd = np.array(
            [
                getattr(bounds[(g.index, g.k)], BOUND_FIELD[metric])
                if not bounds[(g.index, g.k)].singular
                else math.nan
                for g in rows
            ]
        )
        checks.append(_efficiency_check(f"efficiency-{label}", em, sd, cluster, level, resamples))
        for name, preds in {"least_squares": least_squares, **others}.items():
            e, g = errors_at(by_index, rows, preds, metric)
            rec = reported.setdefault(name, {})
            iv = bootstrap_clustered_quantile_ratio(e, el, cluster, 0.5, level, resamples)
            rec[f"median-{label}"] = float(np.median(e))
            rec[f"ratio-{label}"] = {"ratio": iv.ratio, "lo": iv.lo, "hi": iv.hi}
            keep = np.isfinite(sd) & (sd > 0)
            z = np.abs(e[keep]) / sd[keep]
            rec[f"efficiency-{label}"] = float(np.median(z) / GAUSS_MEDIAN_ABS) if z.size else None
            if metric == "range_rel":
                rec["gross"] = float(g.mean())
        rec_m = reported.setdefault("model", {})
        rec_m[f"median-{label}"] = float(np.median(em))
        if metric == "range_rel":
            rec_m["gross"] = float(gm.mean())
    return Gate1Result(checks, reported)
