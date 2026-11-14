"""Readings of spec 018 from ``run6`` shards: study L's readings of the standing control
(``study4``) and, beside them, what a manoeuvre prior that adapts to the period and a
hedged track are worth.

* Paired per-period comparisons in **range, course and speed**, each with its period count.
* The adaptive control's gain as a share of the gain of the search told the true statistics.
* Each comparison **by kind of period**: whether the standing control misses a true
  manoeuvre the bearings show (detectability at least the threshold, at the match
  tolerance), and by tercile of the period's median bound.
* Manoeuvres missed and false at three tolerances (``study4``'s counts), periods with any
  false manoeuvre, targets with one manoeuvre called quiet.
* The inferred rate against the split.
* The hedged track's stated spread: the share of rows whose true range lies within one and
  two stated sds of the mixture's mean range, overall and by number of true manoeuvres.

Conditions read **cost** (paired ratios of period error), never counts alone.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .score import UNDETERMINED, _period_medians
from .study import gain_share, paired, wilson
from .study3 import whole_true
from .study4 import study_split4
from .study5 import found_flags

QUANTITIES = ("range", "course", "speed")
MIN_PERIODS = 5


def medians3(arr: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    """(period ids, per system [P, 3] period medians of range, course and speed error over
    determined rows, [P] the period's median bound on relative range)."""
    bound = arr["bound"].astype(np.float64)
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    ids: np.ndarray = np.zeros(0, dtype=np.int64)
    med: dict[str, np.ndarray] = {}
    for k in sorted(arr):
        if k.startswith("err_"):
            ids, m = _period_medians(arr[k].astype(np.float64), arr["period"], det)
            med[k[4:]] = m[:, :3]
    pb = np.array([np.median(bound[det & (arr["period"] == i), 0]) for i in ids])
    return ids, med, pb


def pair3(
    med: dict[str, np.ndarray], a: str, b: str, keep: np.ndarray | None = None
) -> dict[str, Any] | None:
    """a ÷ b for each quantity on the periods where both have a finite median (and ``keep``)."""
    if a not in med or b not in med:
        return None
    out: dict[str, Any] = {}
    for q, name in enumerate(QUANTITIES):
        ok = np.isfinite(med[a][:, q]) & np.isfinite(med[b][:, q])
        ok &= (med[a][:, q] > 0) & (med[b][:, q] > 0)
        if keep is not None:
            ok &= keep
        if int(ok.sum()) >= MIN_PERIODS:
            out[name] = paired(med[a][ok, q], med[b][ok, q])
    return out or None


def control_misses(
    periods: list[dict[str, Any]], control: str, threshold: float, tol: float
) -> dict[int, bool]:
    """Per period ordinal: the control's history lacks a whole true manoeuvre whose
    detectability is at least ``threshold`` (matched within ``tol``)."""
    out: dict[int, bool] = {}
    for r in periods:
        h = (r.get("histories") or {}).get(control)
        if h is None or "detectability" not in r:
            continue
        flags = found_flags(r["true"], h["spans"], tol)
        out[int(r["ordinal"])] = any(
            (not c) and d >= threshold and not f
            for d, c, f in zip(r["detectability"], r["true_cut"], flags, strict=True)
        )
    return out


def kinds_of_period(
    ids: np.ndarray, bound: np.ndarray, misses: dict[int, bool]
) -> dict[str, np.ndarray]:
    """Masks over ``ids``: the control misses a detectable manoeuvre or not; bound terciles."""
    miss = np.array([misses.get(int(i), False) for i in ids], dtype=bool)
    known = np.array([int(i) in misses for i in ids], dtype=bool)
    out = {"control_misses": miss & known, "control_finds_all": ~miss & known}
    fin = np.isfinite(bound)
    if int(fin.sum()) >= 3:
        lo, hi = np.quantile(bound[fin], [1 / 3, 2 / 3])
        out["bound_tight"] = fin & (bound <= lo)
        out["bound_middle"] = fin & (bound > lo) & (bound <= hi)
        out["bound_loose"] = fin & (bound > hi)
    return out


def coverage(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], hedge: str, levels: list[float]
) -> dict[str, Any]:
    """Share of determined rows whose true range is within k stated sds of the mixture's
    mean range, for each k; overall and by the period's number of whole true manoeuvres."""
    if f"spread_{hedge}" not in arr:
        return {}
    bound = arr["bound"].astype(np.float64)
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    mean = arr[f"hrange_{hedge}"].astype(np.float64)
    sd = arr[f"spread_{hedge}"].astype(np.float64)
    true = arr["true_range"].astype(np.float64)
    ok = det & np.isfinite(mean) & np.isfinite(sd) & (sd > 0)
    z = np.abs(mean - true) / np.where(ok, sd, np.nan)
    count = {int(r["ordinal"]): whole_true(r) for r in periods}
    n_true = np.array([count.get(int(i), -1) for i in arr["period"]])
    groups = {"all": ok, "0": ok & (n_true == 0), "1": ok & (n_true == 1), "2+": ok & (n_true >= 2)}
    out: dict[str, Any] = {"rows_with_a_spread": int(ok.sum()), "rows_determined": int(det.sum())}
    for g, m in groups.items():
        row: dict[str, Any] = {
            "rows": int(m.sum()),
            "periods": int(np.unique(arr["period"][m]).size),
        }
        for k in levels:
            row[f"within_{k:g}sd"] = float(np.mean(z[m] <= k)) if m.any() else math.nan
        row["median_relative_sd"] = float(np.median(sd[m] / true[m])) if m.any() else math.nan
        out[g] = row
    return out


