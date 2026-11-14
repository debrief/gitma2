"""Readings of spec 017: study L's readings of the control (``study4``) and, beside them,
what the gap to the true history is made of.

* **Detectability** of the whole true manoeuvres: quantiles and the share under each
  registered threshold; the control's miss rate by detectability band.
* **The gap, split**: for a system S, a full reference F and the reference D told only the
  manoeuvres above a threshold, the *attainable share* is Σ log(S ÷ D) ÷ Σ log(S ÷ F) over
  periods (a period bootstrap for its interval): the part of the gap a system told every
  detectable manoeuvre would still close. The rest is identifiability at that threshold.
* The verdict (research R5) reads the attainable share at the primary threshold.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .study import gain_share, wilson
from .study4 import _medians, study_split4

BANDS = ((0.0, 5.0), (5.0, 10.0), (10.0, 20.0), (20.0, 40.0), (40.0, 100.0), (100.0, math.inf))


def found_flags(true: list[list[float]], found: list[list[float]], tol: float) -> list[bool]:
    """Per true manoeuvre: whether a found one pairs with it (nearest first, each used once,
    mid-times within ``tol``), as ``counts.match`` pairs them."""
    tm = [0.5 * (a + b) for a, b in true]
    fm = [0.5 * (a + b) for a, b in found]
    pairs = sorted(
        (abs(a - b), i, j) for i, a in enumerate(tm) for j, b in enumerate(fm) if abs(a - b) < tol
    )
    used_t: set[int] = set()
    used_f: set[int] = set()
    for _d, i, j in pairs:
        if i not in used_t and j not in used_f:
            used_t.add(i)
            used_f.add(j)
    return [i in used_t for i in range(len(tm))]


def detect_table(
    periods: list[dict[str, Any]], systems: list[str], thresholds: list[float], tol: float
) -> dict[str, Any]:
    """Whole (uncut) true manoeuvres only."""
    det: list[float] = []
    hit: dict[str, list[bool]] = {s: [] for s in systems}
    for r in periods:
        d, cut = r["detectability"], r["true_cut"]
        flags = {
            s: found_flags(r["true"], r["histories"][s]["spans"], tol)
            for s in systems
            if s in r["histories"]
        }
        for i, (x, c) in enumerate(zip(d, cut, strict=True)):
            if c:
                continue
            det.append(float(x))
            for s in systems:
                hit[s].append(bool(flags[s][i]) if s in flags else False)
    a = np.array(det)
    out: dict[str, Any] = {"manoeuvres": int(a.size)}
    if a.size == 0:
        return out
    out["quantiles_10_25_50_75_90"] = [
        float(q) for q in np.quantile(a, [0.1, 0.25, 0.5, 0.75, 0.9])
    ]
    out["share_below"] = {f"{t:g}": wilson(int((a < t).sum()), int(a.size)) for t in thresholds}
    bands: dict[str, Any] = {}
    for lo, hi in BANDS:
        m = (a >= lo) & (a < hi)
        key = f"{lo:g}-{hi:g}" if math.isfinite(hi) else f"{lo:g}+"
        row: dict[str, Any] = {"n": int(m.sum())}
        for s in systems:
            h = np.array(hit[s], dtype=bool)
            row[s] = wilson(int((~h[m]).sum()), int(m.sum())) if m.any() else None
        bands[key] = row
    out["missed_by_band"] = bands
    return out


def gap_split(
    med: dict[str, np.ndarray], system: str, full: str, thresholds: list[float], suffix: str = ""
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t in thresholds:
        part = f"ref-d{t:g}{suffix}"
        if system not in med or full not in med or part not in med:
            continue
        ok = np.isfinite(med[system]) & np.isfinite(med[full]) & np.isfinite(med[part])
        if int(ok.sum()) < 5:
            continue
        out[f"{t:g}"] = gain_share(med[system][ok], med[part][ok], med[full][ok])
    return out


def verdict(share: dict[str, float] | None) -> str:
    """Research R5, on the attainable share at the primary threshold."""
    if share is None:
        return "absent"
    if share["hi"] < 0.5:
        return "mostly identifiability"
    if share["lo"] > 0.5:
        return "mostly attainable"
    return "mixed"


def study_split5(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    out = study_split4(arr, periods, plan)
    st = plan["shifted"]
    thresholds = [float(x) for x in plan["settings"]["detect_thresholds"]]
    tol = float(plan["study"]["match_tolerance_s"])
    _ids, med = _medians(arr)
    systems = [s for s in st["systems"] if all(s in r["histories"] for r in periods)]
    out["detectability"] = detect_table(periods, systems, thresholds, tol)
    out["gap_split"] = {
        s: gap_split(med, s, "ref-full", thresholds) for s in st["systems"] if s in med
    }
    if "ref-full-edit" in med:
        out["gap_split_edited"] = {
            s: gap_split(med, s, "ref-full-edit", thresholds, "-edit")
            for s in st["systems"]
            if s in med
        }
    primary = f"{float(st['primary_threshold']):g}"
    out["verdict"] = verdict(out["gap_split"].get(st["control"], {}).get(primary))
    return out
