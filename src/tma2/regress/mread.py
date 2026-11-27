"""Paired readings of the regressor against a control under mismatch (spec 037 research R6).

Inputs are one scoring run's per-row absolute errors [rows, 3] (relative range, course °, speed
kt) per estimator, with each row's scenario ordinal. A system's error on a scenario is the
median over the rows that both sides of a comparison answer; the paired statistic is the
per-scenario ratio control ÷ system (above 1: the system is better), summarised by its geometric
mean with a scenario bootstrap, its median and the shares better, twice as good and twice as
bad. Scenarios with no common row, or a zero median, are left out and counted.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

COLS = ("range", "course_deg", "speed_kt")
Q = 0.6744897501960817
Z95 = 1.959963984540054


def scenario_log_ratio(
    ctl: np.ndarray, sys: np.ndarray, ordinal: np.ndarray, rows: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray, int]:
    """(scenario ordinals, ln(median control ÷ median system), scenarios left out)."""
    ok = np.isfinite(ctl) & np.isfinite(sys)
    if rows is not None:
        ok &= rows
    every = np.unique(ordinal if rows is None else ordinal[rows])
    ids, out = [], []
    for u in np.unique(ordinal[ok]):
        m = ok & (ordinal == u)
        a, b = float(np.median(ctl[m])), float(np.median(sys[m]))
        if a > 0 and b > 0:
            ids.append(int(u))
            out.append(math.log(a / b))
    return np.array(ids, dtype=np.int64), np.array(out), int(every.size - len(ids))


def summarise(
    lr: np.ndarray, level: float = 0.95, resamples: int = 2000, seed: int = 37
) -> dict[str, Any]:
    """Geometric mean of the ratios with a bootstrap over scenarios, and the distribution."""
    n = int(lr.size)
    if n == 0:
        return {"scenarios": 0, "outcome": "no scenarios"}
    rng = np.random.default_rng(seed)
    means = lr[rng.integers(0, n, (resamples, n))].mean(axis=1)
    lo, hi = np.quantile(means, [(1 - level) / 2, (1 + level) / 2])
    gm, lo, hi = math.exp(float(lr.mean())), math.exp(float(lo)), math.exp(float(hi))
    return {
        "scenarios": n,
        "ratio": gm,
        "lo": lo,
        "hi": hi,
        "median_ratio": math.exp(float(np.median(lr))),
        "share_better": float(np.mean(lr > 0)),
        "share_twice_as_good": float(np.mean(lr > math.log(2.0))),
        "share_twice_as_bad": float(np.mean(lr < -math.log(2.0))),
        "outcome": "better" if lo > 1 else "worse" if hi < 1 else "not separated",
    }


def paired(
    errs: dict[str, np.ndarray],
    control: str,
    systems: list[str],
    ordinal: np.ndarray,
    rows: np.ndarray | None = None,
    resamples: int = 2000,
) -> dict[str, Any]:
    """control ÷ each system and control ÷ the systems pooled (the mean log ratio over the
    systems, on scenarios all of them share), for range, course and speed."""
    out: dict[str, Any] = {}
    for c, col in enumerate(COLS):
        per: dict[str, Any] = {}
        logs: list[dict[int, float]] = []
        for s in systems:
            ids, lr, left = scenario_log_ratio(errs[control][:, c], errs[s][:, c], ordinal, rows)
            per[s] = {**summarise(lr, resamples=resamples), "left_out": left}
            logs.append(dict(zip(ids.tolist(), lr.tolist(), strict=True)))
        if len(systems) > 1:
            common = sorted(set.intersection(*(set(d) for d in logs))) if logs else []
            pooled = np.array([np.mean([d[u] for d in logs]) for u in common])
            per["pooled"] = summarise(pooled, resamples=resamples)
        out[col] = per
    return out


def system_summary(
    e: np.ndarray, ordinal: np.ndarray, bound: np.ndarray | None, rows: np.ndarray | None = None
) -> dict[str, Any]:
    """Per system: the share of rows answered, the row median (a missing row counts as a
    failure), the median over scenarios of the scenario median, efficiency against the bound."""
    sel = np.ones(e.shape[0], dtype=bool) if rows is None else rows
    out: dict[str, Any] = {"rows": int(sel.sum())}
    fin = np.isfinite(e).all(axis=1)
    out["answered"] = float(fin[sel].mean()) if sel.any() else math.nan
    for c, col in enumerate(COLS):
        v = e[sel, c]
        ok = sel & np.isfinite(e[:, c])
        meds = [float(np.median(e[ok & (ordinal == u), c])) for u in np.unique(ordinal[ok])]
        rec = {
            "row_median": float(np.median(v)) if v.size else math.nan,
            "scenario_median": float(np.median(meds)) if meds else math.nan,
        }
        if bound is not None:
            b = bound[:, c]
            m = ok & np.isfinite(b) & (b > 0)
            rec["efficiency"] = float(np.median(e[m, c] / b[m])) / Q if m.any() else math.nan
        out[col] = rec
    return out


def coverage(
    hit: np.ndarray,
    z: np.ndarray,
    ordinal: np.ndarray,
    level: float = 0.95,
    resamples: int = 2000,
    seed: int = 38,
) -> dict[str, Any]:
    """Coverage of stated intervals over rows that state one (``hit`` NaN: none stated), with a
    scenario bootstrap; ``z`` is |error| ÷ the stated sd, whose median ÷ 0.6745 is 1 when the
    statement is honest in scale."""
    ok = np.isfinite(hit)
    n = int(ok.sum())
    out: dict[str, Any] = {"rows": n, "stated_share": float(ok.mean()) if ok.size else math.nan}
    if n == 0:
        return out
    h, o = hit[ok], ordinal[ok]
    uniq, inv = np.unique(o, return_inverse=True)
    num = np.bincount(inv, weights=h, minlength=uniq.size)
    den = np.bincount(inv, minlength=uniq.size).astype(np.float64)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, uniq.size, (resamples, uniq.size))
    draws = num[pick].sum(axis=1) / den[pick].sum(axis=1)
    lo, hi = np.quantile(draws, [(1 - level) / 2, (1 + level) / 2])
    zz = z[ok & np.isfinite(z)]
    out |= {
        "scenarios": int(uniq.size),
        "coverage": float(h.mean()),
        "lo": float(lo),
        "hi": float(hi),
        "normalised_error_median": float(np.median(zz)) / Q if zz.size else math.nan,
    }
    return out


def interval_rows(
    stated: dict[tuple[int, int], dict[str, float]],
    ordinal: np.ndarray,
    ks: np.ndarray,
    e: np.ndarray,
    true_range: np.ndarray,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Per quantity (hit, z) over scored rows from the rows' stated intervals. ``stated`` maps
    (ordinal, k) to a prediction row's fields. Speed errors are in knots; the row's in m/s."""
    kt = 3600.0 / 1852.0
    n = ordinal.size
    out = {c: (np.full(n, np.nan), np.full(n, np.nan)) for c in COLS}
    for q in range(n):
        x = stated.get((int(ordinal[q]), int(ks[q])))
        if x is None or not np.isfinite(e[q]).all():
            continue
        w = x.get("range_ratio_q95")
        if w is not None and w > 0:
            d = abs(math.log(max(float(x["range_m"]), 1e-9) / true_range[q]))
            out["range"][0][q], out["range"][1][q] = float(d <= w), d / (w / Z95)
        a = x.get("course_arc_rad")
        if a is not None and a > 0:
            d = math.radians(float(e[q, 1]))
            out["course_deg"][0][q], out["course_deg"][1][q] = float(d <= a), d / (a / Z95)
        s = x.get("speed_q95_mps")
        if s is not None and s > 0:
            d = float(e[q, 2]) / kt
            out["speed_kt"][0][q], out["speed_kt"][1][q] = float(d <= s), d / (s / Z95)
    return out


