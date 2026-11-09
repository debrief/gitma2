"""Headroom statistics and Gate H's checks (spec 010 research R6–R8).

``R``: one estimator's median error over another's, minus 1, on the same rows, with a paired,
scenario-clustered bootstrap interval. The gated R is the robust control against the attainable
ceiling, both on the true segmentation (H-c). A row an estimator does not answer is an infinite
error, as at Gate S; every comparison is also given on the rows every estimator answers.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.eval.bootstrap import BOOTSTRAP_RESAMPLES, bootstrap_clustered_statistic
from tma2.segment.score import efficiency_of, lower_median

COLS = ("range", "course", "speed")
LEVEL = 0.95
KT = 1852.0 / 3600.0
SETTLED_RANGE_REL = 0.10
"""Research R8: a solution is settled at a scored time when its range error is within 10% there
and at every later scored time."""


def ratio(cols: dict[str, np.ndarray], a: str, b: str, col: int) -> float:
    """median(a) / median(b) − 1 on column ``col`` (NaN when the denominator is 0 or ∞)."""
    ma, mb = lower_median(cols[a][:, col]), lower_median(cols[b][:, col])
    if not np.isfinite(mb) or mb <= 0.0:
        return float("nan")
    return float(ma / mb - 1.0)


def closed(cols: dict[str, np.ndarray], base: str, fix: str, ceiling: str, col: int) -> float:
    """Share of the base-to-ceiling gap in the median that ``fix`` closes."""
    mb = lower_median(cols[base][:, col])
    mf = lower_median(cols[fix][:, col])
    mc = lower_median(cols[ceiling][:, col])
    if not np.isfinite(mb - mc) or mb - mc == 0.0:
        return float("nan")
    return float((mb - mf) / (mb - mc))


def interval(
    cols: dict[str, np.ndarray],
    cluster: np.ndarray,
    stat: Any,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, float]:
    iv = bootstrap_clustered_statistic(cols, cluster, stat, LEVEL, resamples)
    return {"value": iv.value, "lo": iv.lo, "hi": iv.hi}


def comparison(
    errs: dict[str, np.ndarray],
    cluster: np.ndarray,
    a: str,
    b: str,
    mask: np.ndarray | None = None,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    """R of ``a`` against ``b`` for range, course and speed, each with its interval."""
    m = np.ones(cluster.shape[0], dtype=bool) if mask is None else mask
    cols = {a: errs[a][m], b: errs[b][m]}
    out: dict[str, Any] = {"numerator": a, "denominator": b, "rows": int(m.sum())}
    for c, name in enumerate(COLS):
        out[name] = interval(cols, cluster[m], lambda x, c=c: ratio(x, a, b, c), resamples)
    return out


def summary(e: np.ndarray, bound: np.ndarray | None, settled: np.ndarray) -> dict[str, Any]:
    """Medians, P90, answered share and (with a bound) efficiency on settled rows."""
    out: dict[str, Any] = {"answered": float(np.isfinite(e[:, 0]).mean())}
    for c, name in enumerate(COLS):
        out[f"median_{name}"] = lower_median(e[:, c])
        out[f"p90_{name}"] = float(np.quantile(np.where(np.isfinite(e[:, c]), e[:, c], 1e300), 0.9))
    if bound is not None:
        for c, name in enumerate(COLS):
            out[f"efficiency_settled_{name}"] = efficiency_of(e[settled, c], bound[settled, c])
    return out


def operational(
    e: np.ndarray, true_range_m: np.ndarray, cluster: np.ndarray, minute: np.ndarray
) -> dict[str, Any]:
    """The same errors in operational units (research R8): metres, degrees, knots, and the share
    of engagements with a settled solution by each scored time."""
    metres = e[:, 0] * true_range_m
    out: dict[str, Any] = {
        "median_range_m": lower_median(metres),
        "median_course_deg": lower_median(e[:, 1]),
        "median_speed_kt": lower_median(e[:, 2]),
    }
    by: dict[int, dict[int, bool]] = {}
    for j, mn, err in zip(cluster.tolist(), minute.tolist(), e[:, 0].tolist(), strict=True):
        by.setdefault(j, {})[mn] = bool(np.isfinite(err) and err <= SETTLED_RANGE_REL)
    for mn in sorted(set(minute.tolist())):
        have = [v for v in by.values() if mn in v]
        ok = [all(good for m2, good in v.items() if m2 >= mn) for v in have]
        out[f"settled_by_{mn}min"] = float(np.mean(ok)) if ok else float("nan")
    return out


def headroom(
    errs: dict[str, np.ndarray],
    cluster: np.ndarray,
    settled: np.ndarray,
    true_range_m: np.ndarray,
    minute: np.ndarray,
    bound: np.ndarray | None,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    """Everything ``headroom.json`` holds for one condition's scoring."""
    names = sorted(errs)
    out: dict[str, Any] = {
        "rows": int(cluster.shape[0]),
        "scenarios": int(np.unique(cluster).shape[0]),
        "estimators": {n: summary(errs[n], bound, settled) for n in names},
        "operational": {n: operational(errs[n], true_range_m, cluster, minute) for n in names},
    }
    answered = np.ones(cluster.shape[0], dtype=bool)
    for n in names:
        answered &= np.isfinite(errs[n][:, 0])
    out["rows_all_answer"] = int(answered.sum())
    pairs = {
        # H-c: what knowing the error model is worth after the classical fixes
        "R": ("robust@truth", "attainable@truth"),
        # before the classical fixes
        "R_nominal": ("nominal@truth", "attainable@truth"),
        # H-b on mismatch-off data: the control's cost where nothing is wrong
        "robust_over_nominal": ("robust@truth", "nominal@truth"),
        # what the outlier flags are worth beyond the model
        "attainable_over_realisation": ("attainable@truth", "realisation@truth"),
        # on the classical segmentation
        "R_c2": ("robust@c2", "attainable@truth"),
        "R_c2_nominal": ("nominal@c2", "attainable@truth"),
        "robust_over_nominal_c2": ("robust@c2", "nominal@c2"),
    }
    for key, (a, b) in pairs.items():
        if a in errs and b in errs:
            out[key] = comparison(errs, cluster, a, b, None, resamples)
            out[f"{key}_all_answer"] = comparison(errs, cluster, a, b, answered, resamples)
    trio = ("nominal@truth", "robust@truth", "attainable@truth")
    if all(n in errs for n in trio):
        cols = {n: errs[n] for n in trio}
        out["closed_by_robust"] = {
            name: interval(cols, cluster, lambda x, c=c: closed(x, *trio, c), resamples)
            for c, name in enumerate(COLS)
        }
    return out


def soundness(
    primary: dict[str, Any], off: dict[str, Any], band: tuple[float, float], tolerance: float
) -> dict[str, Any]:
    """H-a and H-b (research R7) from the primary and the mismatch-off ``headroom.json``."""
    eff = primary["estimators"]["attainable@truth"].get("efficiency_settled_range")
    h_a = eff is not None and band[0] <= eff <= band[1]
    rb = off["robust_over_nominal"]["range"]
    h_b = rb["hi"] <= tolerance - 1.0
    return {
        "H-a": {"efficiency_settled_range": eff, "band": list(band), "pass": bool(h_a)},
        "H-b": {**rb, "limit": tolerance - 1.0, "pass": bool(h_b)},
    }


def verdict(primary: dict[str, Any], threshold: float) -> dict[str, Any]:
    """H-c: material, not material or inconclusive from R on the primary condition."""
    r = primary["R"]["range"]
    if r["lo"] > threshold:
        v = "material"
    elif r["hi"] < threshold:
        v = "not_material"
    else:
        v = "inconclusive"
    return {"H-c": {**r, "threshold": threshold, "verdict": v}}
