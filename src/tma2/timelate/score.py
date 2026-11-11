"""Whole-track scoring (spec 013 FR-011 to FR-013).

``row_errors`` gives, at every 5-second row of a period, the error of a track in relative
range, course (°), speed (kt) and position (m). ``summarise`` turns per-row errors of many
periods into the headline: the median over a period's determined rows, then the median over
periods, with a period-clustered bootstrap; and efficiency against the bound on determined rows.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .periods import Period

COLS = ("range", "course_deg", "speed_kt", "position_m")
KT = 1852.0 / 3600.0
UNDETERMINED = 0.5  # a row whose bound on relative range exceeds this is undetermined
Q = 0.6744897501960817


def truth_rows(p: Period) -> np.ndarray:
    """[rows, 6]: target x, y, course, speed, and ownship x, y at the period's rows."""
    a, b = p.first, p.first + p.rows
    return np.stack(
        [p.tgt[a:b, 1], p.tgt[a:b, 2], p.tgt[a:b, 3], p.tgt[a:b, 4], p.own[a:b, 1], p.own[a:b, 2]],
        axis=1,
    ).astype(np.float64)


def row_errors(states: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """[rows, 4] errors (COLS); NaN where the track has no state."""
    tx, ty, tc, ts, ox, oy = truth.T
    rng = np.hypot(tx - ox, ty - oy)
    est = np.hypot(states[:, 0] - ox, states[:, 1] - oy)
    course = np.arctan2(states[:, 2], states[:, 3])
    dc = np.degrees(np.abs((course - tc + np.pi) % (2 * np.pi) - np.pi))
    speed = np.hypot(states[:, 2], states[:, 3])
    out: np.ndarray = np.stack(
        [
            np.abs(est - rng) / rng,
            dc,
            np.abs(speed - ts) / KT,
            np.hypot(states[:, 0] - tx, states[:, 1] - ty),
        ],
        axis=1,
    )
    return out


def strata_of(p: Period, rows: int) -> np.ndarray:
    """Per row: 0 first leg, 1 interior, 2 last leg (by the true manoeuvres in the period)."""
    out = np.ones(rows, dtype=np.int8)
    sp = p.spans()
    first_end = min((s["start_index"] for s in sp), default=rows)
    last_start = max((s["end_index"] for s in sp), default=-1)
    out[:first_end] = 0
    out[last_start + 1 :] = 2
    if not sp:
        out[:] = 0
    return out


def _period_medians(
    e: np.ndarray, period: np.ndarray, keep: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(period ids with at least one kept row, [P, C] median over kept rows; a row with no
    state counts as +inf so that a failed solve is not rewarded)."""
    ids = np.unique(period[keep])
    filled = np.where(np.isfinite(e), e, np.inf)
    med = (
        np.stack([np.median(filled[keep & (period == i)], axis=0) for i in ids])
        if ids.size
        else np.zeros((0, e.shape[1]))
    )
    return ids, med


def summarise(
    errs: dict[str, np.ndarray],
    period: np.ndarray,
    bound: np.ndarray,
    reference: str = "reference",
    level: float = 0.95,
    resamples: int = 2000,
    seed: int = 17,
    keep: np.ndarray | None = None,
) -> dict[str, Any]:
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    use = det if keep is None else det & keep
    out: dict[str, Any] = {
        "rows": int(period.size),
        "rows_determined": int(det.sum()),
        "rows_used": int(use.sum()),
        "periods": int(np.unique(period).size),
        "systems": {},
    }
    rng = np.random.default_rng(seed)
    meds: dict[str, np.ndarray] = {}
    ids = np.unique(period[use])
    for name, e in errs.items():
        i2, m = _period_medians(e, period, use)
        assert np.array_equal(i2, ids)
        meds[name] = m
    draws = [rng.integers(0, ids.size, ids.size) for _ in range(resamples)] if ids.size else []
    lo_q, hi_q = (1 - level) / 2, (1 + level) / 2
    for name, m in meds.items():
        rec: dict[str, Any] = {}
        for c, col in enumerate(COLS):
            b = np.array([np.median(m[d, c]) for d in draws]) if draws else np.zeros(0)
            lo, hi = np.quantile(b, [lo_q, hi_q]) if b.size else (np.nan, np.nan)
            rec[col] = {
                "median": float(np.median(m[:, c])) if ids.size else float("nan"),
                "lo": float(lo),
                "hi": float(hi),
            }
        e = errs[name]
        eff = {}
        for c, col in enumerate(COLS[:3]):
            ok = use & np.isfinite(e[:, c]) & np.isfinite(bound[:, c]) & (bound[:, c] > 0)
            eff[col] = float(np.median(e[ok, c] / bound[ok, c]) / Q) if ok.any() else float("nan")
        rec["efficiency"] = eff
        rec["rows_without_state"] = int((use & ~np.isfinite(e[:, 0])).sum())
        if name != reference and reference in meds:
            r = meds[reference]
            h = float(np.median(m[:, 0]) / np.median(r[:, 0]) - 1.0)
            hb = np.array([np.median(m[d, 0]) / np.median(r[d, 0]) - 1.0 for d in draws])
            rec["headroom_range"] = {
                "value": h,
                "lo": float(np.quantile(hb, lo_q)),
                "hi": float(np.quantile(hb, hi_q)),
            }
        out["systems"][name] = rec
    return out