def row_terms(
    stated: dict[tuple[int, int], dict[str, float]],
    ordinal: np.ndarray,
    ks: np.ndarray,
    e: np.ndarray,
    true_range: np.ndarray,
) -> dict[str, np.ndarray]:
    """Per scored row, for the uncertainty readings: the estimator's own range estimate, its
    errors in the intervals' units (|ln range ratio|, course rad, speed m/s) and its stated 95%
    half-widths (NaN where none is stated). Rows the estimator does not answer are NaN."""
    kt = 3600.0 / 1852.0
    n = ordinal.size
    est = np.full(n, np.nan)
    err = np.full((n, 3), np.nan)
    half = np.full((n, 3), np.nan)
    for q in range(n):
        x = stated.get((int(ordinal[q]), int(ks[q])))
        if x is None or not np.isfinite(e[q]).all():
            continue
        est[q] = float(x["range_m"])
        err[q] = (
            abs(math.log(max(est[q], 1e-9) / true_range[q])),
            math.radians(float(e[q, 1])),
            float(e[q, 2]) / kt,
        )
        for c, key in enumerate(("range_ratio_q95", "course_arc_rad", "speed_q95_mps")):
            w = x.get(key)
            if w is not None and w > 0:
                half[q, c] = float(w)
    return {"est_range_m": est, "err": err, "half": half}


