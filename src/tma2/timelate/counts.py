"""Manoeuvre counts for a found history against the true one (spec 014 FR-013; spec 013
FR-011): matched, missed and false at a tolerance on mid-times, and the timing error of the
matches. A true manoeuvre cut by the period's edge is neither missed nor, when a found one
pairs with it, a source of a false count."""

from __future__ import annotations

from typing import Any

import numpy as np

TOLERANCES = (60.0, 120.0, 240.0)


def match(
    true: list[list[float]],
    found: list[list[float]],
    tol: float,
    edge: list[bool] | None = None,
) -> dict[str, Any]:
    """Pairs in time order, nearest first: each true manoeuvre takes the closest unused found
    one whose mid-time is within ``tol``. ``edge`` marks true manoeuvres cut by the period."""
    tm = [0.5 * (a + b) for a, b in true]
    fm = [0.5 * (a + b) for a, b in found]
    cut = list(edge) if edge is not None else [False] * len(tm)
    pairs = sorted(
        (abs(a - b), i, j) for i, a in enumerate(tm) for j, b in enumerate(fm) if abs(a - b) < tol
    )
    used_t: set[int] = set()
    used_f: set[int] = set()
    timing: list[float] = []
    for d, i, j in pairs:
        if i in used_t or j in used_f:
            continue
        used_t.add(i)
        used_f.add(j)
        if not cut[i]:
            timing.append(d)
    whole = [i for i in range(len(tm)) if not cut[i]]
    return {
        "true": len(whole),
        "matched": sum(1 for i in whole if i in used_t),
        "missed": sum(1 for i in whole if i not in used_t),
        "false": len(fm) - len(used_f),
        "found": len(fm),
        "timing": timing,
    }


def pooled(
    periods: list[dict[str, Any]], system: str, tolerances: tuple[float, ...] = TOLERANCES
) -> dict[str, Any]:
    """Counts over periods for one system's histories (``record["histories"][system]``)."""
    out: dict[str, Any] = {}
    for tol in tolerances:
        tot = {"true": 0, "matched": 0, "missed": 0, "false": 0, "found": 0}
        timing: list[float] = []
        n = 0
        for r in periods:
            h = (r.get("histories") or {}).get(system)
            if h is None:
                continue
            c = match(r["true"], h["spans"], tol, r.get("true_edge"))
            n += 1
            for k in tot:
                tot[k] += int(c[k])
            timing += c["timing"]
        rec: dict[str, Any] = {"periods": n, **tot}
        rec["missed_share"] = tot["missed"] / tot["true"] if tot["true"] else float("nan")
        rec["false_per_period"] = tot["false"] / n if n else float("nan")
        rec["timing_median_s"] = float(np.median(timing)) if timing else float("nan")
        rec["timing_p90_s"] = float(np.quantile(timing, 0.9)) if timing else float("nan")
        out[f"{int(tol)}"] = rec
    return out