def one_called_quiet(periods: list[dict[str, Any]], system: str) -> dict[str, Any] | None:
    rows = [
        r
        for r in periods
        if whole_true(r) == 1 and len(r["true"]) == 1 and system in (r.get("histories") or {})
    ]
    if not rows:
        return None
    return wilson(sum(1 for r in rows if not r["histories"][system]["spans"]), len(rows))


def any_false(periods: list[dict[str, Any]], system: str, tol: float) -> dict[str, Any] | None:
    """Share of periods in which the system declares a manoeuvre that pairs with no true one."""
    rows = [r for r in periods if system in (r.get("histories") or {})]
    if not rows:
        return None
    k = 0
    for r in rows:
        found = r["histories"][system]["spans"]
        used = found_flags(found, r["true"], tol)  # per found manoeuvre: paired or not
        k += int(any(not u for u in used))
    return wilson(k, len(rows))


def study_split6(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    out = study_split4(arr, periods, plan)
    st = plan["adaptive_study"]
    tol = float(plan["study"]["match_tolerance_s"])
    control, ada, hedge, ceiling = st["control"], st["adaptive"], st["hedged"], st["ceiling"]
    ids, med, pbound = medians3(arr)
    out["comparisons3"] = {}
    for a, b in plan.get("comparisons", []):
        c = pair3(med, a, b)
        if c:
            out["comparisons3"][f"{a}_over_{b}"] = c
    kinds = kinds_of_period(
        ids, pbound, control_misses(periods, control, float(st["detect_threshold"]), tol)
    )
    out["kinds"] = {k: int(m.sum()) for k, m in kinds.items()}
    out["by_kind"] = {}
    for a, b in ([control, ada], [control, hedge], [control, ceiling], [ada, ceiling]):
        rows = {k: pair3(med, a, b, m) for k, m in kinds.items()}
        out["by_kind"][f"{a}_over_{b}"] = {k: v for k, v in rows.items() if v}
    share: dict[str, Any] = {}
    if all(s in med for s in (control, ada, ceiling)):
        for q, name in enumerate(QUANTITIES):
            cols = [med[s][:, q] for s in (control, ada, ceiling)]
            ok = np.all([np.isfinite(c) & (c > 0) for c in cols], axis=0)
            if int(ok.sum()) >= MIN_PERIODS:
                share[name] = gain_share(cols[0][ok], cols[1][ok], cols[2][ok])
    out["share_of_ceiling"] = share
    named = [s for s in (control, ada, ceiling, "c2") if any(s in r["histories"] for r in periods)]
    out["one_called_quiet"] = {s: one_called_quiet(periods, s) for s in named}
    out["any_false"] = {
        s: {f"{int(t)}": any_false(periods, s, t) for t in (60.0, 120.0, 240.0)} for s in named
    }
    legs = [float(r["leg_inferred_s"]) for r in periods if "leg_inferred_s" in r]
    picks = [r["rate_inferred"] for r in periods if "rate_inferred" in r]
    out["rate"] = {
        "periods": len(legs),
        "leg_inferred_median_s": float(np.median(legs)) if legs else math.nan,
        "leg_inferred_quartiles_s": [float(x) for x in np.quantile(legs, [0.25, 0.75])]
        if legs
        else [],
        "picked": {k: picks.count(k) / len(picks) for k in sorted(set(picks))},
    }
    out["coverage"] = coverage(arr, periods, hedge, [float(x) for x in st["nominal_sd"]])
    auto: dict[str, list[bool]] = {}
    for r in periods:
        for k, v in (r.get("auto") or {}).items():
            auto.setdefault(k, []).append(bool(v))
    out["auto_declares_share"] = {k: float(np.mean(v)) for k, v in sorted(auto.items())}
    return out