def winkler(err: np.ndarray, half: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Interval score of a symmetric interval of half-width ``half`` about the estimate."""
    out: np.ndarray = 2.0 * half + (2.0 / alpha) * np.maximum(err - half, 0.0)
    return out


def fit_scale(err: np.ndarray, half: np.ndarray, level: float = 0.95) -> float:
    """The multiplier of the stated half-widths that makes them cover ``level`` of these rows."""
    ok = np.isfinite(err) & np.isfinite(half) & (half > 0)
    return float(np.quantile(err[ok] / half[ok], level))


def fit_temperature(est: np.ndarray, err: np.ndarray, level: float = 0.95) -> dict[str, Any]:
    """The control: one half-width per quantity and per third of the estimator's own range
    estimate, covering ``level`` of these rows. It reads no truth when applied."""
    ok = np.isfinite(est) & np.isfinite(err).all(axis=1)
    cuts = np.quantile(est[ok], [1 / 3, 2 / 3])
    band = np.searchsorted(cuts, est, side="right")
    widths = [
        [float(np.quantile(err[ok & (band == b), c], level)) for c in range(3)] for b in range(3)
    ]
    return {"cuts_m": [float(c) for c in cuts], "half_widths": widths, "level": level}


def temperature_half(temp: dict[str, Any], est: np.ndarray) -> np.ndarray:
    """[rows, 3] the control's half-widths for rows with these range estimates."""
    band = np.searchsorted(np.asarray(temp["cuts_m"]), np.nan_to_num(est), side="right")
    out: np.ndarray = np.asarray(temp["half_widths"])[band]
    return out


def score_ratio(
    a: np.ndarray, b: np.ndarray, ordinal: np.ndarray, resamples: int = 2000, seed: int = 39
) -> dict[str, Any]:
    """mean(a) ÷ mean(b) over rows where both are finite, with an engagement bootstrap; "better"
    (for a) if the interval lies wholly below 1."""
    ok = np.isfinite(a) & np.isfinite(b)
    if not ok.any():
        return {"rows": 0}
    uniq, inv = np.unique(ordinal[ok], return_inverse=True)
    sa = np.bincount(inv, weights=a[ok], minlength=uniq.size)
    sb = np.bincount(inv, weights=b[ok], minlength=uniq.size)
    pick = np.random.default_rng(seed).integers(0, uniq.size, (resamples, uniq.size))
    draws = sa[pick].sum(axis=1) / sb[pick].sum(axis=1)
    lo, hi = (float(v) for v in np.quantile(draws, [0.025, 0.975]))
    return {
        "rows": int(ok.sum()),
        "scenarios": int(uniq.size),
        "a_mean": float(a[ok].mean()),
        "b_mean": float(b[ok].mean()),
        "ratio": float(sa.sum() / sb.sum()),
        "lo": lo,
        "hi": hi,
        "outcome": "better" if hi < 1 else "worse" if lo > 1 else "not separated",
    }
