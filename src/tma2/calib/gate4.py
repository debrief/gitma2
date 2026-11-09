"""Gate 4's criteria (spec 009; proposed in the SRD amendment, fixed in the decision record).

Computed on one scoring run's per-row statement columns (``eval.calibration``, columns 9–14),
with the scorer's scenario-clustered bootstrap:

* **G4-a (intervals):** range and speed 95% coverage (|e| ≤ q; a row stating nothing is not
  covered), each interval wholly inside the band.
* **G4-b (reliability):** hit rate minus mean stated P, interval wholly inside ±``reliability``;
  and in each of ``bins`` equal-count bins of P, |hit − P| within ±``reliability_bin`` (points).
* **G4-c (informative):** the mean course log score minus the uniform's, interval wholly above
  zero; and mean P at least ``min_mean_p`` (point).
* **G4-d (learning):** the head's standardised summed score (course negative log score and the
  two interval scores, each divided by the temperature's mean on the same rows, ``scale_of``)
  minus the temperature's, paired, wholly below zero; void (not passed) if the shuffled rule
  failed on validation.
* **G4-e (no regression):** the stated E's point errors equal the uncalibrated E's on every row.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.calib.gate import FAIL as FAIL
from tma2.calib.gate import PASS as PASS
from tma2.calib.gate import _interval, all_of, below, inside
from tma2.eval import calibration as ec


def components(c: np.ndarray) -> np.ndarray:
    """[N, 3] course negative log score and the range and speed 95% interval scores; a missing
    interval score is charged the 99th percentile of the finite ones, as the scorer does."""
    with np.errstate(invalid="ignore"):
        is_r = 2 * c[:, 11] + (2 / ec.ALPHA) * np.maximum(c[:, 0] - c[:, 11], 0.0)
        is_s = 2 * c[:, 12] + (2 / ec.ALPHA) * np.maximum(c[:, 2] - c[:, 12], 0.0)
    both = ec.charged(np.stack([np.where(np.isfinite(is_r), is_r, np.inf),
                                np.where(np.isfinite(is_s), is_s, np.inf)], axis=1))  # fmt: skip
    return np.stack([-c[:, 13], both[:, 0], both[:, 1]], axis=1)


def scale_of(c: np.ndarray) -> dict[str, float]:
    """The control's mean of each component (absolute, so a negative mean log loss still scales)."""
    m = np.abs(components(c).mean(axis=0)) + 1e-12
    return {"course": float(m[0]), "range": float(m[1]), "speed": float(m[2])}


def summed_score(c: np.ndarray, scale: dict[str, float]) -> np.ndarray:
    """[N] standardised summed score (lower is better)."""
    k = components(c)
    out: np.ndarray = (
        k[:, 0] / scale["course"] + k[:, 1] / scale["range"] + k[:, 2] / scale["speed"]
    )
    return out


def score_difference(
    head: np.ndarray,
    temp: np.ndarray,
    scale: dict[str, float],
    cluster: np.ndarray,
    level: float,
    n: int,
) -> dict[str, float]:
    """Mean standardised summed score, head − temperature, paired."""

    def stat(d: dict[str, np.ndarray]) -> float:
        return float(summed_score(d["h"], scale).mean() - summed_score(d["t"], scale).mean())

    return _interval(stat, {"h": head, "t": temp}, cluster, level, n)


def above(iv: dict[str, float], limit: float) -> str:
    neg = {"value": -iv["value"], "lo": -iv["hi"], "hi": -iv["lo"]}
    return below(neg, -limit)


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
    """G4-a…G4-e for the carried stated E (``cal_e``, ``err_e``) against the temperature's
    statement (``cal_temp``) and the uncalibrated E (``err_raw``)."""
    meas = {m.name: m for m in ec.measures()}

    def iv(name: str) -> dict[str, float]:
        return _interval(meas[name].stat, {"c": cal_e}, cluster, level, resamples)

    lo, hi = bands["coverage95"]
    a_iv = {q: iv(f"statement_coverage95_{q}") for q in ("log_range", "speed")}
    a = {q: inside(v, lo, hi) for q, v in a_iv.items()}
    r = float(bands["reliability_overall"])
    b_iv = iv("statement_reliability")
    b_bins = ec.reliability_bins(cal_e, int(bands["bins"]))
    rb = float(bands["reliability_bin"])
    bins_ok = all(abs(x["hit"] - x["p"]) <= rb for x in b_bins)
    b = all_of([inside(b_iv, -r, r), PASS if bins_ok else FAIL])
    c_iv = iv("statement_course_log_gain")
    mean_p = float(meas["statement_mean_p"].stat({"c": cal_e}))
    c = all_of([above(c_iv, 0.0), PASS if mean_p >= float(bands["min_mean_prob"]) else FAIL])
    scale = scale_of(cal_temp)
    d_iv = score_difference(cal_e, cal_temp, scale, cluster, level, resamples)
    d = below(d_iv, 0.0)
    if d == PASS and shuffled_rule != PASS:
        d = FAIL  # void: recorded as not passed
    e = PASS if bool(np.array_equal(err_e, err_raw)) else FAIL
    out: dict[str, Any] = {
        "g4a": all_of(list(a.values())),
        "g4a_by_quantity": a,
        "g4b": b,
        "g4b_bins": b_bins,
        "g4c": c,
        "g4c_mean_p": mean_p,
        "g4d": d,
        "g4e": e,
        "g4d_scale": scale,
        "intervals": {"g4a": a_iv, "g4b": b_iv, "g4c": c_iv, "g4d": d_iv},
        "shuffled_rule": shuffled_rule,
    }
    out["overall"] = all_of([out[k] for k in ("g4a", "g4b", "g4c", "g4d", "g4e")])
    return out


def shuffled_rule(shuffled_minus_temp: dict[str, float]) -> str:
    """Validation: the shuffled head must not beat the temperature (its summed-score difference
    wholly below zero) for a G4-d pass to stand."""
    return FAIL if below(shuffled_minus_temp, 0.0) == PASS else PASS
