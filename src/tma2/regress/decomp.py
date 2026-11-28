"""Where the regressor's gain comes from (spec 038 research R5).

Readings on one scoring run's per-row errors, built on ``regress.mread``: a system's error on an
engagement is its median over the rows both sides answer, comparisons are paired log ratios
(control ÷ system, above 1: the system is better) with a bootstrap over engagements, and several
training seeds of one system are pooled by the mean log ratio on the engagements they share.

New here: the **share** of one log gain that another obtains (the gap a hardened control closes;
the part of the regressor's gain that a prior inside a classical solve obtains), slices of rows
(time since the last true target change, a wild first bearing, whether C″'s structure was right
at the first scored row), and the per-engagement log ratios kept for comparisons between splits.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tma2.regress.mread import COLS, scenario_log_ratio, summarise

SINCE_BANDS_S = (300.0, 900.0)  # under 5 min, 5 to 15 min, over 15 min since the last change
MATCH_TOL_S = 120.0
MOST, LITTLE = 0.5, 0.2


def pooled_logs(
    errs: dict[str, np.ndarray],
    control: str,
    systems: list[str],
    ordinal: np.ndarray,
    col: int,
    rows: np.ndarray | None = None,
) -> dict[int, float]:
    """{engagement: mean over ``systems`` of ln(control ÷ system)} on engagements all share."""
    per = []
    for s in systems:
        ids, lr, _ = scenario_log_ratio(errs[control][:, col], errs[s][:, col], ordinal, rows)
        per.append(dict(zip(ids.tolist(), lr.tolist(), strict=True)))
    if not per:
        return {}
    common = sorted(set.intersection(*(set(d) for d in per)))
    return {u: float(np.mean([d[u] for d in per])) for u in common}


def ratio(logs: dict[int, float], resamples: int = 2000) -> dict[str, Any]:
    return summarise(np.array(list(logs.values()), dtype=np.float64), resamples=resamples)


def share(
    num: dict[int, float], den: dict[int, float], resamples: int = 2000, seed: int = 41
) -> dict[str, Any]:
    """mean(num) ÷ mean(den) over the engagements both have, with an engagement bootstrap. Not
    defined where the denominator's own interval contains 0 (no gain to take a share of)."""
    common = sorted(set(num) & set(den))
    n = len(common)
    if n == 0:
        return {"scenarios": 0, "defined": False}
    a = np.array([num[u] for u in common])
    b = np.array([den[u] for u in common])
    pick = np.random.default_rng(seed).integers(0, n, (resamples, n))
    am, bm = a[pick].mean(axis=1), b[pick].mean(axis=1)
    dlo, dhi = (float(v) for v in np.quantile(bm, [0.025, 0.975]))
    out: dict[str, Any] = {
        "scenarios": n,
        "numerator_ratio": math.exp(float(a.mean())),
        "denominator_ratio": math.exp(float(b.mean())),
        "denominator_lo": math.exp(dlo),
        "denominator_hi": math.exp(dhi),
        "defined": bool(dlo > 0 or dhi < 0),
    }
    if out["defined"]:
        lo, hi = (float(v) for v in np.quantile(am / bm, [0.025, 0.975]))
        k = n // 10  # beside the mean (spec 038's panel): medians, and 10% trimmed at both ends
        sa, sb = np.sort(a), np.sort(b)
        out |= {
            "share_of_medians": float(np.median(a) / np.median(b)) if np.median(b) != 0 else None,
            "share_trimmed": float(sa[k : n - k].mean() / sb[k : n - k].mean())
            if n - 2 * k > 0 and sb[k : n - k].mean() != 0
            else None,
        }
        out |= {
            "share": float(a.mean() / b.mean()),
            "lo": lo,
            "hi": hi,
            "outcome": "most" if lo >= MOST else "little" if hi <= LITTLE else "between",
        }
    return out


