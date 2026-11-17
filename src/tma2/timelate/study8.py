"""Spec 023's readings: paired per-period ratios with an engagement bootstrap (research R5).

A period's figure is the median of its row errors over the rows scored for it; the ratio of
two systems is taken per period and summarised by its geometric mean, with a 95% interval
from resampling engagements (all of an engagement's periods together), the median
per-period ratio, and the shares of periods better, twice as good and twice as bad.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from .score import COLS, Q

UNDETERMINED = 0.5  # rows are scored where the span's bound on relative range is below this
BOOT = 2000
BOOT_SEED = 23
QUANTITIES = ("range", "course", "speed")


def period_table(
    arr: dict[str, np.ndarray], rows: np.ndarray, systems: list[str]
) -> dict[str, Any]:
    """Per (engagement, period) with any selected row: the median error of each system in each
    quantity, over the selected rows where every listed system has a state."""
    eng, per = arr["eng"].astype(np.int64), arr["period"].astype(np.int64)
    key = eng * 8 + per
    ok = rows.copy()
    for s in systems:
        ok &= np.isfinite(arr[f"err_{s}"][:, 0])
    keys = np.unique(key[ok])
    out: dict[str, Any] = {
        "eng": keys // 8,
        "period": keys % 8,
        "rows": np.array([int((ok & (key == k)).sum()) for k in keys]),
    }
    for s in systems:
        e = arr[f"err_{s}"].astype(np.float64)
        med = np.full((keys.size, 3), np.nan)
        for i, k in enumerate(keys):
            m = ok & (key == k)
            for c in range(3):
                v = e[m, c]
                v = v[np.isfinite(v)]
                med[i, c] = float(np.median(v)) if v.size else np.nan
        out[s] = med
    out["dropped_rows_without_state"] = int((rows & ~ok).sum())
    return out


def paired(num: np.ndarray, den: np.ndarray, eng: np.ndarray, quantity: int = 0) -> dict[str, Any]:
    """``num ÷ den`` per period (a value above 1: ``den`` is better)."""
    a, b = num[:, quantity], den[:, quantity]
    ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    lr, g = np.log(a[ok] / b[ok]), eng[ok]
    if lr.size == 0:
        return {"periods": 0, "engagements": 0}
    ids = np.unique(g)
    groups = [lr[g == i] for i in ids]
    rng = np.random.default_rng(BOOT_SEED)
    means = np.empty(BOOT)
    for k in range(BOOT):
        pick = rng.integers(0, ids.size, ids.size)
        means[k] = np.concatenate([groups[j] for j in pick]).mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "value": float(np.exp(lr.mean())),
        "lo": float(np.exp(lo)),
        "hi": float(np.exp(hi)),
        "median": float(np.exp(np.median(lr))),
        "better": float(np.mean(lr > 0)),
        "twice_as_good": float(np.mean(lr > np.log(2))),
        "twice_as_bad": float(np.mean(lr < -np.log(2))),
        "periods": int(lr.size),
        "engagements": int(ids.size),
    }


def _per_period_facts(periods: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    """Per (engagement, period): own ownship turns, the longest adjacent gap (s), whether an
    adjacent gap holds a true manoeuvre, and whether the joint solve fell back."""
    out = {}
    for r in periods:
        if "layout" not in r:
            continue
        gaps = r["gaps"]
        k = len(r["layout"]["periods"])
        for i in range(k):
            adj = [gaps[j] for j in (i - 1, i) if 0 <= j < len(gaps)]
            out[(int(r["ordinal"]), i)] = {
                "own_turn": r["own_turns"][i] > 0,
                "gap_s": max(g["length_s"] for g in adj),
                "gap_manoeuvre": any(g["true"] > 0 for g in adj),
                "fell_back": bool(r["joint_fell_back"][i]),
            }
    return out


def gap_reading(periods: list[dict[str, Any]]) -> dict[str, Any]:
    """Manoeuvres in gaps: gaps holding one (found: the joint solve declared one there; missed),
    and gaps holding none in which it declared one (invented)."""
    gs = [g for r in periods for g in r.get("gaps", [])]
    held = [g for g in gs if g["true"] > 0]
    quiet = [g for g in gs if g["true"] == 0]
    return {
        "gaps": len(gs),
        "with_true_manoeuvre": len(held),
        "found": int(sum(g["declared"] > 0 for g in held)),
        "missed": int(sum(g["declared"] == 0 for g in held)),
        "invented": int(sum(g["declared"] > 0 for g in quiet)),
        "invented_share": float(np.mean([g["declared"] > 0 for g in quiet])) if quiet else None,
        "found_share": float(np.mean([g["declared"] > 0 for g in held])) if held else None,
    }


def false_manoeuvres(periods: list[dict[str, Any]]) -> dict[str, Any]:
    """On held course: the share of engagements in which each system declares any manoeuvre,
    and for the joint solve where (inside a period or in a gap)."""
    rs = [r for r in periods if "layout" in r]
    if not rs:
        return {}

    def inside(spans: list[list[float]], r: dict[str, Any]) -> bool:
        return any(s[1] >= a and s[0] <= b for s in spans for a, b in r["layout"]["period_seconds"])

    return {
        "engagements": len(rs),
        "alone_any": float(np.mean([any(len(a) for a in r["alone"]) for r in rs])),
        "joint_any": float(np.mean([len(r["joint"]) > 0 for r in rs])),
        "joint_in_period": float(np.mean([inside(r["joint"], r) for r in rs])),
        "joint_in_gap": float(np.mean([any(g["declared"] > 0 for g in r["gaps"]) for r in rs])),
        "full_any": float(np.mean([len(r["full"]) > 0 for r in rs])),
    }


COMPARISONS = (
    ("alone", "joint"),  # the decided ratio
    ("full", "joint"),  # below 1: what the gaps cost
    ("joint", "ref-span"),  # what is left against the span reference
    ("c2", "joint"),
    ("alone", "ref-alone"),
    ("one-leg", "joint"),
)


def study_split8(arr: dict[str, np.ndarray], periods: list[dict[str, Any]]) -> dict[str, Any]:
    span = arr["bound_span"][:, 0].astype(np.float64)
    own = arr["bound_own"][:, 0].astype(np.float64)
    rows = np.isfinite(span) & (span < UNDETERMINED)
    rows_own = rows & np.isfinite(own) & (own < UNDETERMINED)
    systems = [k[4:] for k in arr if k.startswith("err_")]
    facts = _per_period_facts(periods)
    out: dict[str, Any] = {
        "engagements": len(periods),
        "engagements_skipped": sum(1 for r in periods if "skipped" in r),
        "periods": len(facts),
        "joint_fell_back": int(sum(f["fell_back"] for f in facts.values())),
        "scored_rows": int(rows.sum()),
        "scored_rows_own": int(rows_own.sum()),
    }
    tab = period_table(arr, rows, systems)
    tab_own = period_table(arr, rows_own, systems)
    out["periods_scored"] = int(tab["eng"].size)
    out["periods_scored_own"] = int(tab_own["eng"].size)
    out["dropped_rows_without_state"] = tab["dropped_rows_without_state"]

    def block(t: dict[str, Any], sel: np.ndarray | None = None) -> dict[str, Any]:
        res: dict[str, Any] = {}
        for a, b in COMPARISONS:
            if a not in t or b not in t:
                continue
            na, nb, eng = t[a], t[b], t["eng"]
            if sel is not None:
                na, nb, eng = na[sel], nb[sel], eng[sel]
            res[f"{a}/{b}"] = {q: paired(na, nb, eng, c) for c, q in enumerate(QUANTITIES)}
        return res

    out["ratios"] = block(tab)
    out["ratios_own_rows"] = block(tab_own)
    keys = list(zip(tab["eng"].tolist(), tab["period"].tolist(), strict=True))
    f = [facts.get((int(e), int(p)), {}) for e, p in keys]

    def by(pred: Callable[[dict[str, Any]], bool]) -> np.ndarray:
        return np.array([bool(x) and pred(x) for x in f], dtype=bool)

    span_med = np.array(
        [float(np.median(span[rows & (arr["eng"] == e) & (arr["period"] == p)])) for e, p in keys]
    )
    kinds = {
        "own_turn": by(lambda x: x["own_turn"]),
        "no_own_turn": by(lambda x: not x["own_turn"]),
        "gap_under_10min": by(lambda x: x["gap_s"] < 600),
        "gap_10_to_20min": by(lambda x: 600 <= x["gap_s"] < 1200),
        "gap_over_20min": by(lambda x: x["gap_s"] >= 1200),
        "gap_manoeuvre": by(lambda x: x["gap_manoeuvre"]),
        "no_gap_manoeuvre": by(lambda x: not x["gap_manoeuvre"]),
        "span_bound_tight": span_med < 0.05,
        "span_bound_middle": (span_med >= 0.05) & (span_med < 0.2),
        "span_bound_loose": span_med >= 0.2,
    }
    out["by_kind"] = {k: {"periods": int(sel.sum()), **block(tab, sel)} for k, sel in kinds.items()}
    eff: dict[str, Any] = {}
    bs = arr["bound_span"].astype(np.float64)
    for s in systems:
        e = arr[f"err_{s}"].astype(np.float64)
        eff[s] = {}
        for c, col in enumerate(COLS[:3]):
            ok = rows & np.isfinite(e[:, c]) & np.isfinite(bs[:, c]) & (bs[:, c] > 0)
            eff[s][col] = float(np.median(e[ok, c] / bs[ok, c]) / Q) if ok.any() else None
    out["efficiency_span_bound"] = eff
    out["medians"] = {s: float(np.median(tab[s][:, 0][np.isfinite(tab[s][:, 0])])) for s in systems}
    out["gaps"] = gap_reading(periods)
    out["false_manoeuvres"] = false_manoeuvres(periods)
    return out


def verdict(r: dict[str, Any]) -> dict[str, Any]:
    """FR-010: gain if the range interval of alone ÷ joint is wholly above 1; harm if any of
    range, course and speed is wholly below 1."""
    d = r["ratios"].get("alone/joint", {})
    rng = d.get("range", {})
    gain = bool(rng.get("lo", 0) > 1)
    harm = any(d.get(q, {}).get("hi", np.inf) < 1 for q in QUANTITIES)
    return {
        "gain": gain,
        "harm": harm,
        "outcome": "harm" if harm else ("gain" if gain else "not shown"),
    }
