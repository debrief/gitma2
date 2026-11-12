"""Gate T's readings (spec 013): the evidence search against C″ read as a track, the same
under a shifted manoeuvre prior, and whether the candidate tracks and their probabilities can
be relied on. Pure functions over per-period records and per-row errors; the criteria come
from the plan and are fixed by the decision record."""

from __future__ import annotations

from typing import Any

import numpy as np

from .score import UNDETERMINED

MATCH_S = 120.0  # a found manoeuvre matches a true one when their mid-times are this close


def history_right(true: list[list[float]], found: list[list[float]], tol: float = MATCH_S) -> bool:
    """Whether a found history is the true one: the same number of manoeuvres and, in time
    order, mid-times within ``tol``."""
    if len(true) != len(found):
        return False
    if not true:
        return True
    a = np.sort(np.mean(np.array(true, dtype=np.float64), axis=1))
    b = np.sort(np.mean(np.array(found, dtype=np.float64), axis=1))
    return bool(float(np.abs(a - b).max()) < tol)


def temper(evidence: list[float], temperature: float) -> np.ndarray:
    """Candidate probabilities from log evidences at a temperature (1 = Laplace's own; above 1
    flattens an overconfident approximation)."""
    e = np.array(evidence, dtype=np.float64)
    w = np.exp((e - e.max()) / temperature)
    out: np.ndarray = w / w.sum()
    return out


def period_medians(
    err: np.ndarray, period: np.ndarray, bound: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(period ids with determined rows, each period's median relative range error over them;
    a row with no state counts as +inf)."""
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    ids = np.unique(period[det])
    e = np.where(np.isfinite(err[:, 0]), err[:, 0], np.inf)
    med = np.array([np.median(e[det & (period == i)]) for i in ids])
    return ids, med


def ratio(
    a: np.ndarray, b: np.ndarray, level: float = 0.95, resamples: int = 2000, seed: int = 17
) -> dict[str, float]:
    """median(a) / median(b) over periods with a period bootstrap."""
    rng = np.random.default_rng(seed)
    n = a.size
    d = []
    for _ in range(resamples):
        k = rng.integers(0, n, n)
        d.append(float(np.median(a[k]) / np.median(b[k])))
    lo, hi = np.quantile(d, [(1 - level) / 2, (1 + level) / 2])
    return {"value": float(np.median(a) / np.median(b)), "lo": float(lo), "hi": float(hi)}


def candidate_reading(
    periods: list[dict[str, Any]], temperature: float, top: int = 3
) -> dict[str, Any]:
    """Over periods with candidates: how often the top candidate is the true history, how often
    the true history is among the first ``top``, and the calibration of the top probability at
    ``temperature`` (mean stated probability against frequency, by bin, and the Brier score)."""
    rows = [r for r in periods if r.get("candidates")]
    if not rows:
        return {"periods": 0}
    right = np.array([history_right(r["true"], r["candidates"][0]["spans"]) for r in rows])
    inset = np.array(
        [any(history_right(r["true"], c["spans"]) for c in r["candidates"][:top]) for r in rows]
    )
    p = np.array([temper([c["evidence"] for c in r["candidates"]], temperature)[0] for r in rows])
    bins = []
    for lo, hi in ((0.0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0001)):
        k = (p >= lo) & (p < hi)
        if k.any():
            bins.append(
                {
                    "from": lo,
                    "to": min(hi, 1.0),
                    "periods": int(k.sum()),
                    "stated": float(p[k].mean()),
                    "right": float(right[k].mean()),
                }
            )
    return {
        "periods": len(rows),
        "temperature": temperature,
        "top_right": float(right.mean()),
        f"truth_in_top{top}": float(inset.mean()),
        "mean_top_probability": float(p.mean()),
        "calibration_gap": float(p.mean() - right.mean()),
        "brier": float(np.mean((p - right) ** 2)),
        "bins": bins,
    }


def verdicts(reading: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    """Gate T's checks from a scored record and the plan's ``criteria`` block. A plan with
    ``reference_tight_efficiency_band`` is the re-registered gate (2026-11-12): T-a reads the
    history reference with its times held, on tightly bounded rows; T-e compares the search
    with the history reference fitted with the prior; and T-d also checks the candidates'
    calibration on the shift split. Otherwise the first registration's checks."""
    out: dict[str, Any] = {}
    second = "reference_tight_efficiency_band" in c
    man2 = reading["man2"]
    if second:
        eff = man2["systems"]["history-fixed"]["efficiency_range_tight"]
        lo, hi = c["reference_tight_efficiency_band"]
    else:
        eff = man2["systems"]["truth-fit"]["efficiency_range"]
        lo, hi = c["reference_efficiency_band"]
    out["T-a"] = {"value": eff, "band": [lo, hi], "pass": bool(lo <= eff <= hi)}
    r = man2["ratios"]["c2_over_search"]
    out["T-b"] = {
        **r,
        "threshold": c["search_ratio_min"],
        "pass": bool(r["lo"] > c["search_ratio_min"]),
    }
    if "shift" in reading:
        s = reading["shift"]["ratios"]["c2_over_search"]
        out["T-c"] = {
            **s,
            "threshold": c["shift_ratio_min"],
            "pass": bool(s["lo"] > c["shift_ratio_min"]),
        }
    cand = man2["candidates"]
    key = next(k for k in cand if k.startswith("truth_in_top"))
    out["T-d"] = {
        "truth_in_set": cand[key],
        "truth_in_set_min": c["truth_in_set_min"],
        "calibration_gap": cand["calibration_gap"],
        "calibration_gap_max": c["calibration_gap_max"],
        "pass": bool(
            cand[key] >= c["truth_in_set_min"]
            and abs(cand["calibration_gap"]) <= c["calibration_gap_max"]
        ),
    }
    if second and "shift" in reading:
        gap = reading["shift"]["candidates"]["calibration_gap"]
        out["T-d-shift"] = {
            "calibration_gap": gap,
            "calibration_gap_max": c["shift_calibration_gap_max"],
            "pass": bool(abs(gap) <= c["shift_calibration_gap_max"]),
        }
    h = man2["ratios"]["search_over_history" if second else "search_over_truth"]
    out["T-e"] = {
        **h,
        "threshold": c["headroom_ratio_min"],
        "material": bool(h["lo"] > c["headroom_ratio_min"]),
    }
    return out