def since_last_change(manoeuvres: list[dict[str, Any]], k: int, dt: float) -> float:
    """Seconds from the end of the last true target change that began at or before row k to row
    k (0 inside one; ∞ with none yet)."""
    past = [m for m in manoeuvres if int(m["start_index"]) <= k]
    if not past:
        return math.inf
    return max(0.0, (k - max(int(m["end_index"]) for m in past)) * dt)


def since_band(s: float) -> int:
    return int(np.searchsorted(np.asarray(SINCE_BANDS_S), s, side="right"))


def structure_right(
    declared: list[tuple[int, int]],
    manoeuvres: list[dict[str, Any]],
    k: int,
    dt: float,
    tol_s: float = MATCH_TOL_S,
) -> bool:
    """Whether the transitions declared at prefix k are the true target changes: every true
    change begun at least ``tol_s`` before k overlaps a declared transition within ``tol_s``,
    and every declared transition overlaps a true change begun by k within ``tol_s``."""
    tol = tol_s / dt
    true = [(int(m["start_index"]), min(int(m["end_index"]), k)) for m in manoeuvres]
    seen = [(s, e) for s, e in true if s <= k]
    must = [(s, e) for s, e in seen if s <= k - tol]

    def near(a: tuple[int, int], b: tuple[int, int]) -> bool:
        return a[0] <= b[1] + tol and b[0] <= a[1] + tol

    return all(any(near(m, d) for d in declared) for m in must) and all(
        any(near(d, m) for m in seen) for d in declared
    )


def by_engagement(values: dict[int, Any], ordinal: np.ndarray, default: Any) -> np.ndarray:
    return np.array([values.get(int(u), default) for u in ordinal])


def common_rows(errs: dict[str, np.ndarray], names: list[str]) -> np.ndarray:
    out = np.ones(next(iter(errs.values())).shape[0], dtype=bool)
    for n in names:
        out &= np.isfinite(errs[n]).all(axis=1)
    return out


def comparisons(
    errs: dict[str, np.ndarray],
    names: dict[str, Any],
    ordinal: np.ndarray,
    rows: np.ndarray | None = None,
    resamples: int = 2000,
) -> dict[str, Any]:
    """Every registered comparison on ``rows``: comparator ÷ each group of systems, the gap each
    hardened control closes, and the prior's shares; for range, course and speed.

    ``names``: ``comparator``; ``regressors`` (the fine-tuned seeds); optional ``unchanged``,
    ``own``, ``own_hybrid``, ``hybrids``, ``hardened`` (a list), ``true``."""
    cmp_, ft = names["comparator"], list(names["regressors"])
    groups: dict[str, list[str]] = {"fine_tuned": ft}
    for key in ("unchanged", "hybrids"):
        if names.get(key):
            groups[key] = list(names[key])
    for key in ("own", "own_hybrid", "true"):
        if names.get(key):
            groups[key] = [names[key]]
    for h in names.get("hardened", []):
        groups[h] = [h]
    groups = {g: s for g, s in groups.items() if all(x in errs for x in s)}
    out: dict[str, Any] = {"ratios": {}, "gap_closed": {}, "prior_share": {}, "versus": {}}
    for c, col in enumerate(COLS):
        logs = {g: pooled_logs(errs, cmp_, s, ordinal, c, rows) for g, s in groups.items()}
        out["ratios"][col] = {g: ratio(v, resamples) for g, v in logs.items()}
        den = logs["fine_tuned"]
        out["gap_closed"][col] = {
            h: share(logs[h], den, resamples) for h in names.get("hardened", []) if h in logs
        }
        out["prior_share"][col] = {
            g: share(logs[g], den, resamples) for g in ("own", "own_hybrid") if g in logs
        }
        # each classical challenger as the control of the fine-tuned regressor
        out["versus"][col] = {
            g: ratio(pooled_logs(errs, s[0], ft, ordinal, c, rows), resamples)
            for g, s in groups.items()
            if g not in ("fine_tuned", "unchanged", "hybrids") and len(s) == 1
        }
    return out
