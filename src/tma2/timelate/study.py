"""Spec 014's readings: where the search's gain over C″ comes from, how often the bearings
cannot decide between histories, what a better identifier could attain, and how often a
manoeuvre is declared on a target that made none. Pure functions over per-period records and
per-row errors; thresholds come from the plan's ``study`` block (research R3, R4, R5, R9)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .counts import TOLERANCES, pooled
from .gate import candidate_reading, history_right, period_medians, ratio
from .score import UNDETERMINED, Q

CLASSES = ("right", "ambiguous", "search_failure", "evidence_failure")
PRIOR_SYSTEMS = ("search", "search2", "search-flat", "c2-refit", "history-map", "history-best")
FLOOR, CEILING = 1e-4, 1e2  # a period median outside these is clipped before a log ratio


def _log(a: np.ndarray) -> np.ndarray:
    out: np.ndarray = np.log(np.clip(a, FLOOR, CEILING))
    return out


def paired(
    a: np.ndarray, b: np.ndarray, level: float = 0.95, resamples: int = 2000, seed: int = 17
) -> dict[str, float]:
    """a ÷ b period by period: the geometric mean ratio with a period bootstrap, the median
    ratio, and the shares of periods where a is better, and where either is over twice as bad."""
    d = _log(a) - _log(b)
    rng = np.random.default_rng(seed)
    n = d.size
    boot = [float(np.exp(d[rng.integers(0, n, n)].mean())) for _ in range(resamples)]
    lo, hi = np.quantile(boot, [(1 - level) / 2, (1 + level) / 2])
    return {
        "geometric_mean": float(np.exp(d.mean())),
        "lo": float(lo),
        "hi": float(hi),
        "median_ratio": float(np.exp(np.median(d))),
        "a_better": float(np.mean(d < 0)),
        "a_twice_as_bad": float(np.mean(d > math.log(2.0))),
        "b_twice_as_bad": float(np.mean(d < -math.log(2.0))),
        "periods": int(n),
    }


def gain_share(
    base: np.ndarray,
    part: np.ndarray,
    whole: np.ndarray,
    level: float = 0.95,
    resamples: int = 2000,
    seed: int = 17,
) -> dict[str, float]:
    """The share of the log gain from ``base`` to ``whole`` that ``part`` obtains, pooled over
    periods (Σ log(base / part) ÷ Σ log(base / whole)) with a period bootstrap."""
    gp, gw = _log(base) - _log(part), _log(base) - _log(whole)
    rng = np.random.default_rng(seed)
    n = gp.size
    boot = []
    for _ in range(resamples):
        k = rng.integers(0, n, n)
        if gw[k].sum() != 0.0:
            boot.append(float(gp[k].sum() / gw[k].sum()))
    lo, hi = np.quantile(boot, [(1 - level) / 2, (1 + level) / 2]) if boot else (math.nan,) * 2
    share = float(gp.sum() / gw.sum()) if gw.sum() != 0.0 else math.nan
    return {"share": share, "lo": float(lo), "hi": float(hi), "periods": int(n)}


def classify(record: dict[str, Any], threshold: float, tol: float) -> str | None:
    """A period's class from its record: ``right`` when the search's first candidate is the
    true history; otherwise by the true history's log evidence minus the first candidate's."""
    cands = record.get("candidates") or []
    if not cands:
        return None
    if history_right(record["true"], cands[0]["spans"], tol):
        return "right"
    d = float(record["true_evidence"]) - float(cands[0]["evidence"])
    if not math.isfinite(d):
        return "evidence_failure" if d < 0 else "search_failure"
    if abs(d) <= threshold:
        return "ambiguous"
    return "search_failure" if d > 0 else "evidence_failure"


def wilson(k: int, n: int, z: float = 1.959963984540054) -> dict[str, float]:
    if n == 0:
        return {"rate": math.nan, "lo": math.nan, "hi": math.nan, "n": 0}
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return {"rate": p, "lo": mid - half, "hi": mid + half, "n": n}


def verdict(r: dict[str, float], materiality: float) -> str:
    if r["lo"] > materiality:
        return "material"
    if r["hi"] < materiality:
        return "not material"
    return "inconclusive"


def _system_table(
    arr: dict[str, np.ndarray], keep: np.ndarray, tight: float
) -> dict[str, dict[str, Any]]:
    bound = arr["bound"].astype(np.float64)
    det = keep & np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    out: dict[str, dict[str, Any]] = {}
    for k in sorted(arr):
        if not k.startswith("err_"):
            continue
        name, e = k[4:], arr[k].astype(np.float64)
        ok = det & np.isfinite(e[:, 0])
        rec: dict[str, Any] = {
            "rows": int(det.sum()),
            "rows_without_state": int((det & ~np.isfinite(e[:, 0])).sum()),
            "median_rows_range": float(np.median(e[ok, 0])) if ok.any() else math.nan,
            "bound_applies": name not in PRIOR_SYSTEMS,
        }
        for c, col in enumerate(("range", "course", "speed")):
            good = ok & np.isfinite(e[:, c]) & np.isfinite(bound[:, c]) & (bound[:, c] > 0)
            rec[f"efficiency_{col}"] = (
                float(np.median(e[good, c] / bound[good, c]) / Q) if good.any() else math.nan
            )
        t = ok & (bound[:, 0] < tight)
        rec["efficiency_range_tight"] = (
            float(np.median(e[t, 0] / bound[t, 0]) / Q) if t.any() else math.nan
        )
        out[name] = rec
    return out


def study_split(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    """Every reading of one split."""
    st = plan["study"]
    thr, tol = float(st["class_threshold"]), float(st["match_tolerance_s"])
    tight = float((plan.get("reference") or {}).get("tight_bound", 0.05))
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
        "periods_with_determined_rows": int(ids.size),
        "systems": _system_table(arr, np.ones(period.size, dtype=bool), tight),
    }
    for n in names:
        out["systems"][n]["median_period_range"] = (
            float(np.median(meds[n])) if ids.size else math.nan
        )
    conv = [bool(r.get("history_converged")) for r in periods]
    out["history_converged_share"] = float(np.mean(conv)) if conv else math.nan
    # comparisons: ratio of medians beside the paired reading (FR-014)
    pairs = [
        ("c2", "search2"),
        ("c2", "c2-refit"),
        ("c2-refit", "search2"),
        ("search-flat", "search2"),
        ("c2", "search-flat"),
        ("search", "search2"),
        ("search2", "history-map"),
        ("search2", "one-leg"),
        ("c2", "one-leg"),
    ]
    out["comparisons"] = {}
    if ids.size:
        for a, b in pairs:
            if a in meds and b in meds:
                out["comparisons"][f"{a}_over_{b}"] = {
                    "of_medians": ratio(meds[a], meds[b]),
                    "paired": paired(meds[a], meds[b]),
                }
    # classes of wrong-history periods and what a better identifier could attain
    cls_all = {int(r["ordinal"]): classify(r, thr, tol) for r in periods}
    known = [c for c in cls_all.values() if c is not None]
    out["classes"] = {c: wilson(sum(1 for x in known if x == c), len(known)) for c in CLASSES}
    wrong = [c for c in known if c != "right"]
    out["classes_among_wrong"] = {
        c: wilson(sum(1 for x in wrong if x == c), len(wrong)) for c in CLASSES[1:]
    }
    out["class_sensitivity"] = {}
    for t2 in (1.0, 3.0, 5.0):
        for tol2 in TOLERANCES:
            got = [classify(r, t2, tol2) for r in periods]
            got = [g for g in got if g is not None]
            out["class_sensitivity"][f"threshold_{t2:g}_tol_{int(tol2)}"] = {
                c: (sum(1 for x in got if x == c) / len(got) if got else math.nan) for c in CLASSES
            }
    top = int(plan.get("top", 3))
    out["truth_in_first_three_by_class"] = {}
    for c in CLASSES:
        rows = [r for r in periods if cls_all[int(r["ordinal"])] == c]
        hit = [
            any(history_right(r["true"], k["spans"], tol) for k in r["candidates"][:top])
            for r in rows
        ]
        out["truth_in_first_three_by_class"][c] = wilson(int(sum(hit)), len(hit))
    if ids.size and "search2" in meds and "history-best" in meds:
        cls = np.array([cls_all[int(i)] or "" for i in ids])
        s2, hb = meds["search2"], meds["history-best"]
        comp = {
            "ident-search": np.where(cls == "search_failure", hb, s2),
            "ident-all": np.where(np.isin(cls, ["search_failure", "evidence_failure"]), hb, s2),
        }
        out["headroom"] = {}
        for name, m in comp.items():
            p = paired(s2, m)
            out["headroom"][name] = {
                "paired": p,
                "of_medians": ratio(s2, m),
                "verdict": verdict(p, float(st["materiality"])),
                "median_period_range": float(np.median(m)),
            }
        out["by_class"] = {
            c: {
                "periods": int((cls == c).sum()),
                **{
                    n: float(np.median(meds[n][cls == c]))
                    for n in ("c2", "c2-refit", "search2", "history-best")
                    if n in meds and (cls == c).any()
                },
            }
            for c in CLASSES
        }
        if "c2-refit" in meds:
            out["gain_share"] = {"all": gain_share(meds["c2"], meds["c2-refit"], s2)}
            for label, k in (("search_right", cls == "right"), ("search_wrong", cls != "right")):
                if k.sum() >= 5:
                    out["gain_share"][label] = gain_share(meds["c2"][k], meds["c2-refit"][k], s2[k])
            if "search-flat" in meds:
                out["gain_share"]["flat_prior_search"] = gain_share(
                    meds["c2"], meds["search-flat"], s2
                )
    # manoeuvre counts and false manoeuvres on targets that made none (FR-010, FR-013)
    out["counts"] = {
        n: pooled(periods, n)
        for n in ("c2", "c2-refit", "search", "search2", "search-flat")
        if any(n in (r.get("histories") or {}) for r in periods)
    }
    quiet = [r for r in periods if not r["true"]]
    out["quiet"] = {"periods": len(quiet), "false_manoeuvre_rate": {}}
    for n in out["counts"]:
        have = [r for r in quiet if n in r["histories"]]
        k = sum(1 for r in have if len(r["histories"][n]["spans"]) > 0)
        out["quiet"]["false_manoeuvre_rate"][n] = wilson(k, len(have))
    # period-level splits (FR-015)
    out["by_true_count"], out["by_ownship_turns"] = {}, {}
    if ids.size:
        tc = np.array([min(len(r["true"]), 3) for r in recs])
        ot = np.array([min(int(r.get("ownship_turns", 0)), 2) for r in recs])
        for key, vals, labels in (
            ("by_true_count", tc, ("0", "1", "2", "3+")),
            ("by_ownship_turns", ot, ("0", "1", "2+")),
        ):
            for j, lab in enumerate(labels):
                k = vals == j
                if k.any():
                    out[key][lab] = {
                        "periods": int(k.sum()),
                        **{n: float(np.median(meds[n][k])) for n in names},
                    }
    # row-level splits: position in the period and range band
    out["by_leg_position"], out["by_range_band"] = {}, {}
    if "stratum" in arr:
        for j, lab in enumerate(("first", "middle", "last")):
            out["by_leg_position"][lab] = _system_table(arr, arr["stratum"] == j, tight)
    if "true_range" in arr and period.size:
        rng = arr["true_range"].astype(np.float64)
        q = np.quantile(rng, [1 / 3, 2 / 3])
        band = np.digitize(rng, q)
        for j, lab in enumerate(("near", "middle", "far")):
            tab = _system_table(arr, band == j, tight)
            for rec in tab.values():
                rec["range_m"] = [float(rng[band == j].min()), float(rng[band == j].max())]
            out["by_range_band"][lab] = tab
    if any(r.get("candidates") for r in periods):
        out["candidates"] = candidate_reading(periods, float(plan["temperature"]), top)
    secs: dict[str, list[float]] = {}
    for r in periods:
        for k2, v in (r.get("seconds") or {}).items():
            secs.setdefault(k2, []).append(float(v))
    out["seconds_per_period"] = {k2: float(np.mean(v)) for k2, v in secs.items()}
    return out


def soundness(reading: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """The validation stop (research R9): the reference from neutral starts with times held is
    at the bound on tightly bounded rows, and enough true-history fits have a consistent cost."""
    st = plan["study"]
    lo, hi = (float(x) for x in st["soundness_band"])
    name = str((plan.get("reference") or {}).get("sound", "history-fixed"))
    r = reading["man2"]
    eff = float(r["systems"][name]["efficiency_range_tight"])
    conv = float(r["history_converged_share"])
    return {
        "reference_efficiency_tight": eff,
        "band": [lo, hi],
        "history_converged_share": conv,
        "convergence_min": float(st["convergence_min"]),
        "pass": bool(lo <= eff <= hi and conv >= float(st["convergence_min"])),
    }
