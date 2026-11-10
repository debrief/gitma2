"""The pre-registered readings of the regressor control (spec 012 FR-021, FR-022, research R6).

Inputs are one scoring run's per-row errors [rows, 3] (relative range, course °, speed kt) for
every estimator, the Cramér–Rao bound's standard deviations on the same rows, and row labels.

**Held course** (settled rows on which no target change has begun): efficiency
median(|e| / σ) / 0.6745 for range, course and speed, with a scenario-clustered interval.
*Reaches the bound*: all three intervals lie wholly below ``reach``. *Flat floor*: for some
quantity the interval lies wholly above ``floor`` and its efficiency in the best geometry
quartile is not below that in the worst. Otherwise *partial*. Geometry quartiles are of the
bound's own relative range sd (small = well observed).

**After manoeuvres** (rows on which a change has begun): paired differences of medians,
regressor − reference, with clustered intervals, overall and by quartile of true range.
"""

from __future__ import annotations

from typing import Any

import numpy as np

COLS = ("range", "course_deg", "speed_kt")
Q = 0.6744897501960817


def efficiency(e: np.ndarray, sd: np.ndarray) -> float:
    ok = np.isfinite(sd) & (sd > 0) & np.isfinite(e)
    if not ok.any():
        return float("nan")
    return float(np.median(np.abs(e[ok]) / sd[ok])) / Q


def _draws(ordinal: np.ndarray, n: int, seed: int) -> list[np.ndarray]:
    uniq = np.unique(ordinal)
    rows = [np.flatnonzero(ordinal == u) for u in uniq]
    rng = np.random.default_rng(seed)
    return [
        np.concatenate([rows[i] for i in rng.integers(0, uniq.size, uniq.size)]) for _ in range(n)
    ]


def _interval(vals: list[float], level: float) -> tuple[float, float]:
    a = np.asarray(vals, dtype=np.float64)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float("nan"), float("nan")
    lo, hi = np.quantile(a, [(1 - level) / 2, (1 + level) / 2])
    return float(lo), float(hi)


def held_course(
    e: np.ndarray,
    sd: np.ndarray,
    ordinal: np.ndarray,
    held: np.ndarray,
    reach: float = 1.25,
    floor: float = 2.0,
    level: float = 0.95,
    resamples: int = 2000,
    seed: int = 12,
) -> dict[str, Any]:
    idx = np.flatnonzero(held)
    out: dict[str, Any] = {"rows": int(idx.size), "scenarios": int(np.unique(ordinal[idx]).size)}
    if idx.size == 0:
        return {**out, "reading": "no rows"}
    ee, ss, oo = e[idx], sd[idx], ordinal[idx]
    draws = _draws(oo, resamples, seed)
    geo = ss[:, 0]
    okg = np.isfinite(geo) & (geo > 0)
    cuts = np.quantile(geo[okg], [0.25, 0.5, 0.75]) if okg.any() else np.zeros(3)
    band = np.where(okg, np.searchsorted(cuts, geo, side="right"), -1)  # 0 best … 3 worst
    reaches, floors = [], []
    for c, name in enumerate(COLS):
        pt = efficiency(ee[:, c], ss[:, c])
        lo, hi = _interval([efficiency(ee[d, c], ss[d, c]) for d in draws], level)
        by = [efficiency(ee[band == b, c], ss[band == b, c]) for b in range(4)]
        out[name] = {"efficiency": pt, "lo": lo, "hi": hi, "by_geometry_best_to_worst": by}
        reaches.append(hi < reach)
        floors.append(lo > floor and not by[0] < by[3])
    out["reading"] = "reaches" if all(reaches) else "floor" if any(floors) else "partial"
    out["thresholds"] = {"reach": reach, "floor": floor, "level": level}
    return out


def paired_difference(
    a: np.ndarray,
    b: np.ndarray,
    ordinal: np.ndarray,
    rows: np.ndarray,
    level: float = 0.95,
    resamples: int = 2000,
    seed: int = 13,
) -> dict[str, Any]:
    """median(a) − median(b) over ``rows`` (infinite errors count as failures in both medians)."""
    idx = np.flatnonzero(rows)
    if idx.size == 0:
        return {"rows": 0}
    aa, bb, oo = a[idx], b[idx], ordinal[idx]

    def stat(d: np.ndarray) -> float:
        return float(np.median(aa[d]) - np.median(bb[d]))

    every = np.arange(idx.size)
    lo, hi = _interval([stat(d) for d in _draws(oo, resamples, seed)], level)
    return {
        "rows": int(idx.size),
        "a_median": float(np.median(aa)),
        "b_median": float(np.median(bb)),
        "difference": stat(every),
        "lo": lo,
        "hi": hi,
    }


def after_manoeuvres(
    errs: dict[str, np.ndarray],
    regressor: str,
    references: list[str],
    ordinal: np.ndarray,
    manoeuvring: np.ndarray,
    range_m: np.ndarray,
    level: float = 0.95,
    resamples: int = 2000,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    cuts = np.quantile(range_m[manoeuvring], [0.25, 0.5, 0.75]) if manoeuvring.any() else None
    for ref in references:
        a, b = errs[regressor], errs[ref]
        both = manoeuvring & np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
        rec: dict[str, Any] = {}
        for c, name in enumerate(COLS):
            rec[name] = {
                "all_rows": paired_difference(
                    a[:, c], b[:, c], ordinal, manoeuvring, level, resamples
                ),
                "rows_both_answer": paired_difference(
                    a[:, c], b[:, c], ordinal, both, level, resamples
                ),
            }
        # operational: metres of range error (relative error × true range)
        rec["range_m"] = paired_difference(
            a[:, 0] * range_m, b[:, 0] * range_m, ordinal, both, level, resamples
        )
        if cuts is not None:
            q = np.searchsorted(cuts, range_m, side="right")
            rec["range_by_true_range_quartile"] = [
                paired_difference(
                    a[:, 0], b[:, 0], ordinal, manoeuvring & (q == i), level, resamples
                )
                for i in range(4)
            ]
        out[ref] = rec
    return out
