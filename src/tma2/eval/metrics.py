"""Scoring prediction files against truth: metrics by slice and point, curves, efficiency.

Ported from gitma ``packages/eval/src/evaluate.ts`` (same buckets, points, slice order and
non-finite handling) with the Cramér–Rao bound and efficiency added per slice.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .errors import RowError, Truth, row_error
from .slices import slice_keys
from .stats import ascending, mean, median, percentile

METRIC_COLUMNS = [
    "estimator",
    "slice",
    "point",
    "n",
    "excluded",
    "range_rel_median",
    "range_rel_p90",
    "course_deg_median",
    "course_deg_p90",
    "speed_kt_median",
    "speed_kt_p90",
    "gross_error_rate",
    "non_converged_rate",
    "position_m_mean",
    "position_window_m_median",
    "position_window_m_p90",
    "crb_range_rel_median",
    "crb_course_deg_median",
    "crb_speed_kt_median",
    "efficiency_range",
    "efficiency_course",
    "efficiency_speed",
    "crb_singular_rate",
]
CURVE_COLUMNS = [
    "estimator",
    "t_since_zig_s",
    "n",
    "range_rel_median",
    "range_rel_p90",
    "course_deg_median",
    "speed_kt_median",
    "gross_error_rate",
    "non_converged_rate",
    "efficiency_range",
    "efficiency_speed",
]


@dataclass
class Bucket:
    errors: list[RowError] = field(default_factory=list)
    crb: list[tuple[float, float, float, bool]] = field(default_factory=list)
    excluded: int = 0
    window_means: list[float] = field(default_factory=list)


# Median of |N(0, 1)|: Φ⁻¹(0.75).
GAUSS_MEDIAN_ABS = 0.6744897501960817
_NO_BOUND = (math.nan, math.nan, math.nan, True)


def efficiency(pairs: list[tuple[float, float]]) -> float:
    """median_i(|e_i| / σ_i) / 0.6745 over rows with a regular, positive bound.

    Each error is normalised by its own row's bound before the median, so a slice that mixes
    rows with very different bounds (σ = 1° and 2°, near and far) is not biased the way
    median|e| / median σ is. An unbiased estimator at the bound with Gaussian errors scores 1;
    non-converged rows (error +∞) count as above any finite value, as in the error medians.
    """
    z = [e / s for e, s in pairs if s > 0 and math.isfinite(s)]
    return math.nan if not z else median(ascending(z)) / GAUSS_MEDIAN_ABS


def window_mean_position(errors: list[RowError]) -> float:
    ok = [e.position_m for e in errors if e.converged and math.isfinite(e.position_m)]
    return math.inf if not ok else mean(ok)


def _finite_only(r: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in r.items() if not isinstance(v, float) or math.isfinite(v)}


def _record(label: str, slc: str, point: str, b: Bucket) -> dict[str, Any]:
    n = len(b.errors)
    base: dict[str, Any] = {
        "estimator": label,
        "slice": slc,
        "point": point,
        "n": n,
        "excluded": b.excluded,
    }
    if n == 0:
        return base
    rr = ascending([e.range_rel for e in b.errors])
    cd = ascending([e.course_deg for e in b.errors])
    sk = ascending([e.speed_kt for e in b.errors])
    wm = ascending(b.window_means)
    rec: dict[str, Any] = {
        **base,
        "range_rel_median": median(rr),
        "range_rel_p90": percentile(rr, 0.9),
        "course_deg_median": median(cd),
        "course_deg_p90": percentile(cd, 0.9),
        "speed_kt_median": median(sk),
        "speed_kt_p90": percentile(sk, 0.9),
        "gross_error_rate": sum(1 for e in b.errors if e.gross) / n,
        "non_converged_rate": sum(1 for e in b.errors if not e.converged) / n,
        "position_m_mean": mean([e.position_m for e in b.errors if math.isfinite(e.position_m)]),
    }
    if wm.size:
        rec["position_window_m_median"] = median(wm)
        rec["position_window_m_p90"] = percentile(wm, 0.9)
    if b.crb:
        regular = [c for c in b.crb if not c[3]]
        rec["crb_singular_rate"] = 1 - len(regular) / len(b.crb)
        if regular:
            cr = median(ascending([c[0] for c in regular]))
            cc = median(ascending([c[1] for c in regular]))
            cs = median(ascending([c[2] for c in regular]))
            rec["crb_range_rel_median"] = cr
            rec["crb_course_deg_median"] = cc
            rec["crb_speed_kt_median"] = cs
            rows = [(e, c) for e, c in zip(b.errors, b.crb, strict=True) if not c[3]]
            rec["efficiency_range"] = efficiency([(e.range_rel, c[0]) for e, c in rows])
            rec["efficiency_course"] = efficiency([(e.course_deg, c[1]) for e, c in rows])
            rec["efficiency_speed"] = efficiency([(e.speed_kt, c[2]) for e, c in rows])
    return _finite_only(rec)


def _slice_order(keys: Iterable[str]) -> list[str]:
    ks = list(keys)
    return sorted(ks, key=lambda k: (k != "overall", k))


@dataclass
class PredictionSet:
    label: str
    estimator: str
    by_index: dict[int, dict[str, Any]]
    mode: str


@dataclass
class Evaluation:
    metrics: list[dict[str, Any]]
    curves: list[dict[str, Any]]


def evaluate(
    truths: Iterable[Truth],
    sets: list[PredictionSet],
    points: tuple[int, ...] = (300,),
    curve_step: int = 60,
    crb_lookup: Any = None,
) -> Evaluation:
    """``crb_lookup(truth, row_index) -> (sd_range_rel, sd_course_deg, sd_speed_kt, singular)``
    or None to skip efficiency."""
    buckets: dict[str, dict[str, dict[str, Bucket]]] = {}
    curve_rows: dict[str, dict[int, list[tuple[RowError, Any]]]] = {}

    def bucket(label: str, point: str, slc: str) -> Bucket:
        return buckets.setdefault(label, {}).setdefault(point, {}).setdefault(slc, Bucket())

    for s in truths:
        keys = slice_keys(s.meta)
        for st in sets:
            p = st.by_index.get(s.index)
            if p is None:
                raise ValueError(f"{st.label}: no prediction for scenario {s.index}")
            if not p["rows"]:
                raise ValueError(f"{st.label}: empty prediction for {s.index}")
            errs = [row_error(s, r) for r in p["rows"]]
            # With a lookup, a row it cannot bound counts as singular, so a bucket's errors and
            # bounds stay aligned row for row.
            crbs = [
                (crb_lookup(s, s.row_index(float(r["timestamp_s"]))) or _NO_BOUND)
                if crb_lookup
                else None
                for r in p["rows"]
            ]
            final_err = errs[-1]
            window = window_mean_position(errs)
            for k in keys:
                b = bucket(st.label, "final", k)
                b.errors.append(final_err)
                b.window_means.append(window)
                if crbs[-1] is not None:
                    b.crb.append(crbs[-1])
            if p["mode"] != "per_timestep":
                continue
            for sec in points:
                hit = next(
                    (
                        (e, c)
                        for e, c in zip(errs, crbs, strict=True)
                        if abs(e.t_since_zig_s - sec) < 1e-6
                    ),
                    None,
                )
                for k in keys:
                    b = bucket(st.label, f"zig+{sec}s", k)
                    if hit is None:
                        b.excluded += 1
                    else:
                        b.errors.append(hit[0])
                        if hit[1] is not None:
                            b.crb.append(hit[1])
            curves = curve_rows.setdefault(st.label, {})
            for e, c in zip(errs, crbs, strict=True):
                step = int(round(e.t_since_zig_s / curve_step)) * curve_step
                if abs(e.t_since_zig_s - step) > 1e-6:
                    continue
                curves.setdefault(step, []).append((e, c))

    metrics: list[dict[str, Any]] = []
    for label, by_point in buckets.items():
        for point, by_slice in by_point.items():
            for slc in _slice_order(by_slice):
                metrics.append(_record(label, slc, point, by_slice[slc]))
    curves_out: list[dict[str, Any]] = []
    for label, by_sec in curve_rows.items():
        for sec in sorted(by_sec):
            rows = by_sec[sec]
            errs = [e for e, _ in rows]
            rr = ascending([e.range_rel for e in errs])
            rec: dict[str, Any] = {
                "estimator": label,
                "t_since_zig_s": sec,
                "n": len(errs),
                "range_rel_median": median(rr),
                "range_rel_p90": percentile(rr, 0.9),
                "course_deg_median": median(ascending([e.course_deg for e in errs])),
                "speed_kt_median": median(ascending([e.speed_kt for e in errs])),
                "gross_error_rate": sum(1 for e in errs if e.gross) / len(errs),
                "non_converged_rate": sum(1 for e in errs if not e.converged) / len(errs),
            }
            regular = [(e, c) for e, c in rows if c is not None and not c[3]]
            if regular:
                rec["efficiency_range"] = efficiency([(e.range_rel, c[0]) for e, c in regular])
                rec["efficiency_speed"] = efficiency([(e.speed_kt, c[2]) for e, c in regular])
            curves_out.append(_finite_only(rec))
    return Evaluation(metrics=metrics, curves=curves_out)


def to_csv(columns: list[str], rows: list[dict[str, Any]]) -> str:
    """CSV with a fixed column order; missing and non-finite values are empty cells."""

    def cell(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return _js_num(v) if math.isfinite(v) else ""
        s = str(v)
        return '"' + s.replace('"', '""') + '"' if any(c in s for c in ',"\n') else s

    lines = [",".join(columns)]
    for r in rows:
        lines.append(",".join(cell(r.get(c)) for c in columns))
    return "\n".join(lines) + "\n"


def _js_num(v: float) -> str:
    from tma2.data.canonical import js_number

    return js_number(v)


__all__ = [
    "CURVE_COLUMNS",
    "METRIC_COLUMNS",
    "Evaluation",
    "PredictionSet",
    "evaluate",
    "to_csv",
    "np",
]
