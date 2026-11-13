"""One rule for whether a found manoeuvre history is the true one (spec 015 FR-004, research
R2). A true manoeuvre the period cuts (the engagement's manoeuvre began before the period's
first row or ends after its last) is not required, and a found manoeuvre that pairs with one
is not counted. What remains must have equal counts and, in time order, mid-times within the
tolerance. Kinds are not compared."""

from __future__ import annotations

from typing import Any

import numpy as np

from .periods import Period


def cut_flags(p: Period) -> list[bool]:
    """For each true manoeuvre overlapping the period with at least one row inside it, in
    ``Period.spans()`` order: whether the engagement's manoeuvre extends beyond the period."""
    out = []
    for s in p.meta.get("manoeuvres") or []:
        a, b = int(s["start_index"]), int(s["end_index"])
        if b < p.first or a > p.last:
            continue
        if min(b, p.last) - max(a, p.first) <= 0:
            continue
        out.append(a < p.first or b > p.last)
    return out


def _mids(spans: Any) -> np.ndarray:
    a = np.array(spans, dtype=np.float64).reshape(-1, 2)
    out: np.ndarray = a.mean(axis=1)
    return out


def strip_cut(
    true: Any, found: Any, tol: float, cut: list[bool] | None
) -> tuple[np.ndarray, np.ndarray]:
    """(mid-times of the whole true manoeuvres, mid-times of the found manoeuvres not paired
    with a cut one). Each cut manoeuvre takes at most one found manoeuvre: the nearest within
    ``tol`` of its visible part's mid-time."""
    tm, fm = _mids(true), _mids(found)
    flags = np.array(cut if cut is not None else [False] * tm.size, dtype=bool)
    if flags.size != tm.size:
        raise ValueError("one cut flag per true manoeuvre")
    keep = np.ones(fm.size, dtype=bool)
    for c in tm[flags]:
        d = np.where(keep, np.abs(fm - c), np.inf)
        if d.size and float(d.min()) < tol:
            keep[int(d.argmin())] = False
    return np.sort(tm[~flags]), np.sort(fm[keep])


def same_history(true: Any, found: Any, tol: float, cut: list[bool] | None = None) -> bool:
    a, b = strip_cut(true, found, tol, cut)
    if a.size != b.size:
        return False
    return bool(a.size == 0 or float(np.abs(a - b).max()) < tol)
