"""Spec 015's readings: spec 014's, with one rule for a history's identity
(``match.same_history``: manoeuvres cut by the period are ignored), every decided statistic
at its registered sensitivities, and the readings the panel asked for (other estimands for
the refit's share; false manoeuvres by period length; manoeuvring targets declared quiet)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .counts import TOLERANCES, match
from .gate import period_medians, ratio, temper
from .match import same_history, strip_cut
from .study import CLASSES, _log, _system_table, gain_share, paired, verdict, wilson

MAIN = "search3"
THRESHOLDS = (1.0, 3.0, 5.0)
LENGTHS = ((0, 30), (30, 45), (45, 60), (60, 90), (90, 1000))  # minutes
STATING = ("c2", "c2-refit", "search2", "search3", "search3-flat", "search3-mix")


def is_right(record: dict[str, Any], spans: Any, tol: float) -> bool:
    return same_history(record["true"], spans, tol, record.get("true_cut"))


def classify3(record: dict[str, Any], threshold: float, tol: float) -> str | None:
    cands = record.get("candidates") or []
    if not cands:
        return None
    if is_right(record, cands[0]["spans"], tol):
        return "right"
    d = float(record["true_evidence"]) - float(cands[0]["evidence"])
    if not math.isfinite(d):
        return "evidence_failure" if d < 0 else "search_failure"
    if abs(d) <= threshold:
        return "ambiguous"
    return "search_failure" if d > 0 else "evidence_failure"


def whole_true(record: dict[str, Any]) -> int:
    """True manoeuvres the period does not cut."""
    cut = record.get("true_cut") or [False] * len(record["true"])
    return int(sum(1 for c in cut if not c))


def counts3(periods: list[dict[str, Any]], system: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for tol in TOLERANCES:
        tot = {"true": 0, "matched": 0, "missed": 0, "false": 0, "found": 0}
        timing: list[float] = []
        n = 0
        for r in periods:
            h = (r.get("histories") or {}).get(system)
            if h is None:
                continue
            c = match(r["true"], h["spans"], tol, r.get("true_cut"))
            n += 1
            for k in tot:
                tot[k] += int(c[k])
            timing += c["timing"]
        out[f"{int(tol)}"] = {
            "periods": n,
            **tot,
            "missed_share": tot["missed"] / tot["true"] if tot["true"] else math.nan,
            "false_per_period": tot["false"] / n if n else math.nan,
            "timing_median_s": float(np.median(timing)) if timing else math.nan,
        }
    return out


def candidates3(
    periods: list[dict[str, Any]], temperature: float, top: int, tol: float, key: str
) -> dict[str, Any]:
    rows = [r for r in periods if r.get(key)]
    if not rows:
        return {"periods": 0}
    right = np.array([is_right(r, r[key][0]["spans"], tol) for r in rows])
    inset = np.array([any(is_right(r, c["spans"], tol) for c in r[key][:top]) for r in rows])
    p = np.array([temper([c["evidence"] for c in r[key]], temperature)[0] for r in rows])
    return {
        "periods": len(rows),
        "top_right": float(right.mean()),
        f"truth_in_top{top}": float(inset.mean()),
        "mean_top_probability": float(p.mean()),
        "calibration_gap": float(p.mean() - right.mean()),
        "kinds_differ_among_right": float(
            np.mean(
                [
                    r[key][0]["kinds"] != r["true_kinds"]
                    for r, ok in zip(rows, right, strict=True)
                    if ok and not any(r.get("true_cut") or [])
                ]
                or [math.nan]
            )
        ),
    }


def _headroom(
    s3: np.ndarray, hb: np.ndarray, cls: np.ndarray, keep: np.ndarray, materiality: float
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    sets = {
        "ident-search": ["search_failure"],
        "ident-all": ["search_failure", "evidence_failure"],
        "every-wrong": ["search_failure", "evidence_failure", "ambiguous"],
    }
    for name, which in sets.items():
        comp = np.where(np.isin(cls, which), hb, s3)
        p = paired(s3[keep], comp[keep])
        out[name] = {"paired": p, "of_medians": ratio(s3[keep], comp[keep])}
        if name != "every-wrong":
            out[name]["verdict"] = verdict(p, materiality)
    comp = np.where(np.isin(cls, sets["ident-all"]), np.minimum(hb, s3), s3)
    out["ident-all-hindsight"] = {"paired": paired(s3[keep], comp[keep])}
    return out


def study_split3(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    st = plan["study"]
    thr, tol = float(st["class_threshold"]), float(st["match_tolerance_s"])
    mat = float(st["materiality"])
    tight = float((plan.get("reference") or {}).get("tight_bound", 0.05))
    top = int(plan.get("top", 3))
    period, bound = arr["period"], arr["bound"].astype(np.float64)
    names = [k[4:] for k in sorted(arr) if k.startswith("err_")]
    meds: dict[str, np.ndarray] = {}
    ids = np.zeros(0, dtype=np.int64)
    for n in names:
        ids, meds[n] = period_medians(arr[f"err_{n}"].astype(np.float64), period, bound)
    by_ordinal = {int(r["ordinal"]): r for r in periods}
    recs = [by_ordinal[int(i)] for i in ids]
    out: dict[str, Any] = {
        "periods": len(periods),
        "periods_scored": int(ids.size),
        "systems": _system_table(arr, np.ones(period.size, dtype=bool), tight),
    }
    for n in names:
        out["systems"][n]["median_period_range"] = (
            float(np.median(meds[n])) if ids.size else math.nan
        )
    out["history_converged_share"] = float(
        np.mean([bool(r.get("history_converged")) for r in periods])
    )
    out["reference_flagged_share"] = float(
        np.mean([bool(r.get("reference_flagged")) for r in periods])
    )
    out["refit_fell_back"] = int(sum(bool(r.get("refit_fell_back")) for r in periods))
    out["periods_with_a_cut_manoeuvre"] = int(sum(any(r.get("true_cut") or []) for r in periods))
    pairs = [
        ("c2", MAIN),
        ("c2", "c2-refit"),
        ("c2-refit", MAIN),
        ("search3-flat", MAIN),
        ("search2", MAIN),
        (MAIN, "search3-mix"),
        (MAIN, "history-best"),
        (MAIN, "history-fixed"),
        (MAIN, "one-leg"),
        ("c2", "one-leg"),
        ("search3-mix", "one-leg"),
    ]
    out["comparisons"] = {}
    if ids.size:
        for a, b in pairs:
            if a in meds and b in meds:
                out["comparisons"][f"{a}_over_{b}"] = {
                    "of_medians": ratio(meds[a], meds[b]),
                    "paired": paired(meds[a], meds[b]),
                }
    # classes: on scored periods (the set every ratio uses) and on all periods
    scored = set(int(i) for i in ids)

    def shares(rows: list[dict[str, Any]], t: float, tl: float) -> dict[str, Any]:
        got = [c for c in (classify3(r, t, tl) for r in rows) if c is not None]
        wrong = [c for c in got if c != "right"]
        return {
            "periods": len(got),
            "right": wilson(sum(1 for c in got if c == "right"), len(got)),
            "wrong": len(wrong),
            "among_wrong": {
                c: wilson(sum(1 for x in wrong if x == c), len(wrong)) for c in CLASSES[1:]
            },
        }

    rows_scored = [r for r in periods if int(r["ordinal"]) in scored]
    out["classes"] = {"scored": shares(rows_scored, thr, tol), "all": shares(periods, thr, tol)}
    out["classes"]["scored_without_cut"] = shares(
        [r for r in rows_scored if not any(r.get("true_cut") or [])], thr, tol
    )
    out["truth_in_first_three_by_class"] = {}
    for c in CLASSES:
        rows = [r for r in rows_scored if classify3(r, thr, tol) == c]
        hit = [any(is_right(r, k["spans"], tol) for k in r["candidates"][:top]) for r in rows]
        out["truth_in_first_three_by_class"][c] = wilson(int(sum(hit)), len(hit))
    if ids.size and MAIN in meds and "history-best" in meds:
        s3, hb = meds[MAIN], meds["history-best"]
        flagged = np.array([bool(r.get("reference_flagged")) for r in recs])
        every = np.ones(ids.size, dtype=bool)
        out["headroom"] = {}
        for t in THRESHOLDS:
            for tl in TOLERANCES:
                cls = np.array([classify3(r, t, tl) or "" for r in recs])
                key = f"threshold_{t:g}_tol_{int(tl)}"
                out["headroom"][key] = _headroom(s3, hb, cls, every, mat)
                if t == thr and tl == tol:
                    out["headroom"]["registered"] = out["headroom"][key]
                    out["headroom"]["registered_without_flagged"] = _headroom(
                        s3, hb, cls, ~flagged, mat
                    )
                    out["by_class"] = {
                        c: {
                            "periods": int((cls == c).sum()),
                            **{
                                n: float(np.median(meds[n][cls == c]))
                                for n in ("c2", "c2-refit", MAIN, "history-best")
                                if n in meds and (cls == c).any()
                            },
                        }
                        for c in CLASSES
                    }
        if "c2-refit" in meds:
            c2, rf = meds["c2"], meds["c2-refit"]
            fell = np.array([bool(r.get("refit_fell_back")) for r in recs])
            sane = (np.maximum(np.maximum(c2, rf), s3)) <= 1.0
            cls = np.array([classify3(r, thr, tol) or "" for r in recs])
            g: dict[str, Any] = {
                "registered": gain_share(c2, rf, s3),
                "without_fallbacks": gain_share(c2[~fell], rf[~fell], s3[~fell]),
                "medians_at_most_1": {**gain_share(c2[sane], rf[sane], s3[sane])},
                "ratio_of_log_medians": float(
                    (math.log(np.median(c2)) - math.log(np.median(rf)))
                    / (math.log(np.median(c2)) - math.log(np.median(s3)))
                ),
            }
            for label, k in (("search_right", cls == "right"), ("search_wrong", cls != "right")):
                if k.sum() >= 5:
                    g[label] = gain_share(c2[k], rf[k], s3[k])
            if "search3-flat" in meds:
                g["flat_prior_search"] = gain_share(c2, meds["search3-flat"], s3)
            out["gain_share"] = g
            out["refit_runaways"] = int((_log(rf) >= math.log(1.0)).sum())
    out["counts"] = {
        n: counts3(periods, n)
        for n in STATING
        if any(n in (r.get("histories") or {}) for r in periods)
    }
    # targets that make no (whole) manoeuvre in the period: false manoeuvres, by period length
    quiet = [r for r in periods if whole_true(r) == 0 and not r["true"]]
    out["quiet"] = {"periods": len(quiet), "false_manoeuvre_rate": {}, "by_minutes": {}}
    for n in out["counts"]:
        have = [r for r in quiet if n in r["histories"]]
        out["quiet"]["false_manoeuvre_rate"][n] = wilson(
            sum(1 for r in have if len(r["histories"][n]["spans"]) > 0), len(have)
        )
        for lo, hi in LENGTHS:
            sub = [r for r in have if lo * 60 <= float(r.get("seconds_long", 0.0)) < hi * 60]
            out["quiet"]["by_minutes"].setdefault(f"{lo}-{hi}", {})[n] = wilson(
                sum(1 for r in sub if len(r["histories"][n]["spans"]) > 0), len(sub)
            )
    # manoeuvring targets declared quiet, by number of whole true manoeuvres
    out["declared_quiet"] = {}
    for n in out["counts"]:
        rec: dict[str, Any] = {}
        for lab, lo, hi in (("1", 1, 1), ("2", 2, 2), ("3+", 3, 10**6)):
            sub = [
                r
                for r in periods
                if n in r["histories"]
                and lo <= whole_true(r) <= hi
                and not any(r.get("true_cut") or [])
            ]
            none = sum(
                1
                for r in sub
                if strip_cut(r["true"], r["histories"][n]["spans"], tol, r.get("true_cut"))[1].size
                == 0
            )
            rec[lab] = wilson(none, len(sub))
        out["declared_quiet"][n] = rec
    out["by_true_count"] = {}
    if ids.size:
        tc = np.array([min(whole_true(r), 3) for r in recs])
        for j, lab in enumerate(("0", "1", "2", "3+")):
            k = tc == j
            if k.any():
                out["by_true_count"][lab] = {
                    "periods": int(k.sum()),
                    **{n: float(np.median(meds[n][k])) for n in names},
                }
    for key in ("candidates", "candidates2"):
        if any(r.get(key) for r in periods):
            out[key] = candidates3(periods, float(plan["temperature"]), top, tol, key)
    secs: dict[str, list[float]] = {}
    for r in periods:
        for k2, v in (r.get("seconds") or {}).items():
            secs.setdefault(k2, []).append(float(v))
    out["seconds_per_period"] = {k2: float(np.mean(v)) for k2, v in secs.items()}
    return out


def soundness3(reading: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    st = plan["study"]
    lo, hi = (float(x) for x in st["soundness_band"])
    r = reading["man2"]
    eff = float(r["systems"]["history-fixed"]["efficiency_range_tight"])
    conv, flag = float(r["history_converged_share"]), float(r["reference_flagged_share"])
    limit = float(plan.get("reference_flagged_max", 0.15))
    return {
        "reference_efficiency_tight": eff,
        "band": [lo, hi],
        "history_converged_share": conv,
        "convergence_min": float(st["convergence_min"]),
        "reference_flagged_share": flag,
        "reference_flagged_max": limit,
        "pass": bool(lo <= eff <= hi and conv >= float(st["convergence_min"]) and flag <= limit),
    }
