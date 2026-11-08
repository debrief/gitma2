"""Gate 3's criteria (spec 008 FR-030; proposed in the SRD amendment, fixed in the decision).

All are computed on one scoring run's per-row calibration arrays (``eval.calibration``), with
the scorer's scenario-clustered paired bootstrap:

* **G3-a (coverage):** for each of log range, course and speed, the carried calibrated E's 95%
  coverage over all rows (missing = not covered), interval wholly inside the band → pass; wholly
  outside → fail; otherwise inconclusive. The quantity verdicts combine by ``all_of``.
* **G3-b (consistency):** the median NEES over the χ²₄ median, interval wholly inside its band.
* **G3-c (learning):** the head's mean 95% interval score in log range minus the temperature
  control's, paired, wholly below zero; a pass is void (not passed) if the shuffled rule failed
  on validation.
* **G3-d (no regression):** the calibrated E's point errors equal the uncalibrated E's on every
  row (FR-020), so Gate 2's G2-a…G2-d carry over; checked exactly.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.eval import calibration as ec
from tma2.eval.bootstrap import bootstrap_clustered_statistic

PASS, FAIL, INCONCLUSIVE = "pass", "fail", "inconclusive"


def inside(iv: dict[str, float], lo: float, hi: float) -> str:
    if lo <= iv["lo"] and iv["hi"] <= hi and lo <= iv["value"] <= hi:
        return PASS
    if iv["hi"] < lo or iv["lo"] > hi:
        return FAIL
    return INCONCLUSIVE


def below(iv: dict[str, float], limit: float) -> str:
    if iv["hi"] < limit and iv["value"] < limit:
        return PASS
    if iv["lo"] > limit:
        return FAIL
    return INCONCLUSIVE


def all_of(vs: list[str]) -> str:
    if all(v == PASS for v in vs):
        return PASS
    if any(v == FAIL for v in vs):
        return FAIL
    return INCONCLUSIVE


def _interval(
    stat: Any, cols: dict[str, np.ndarray], cluster: np.ndarray, level: float, n: int
) -> dict[str, float]:
    si = bootstrap_clustered_statistic(cols, cluster, stat, level, n)
    return {"value": si.value, "lo": si.lo, "hi": si.hi}


def score_difference(
    head: np.ndarray, temp: np.ndarray, cluster: np.ndarray, level: float, n: int
) -> dict[str, float]:
    """Mean 95% interval score in log range, head − temperature, paired."""

    def stat(d: dict[str, np.ndarray]) -> float:
        a = ec.charged(ec.interval_score(d["h"]))[:, 0].mean()
        b = ec.charged(ec.interval_score(d["t"]))[:, 0].mean()
        return float(a - b)

    return _interval(stat, {"h": head, "t": temp}, cluster, level, n)


def criteria(
    cal_e: np.ndarray,
    cal_temp: np.ndarray,
    err_e: np.ndarray,
    err_raw: np.ndarray,
    cluster: np.ndarray,
    bands: dict[str, Any],
    shuffled_rule: str,
    level: float,
    resamples: int,
) -> dict[str, Any]:
    """G3-a…G3-d for the carried calibrated E (``cal_e``, ``err_e``) against the temperature
    control (``cal_temp``) and the uncalibrated E (``err_raw``)."""
    meas = {m.name: m for m in ec.measures()}
    a_iv = {
        q: _interval(meas[f"coverage95_{q}"].stat, {"c": cal_e}, cluster, level, resamples)
        for q in ec.COLS
    }
    lo, hi = bands["coverage95"]
    a = {q: inside(iv, lo, hi) for q, iv in a_iv.items()}
    b_iv = _interval(meas["nees_median_ratio"].stat, {"c": cal_e}, cluster, level, resamples)
    b = inside(b_iv, *bands["nees_median_ratio"])
    c_iv = score_difference(cal_e, cal_temp, cluster, level, resamples)
    c = below(c_iv, 0.0)
    if c == PASS and shuffled_rule != PASS:
        c = FAIL  # void: recorded as not passed
    same = bool(np.array_equal(err_e, err_raw))
    d = PASS if same else FAIL
    out: dict[str, Any] = {
        "g3a": all_of(list(a.values())),
        "g3a_by_quantity": a,
        "g3b": b,
        "g3c": c,
        "g3d": d,
        "intervals": {"g3a": a_iv, "g3b": b_iv, "g3c": c_iv},
        "shuffled_rule": shuffled_rule,
    }
    out["overall"] = all_of([out["g3a"], out["g3b"], out["g3c"], out["g3d"]])
    return out


def shuffled_rule(shuffled_minus_temp: dict[str, float]) -> str:
    """Validation: the shuffled head must not beat the temperature (its interval-score
    difference wholly below zero) for a G3-c pass to stand."""
    return FAIL if below(shuffled_minus_temp, 0.0) == PASS else PASS
