"""Readings of spec 016's controls (and, later, the learned tracks) from ``run4`` shards.

For each split: every system's table; paired per-period comparisons of the standing search
with each control, of each with the true-history reference under its three conventions, and
any pairs the plan names; the share of the gap from the search to the reference a control
closes; manoeuvre counts by the edge-aware rule; on periods with no true manoeuvre, how
often each system declares one, and on periods with one, two or more, how often it declares
none; what the correlation estimate and the prior diagnostic said.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .score import UNDETERMINED, _period_medians
from .study import _system_table, gain_share, paired, wilson
from .study3 import counts3, whole_true

REFERENCES = ("history-map", "history-best", "history-held", "history-fixed")


def _medians(arr: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    bound = arr["bound"].astype(np.float64)
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    ids: np.ndarray = np.zeros(0, dtype=np.int64)
    med: dict[str, np.ndarray] = {}
    for k in sorted(arr):
        if k.startswith("err_"):
            ids, m = _period_medians(arr[k].astype(np.float64), arr["period"], det)
            med[k[4:]] = m[:, 0]
    return ids, med


def _pair(med: dict[str, np.ndarray], a: str, b: str) -> dict[str, Any] | None:
    if a not in med or b not in med:
        return None
    ok = np.isfinite(med[a]) & np.isfinite(med[b])
    if int(ok.sum()) < 5:
        return None
    return paired(med[a][ok], med[b][ok])


def _declares(periods: list[dict[str, Any]], system: str) -> dict[str, Any]:
    """By number of whole true manoeuvres (0, 1, 2 or more): how often the system's history
    has none. A period with only cut manoeuvres is in no group."""
    groups: dict[str, list[dict[str, Any]]] = {"0": [], "1": [], "2+": []}
    for r in periods:
        if system not in (r.get("histories") or {}):
            continue
        n = whole_true(r)
        if n == 0 and r["true"]:
            continue
        groups["0" if n == 0 else ("1" if n == 1 else "2+")].append(r)
    out: dict[str, Any] = {}
    for label, rows in groups.items():
        k = sum(1 for r in rows if len(r["histories"][system]["spans"]) == 0)
        out[label] = {"called_quiet": wilson(k, len(rows)) if rows else None, "n": len(rows)}
    return out


def study_split4(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    tight = float(plan["reference"]["tight_bound"])
    keep = np.ones(arr["period"].size, dtype=bool)
    table = _system_table(arr, keep, tight)
    ids, med = _medians(arr)
    for name, m in med.items():
        fin = m[np.isfinite(m)]
        table[name]["median_period_range"] = float(np.median(fin)) if fin.size else math.nan
        table[name]["periods_without_a_track"] = int((~np.isfinite(m)).sum())
    systems = [s for s in med if not s.startswith("history-") and s not in ("one-leg",)]
    comparisons: dict[str, Any] = {}
    for s in systems:
        if s != "search3":
            c = _pair(med, "search3", s)
            if c:
                comparisons[f"search3_over_{s}"] = c
        for ref in REFERENCES:
            c = _pair(med, s, ref)
            if c and s in ("search3", "ctl", "c2") or (c and s.startswith("learned")):
                comparisons[f"{s}_over_{ref}"] = c
    for a, b in plan.get("comparisons", []):
        c = _pair(med, a, b)
        if c:
            comparisons[f"{a}_over_{b}"] = c
    closed: dict[str, Any] = {}
    for s in systems:
        if s in ("search3", "c2") or "history-best" not in med or "search3" not in med:
            continue
        ok = np.isfinite(med["search3"]) & np.isfinite(med[s]) & np.isfinite(med["history-best"])
        if int(ok.sum()) >= 5:
            closed[s] = gain_share(med["search3"][ok], med[s][ok], med["history-best"][ok])
    named = sorted({k for r in periods for k in (r.get("histories") or {})})
    counts = {s: counts3(periods, s) for s in named}
    declares = {s: _declares(periods, s) for s in named}
    est = np.array([r["corr_estimate"] for r in periods], dtype=np.float64).reshape(-1, 2)
    bayes = [
        r["histories"][s]["log_bayes_broad"]
        for r in periods
        for s in ("ctl",)
        if s in r.get("histories", {}) and "log_bayes_broad" in r["histories"][s]
    ]
    secs: dict[str, list[float]] = {}
    for r in periods:
        for k, v in r.get("seconds", {}).items():
            secs.setdefault(k, []).append(float(v))
    n = len(periods)
    return {
        "periods": n,
        "periods_scored": int(ids.size),
        "systems": table,
        "comparisons": comparisons,
        "gap_closed": closed,
        "counts": counts,
        "declares": declares,
        "reference_flagged_share": sum(bool(r["reference_flagged"]) for r in periods) / max(n, 1),
        "history_converged_share": sum(bool(r["history_converged"]) for r in periods) / max(n, 1),
        "corr_estimate": {
            "share_median": float(np.median(est[:, 0])) if n else math.nan,
            "share_quartiles": [float(x) for x in np.quantile(est[:, 0], [0.25, 0.75])]
            if n
            else [],
            "tau_median_where_used": float(np.median(est[est[:, 0] > 0, 1]))
            if (est[:, 0] > 0).any()
            else math.nan,
            "ctl_used_share": sum(bool(r["ctl_corr_estimate"][2]) for r in periods) / max(n, 1),
        },
        "edited_per_period": float(np.mean([r["edited"] for r in periods])) if n else math.nan,
        "log_bayes_broad": {
            "median": float(np.median(bayes)) if bayes else math.nan,
            "quantiles_05_25_75_95": [
                float(x) for x in np.quantile(bayes, [0.05, 0.25, 0.75, 0.95])
            ]
            if bayes
            else [],
            "share_above_0": float(np.mean(np.array(bayes) > 0)) if bayes else math.nan,
            "share_above_3": float(np.mean(np.array(bayes) > 3)) if bayes else math.nan,
        },
        "seconds_per_period": {k: float(np.mean(v)) for k, v in sorted(secs.items())},
    }


def soundness4(reading: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """L-a (research R11): on Annex B data the reference with its times held is at the bound
    on tight rows, its fits converge, and few references drift."""
    st = plan["study"]
    lo, hi = (float(x) for x in st["soundness_band"])
    r = reading["man2"]
    eff = float(r["systems"][plan["reference"]["sound"]]["efficiency_range_tight"])
    conv, flag = float(r["history_converged_share"]), float(r["reference_flagged_share"])
    limit = float(st["reference_flagged_max"])
    return {
        "reference_efficiency_tight": eff,
        "band": [lo, hi],
        "history_converged_share": conv,
        "convergence_min": float(st["convergence_min"]),
        "reference_flagged_share": flag,
        "reference_flagged_max": limit,
        "pass": bool(lo <= eff <= hi and conv >= float(st["convergence_min"]) and flag <= limit),
    }
