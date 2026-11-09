"""Gate 5's criteria (spec 010 FR-030, research R7; proposed in the SRD amendment, fixed in the
decision record).

Computed on one scoring run's per-row statement columns (``eval.calibration``: 9 X, 10 P, 11-12
half-widths, 13 course log score, 15 proxy flag) with the scorer's scenario-clustered bootstrap.
``slices`` maps a slice name to its per-row labels; the proxy's two states come from the carried
statement's own flag column. A slice label with fewer than ``min_slice_rows`` rows is reported,
not gated.

* **G5-a (intervals):** range and speed coverage: overall wholly inside ``coverage95_overall``;
  per gated slice not wholly outside ``coverage95_slice``.
* **G5-b (reliability):** overall hit − P wholly inside ±``reliability_overall``; the calibration
  slope's interval wholly inside ``slope``; per gated slice, hit − P not wholly outside
  ±``reliability_slice`` and its point inside ±``reliability_slice_point``.
* **G5-c (usefulness):** the course log gain over "unknown" wholly above 0; the AUC of P for a hit
  wholly above ``auc_min``.
* **G5-d (learning):** the head's standardised summed score minus the better classical control's
  wholly below 0 (each component divided by that control's mean); void if the encoder-only
  shuffle's rule failed on validation.
* **G5-e (consistency):** points identical to the uncalibrated E's; every stated row's arc mass
  equals its P (checked by the predict step and recorded: ``max_mass_error``).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.calib.gate import FAIL as FAIL
from tma2.calib.gate import INCONCLUSIVE as INCONCLUSIVE
from tma2.calib.gate import PASS as PASS
from tma2.calib.gate import _interval, all_of, below, inside
from tma2.calib.gate4 import scale_of, score_difference
from tma2.eval import calibration as ec


def not_outside(iv: dict[str, float], lo: float, hi: float) -> str:
    """A per-slice "no evidence of miscalibration" check: fail only when the interval lies wholly
    outside [lo, hi], else pass (spec 010 SC-003: with a point band, small calibrated slices were
    inconclusive in a quarter of synthetic datasets)."""
    if iv["hi"] < lo or iv["lo"] > hi:
        return FAIL
    return PASS


def above(iv: dict[str, float], limit: float) -> str:
    return below({"value": -iv["value"], "lo": -iv["hi"], "hi": -iv["lo"]}, -limit)


def _rel(d: dict[str, np.ndarray]) -> float:
    c = d["c"]
    return float(ec._st_hit(c).mean() - c[:, 10].mean())


def _cov(j: int):  # type: ignore[no-untyped-def]
    return {m.name: m.stat for m in ec.measures()}[
        "statement_coverage95_log_range" if j == 0 else "statement_coverage95_speed"
    ]


def slice_table(
    cal: np.ndarray,
    cluster: np.ndarray,
    slices: dict[str, np.ndarray],
    bands: dict[str, Any],
    level: float,
    resamples: int,
) -> list[dict[str, Any]]:
    """Per slice label: rows, gated?, hit − P and coverage intervals, and their verdicts."""
    out: list[dict[str, Any]] = []
    rs, rp = float(bands["reliability_slice"]), float(bands["reliability_slice_point"])
    clo, chi = bands["coverage95_slice"]
    for sname, labels in slices.items():
        for lab in sorted(set(labels.tolist()) - {""}):
            m = labels == lab
            n = int(m.sum())
            rec: dict[str, Any] = {"slice": sname, "label": lab, "rows": n}
            rec["gated"] = n >= int(bands["min_slice_rows"])
            if n < 20:
                out.append(rec)
                continue
            sub, cl = cal[m], cluster[m]
            rel = _interval(_rel, {"c": sub}, cl, level, resamples)
            cov = {
                q: _interval(_cov(j), {"c": sub}, cl, level, resamples)
                for j, q in enumerate(("log_range", "speed"))
            }
            rec["reliability"] = rel
            rec["coverage"] = cov
            v_rel = not_outside(rel, -rs, rs)
            if abs(rel["value"]) > rp:
                v_rel = FAIL  # the point is outside the point band (off by default: R7 as revised)
            rec["verdict_reliability"] = v_rel
            rec["verdict_coverage"] = all_of([not_outside(v, clo, chi) for v in cov.values()])
            out.append(rec)
    return out


def criteria(
    cal_e: np.ndarray,
    cal_controls: dict[str, np.ndarray],
    err_e: np.ndarray,
    err_raw: np.ndarray,
    cluster: np.ndarray,
    slices: dict[str, np.ndarray],
    bands: dict[str, Any],
    encshuf_rule: str,
    level: float,
    resamples: int,
    max_mass_error: float = 0.0,
) -> dict[str, Any]:
    """G5-a…G5-e for the carried stated E against the classical controls (``cal_controls``:
    name → array; the better one is the control of record)."""
    meas = {m.name: m.stat for m in ec.measures()}
    sl = dict(slices)
    fl = cal_e[:, 15]
    if np.isfinite(fl).any():
        sl["proxy"] = np.where(fl == 1.0, "flagged", np.where(fl == 0.0, "not_flagged", ""))
    table = slice_table(cal_e, cluster, sl, bands, level, resamples)
    gated = [r for r in table if r.get("gated") and "reliability" in r]

    def iv(name: str) -> dict[str, float]:
        return _interval(meas[name], {"c": cal_e}, cluster, level, resamples)

    a_overall = {q: iv(f"statement_coverage95_{q}") for q in ("log_range", "speed")}
    a = all_of(
        [inside(v, *bands["coverage95_overall"]) for v in a_overall.values()]
        + [r["verdict_coverage"] for r in gated]
    )
    r = float(bands["reliability_overall"])
    b_overall = _interval(_rel, {"c": cal_e}, cluster, level, resamples)
    b_slope = iv("statement_slope")
    b = all_of(
        [inside(b_overall, -r, r), inside(b_slope, *bands["slope"])]
        + [x["verdict_reliability"] for x in gated]
    )
    c_gain, c_auc = iv("statement_course_log_gain"), iv("statement_auc")
    c = all_of([above(c_gain, 0.0), above(c_auc, float(bands["auc_min"]))])
    # the control of record: the classical control with the lower mean summed score, all on the
    # first control's scale (the temperature's, as Gate 4); G5-d then uses its own scale
    base = scale_of(next(iter(cal_controls.values())))
    means = {n: float(np.mean(_summed(x, base))) for n, x in cal_controls.items()}
    ref_name = min(means, key=lambda n: means[n])
    ref = cal_controls[ref_name]
    d_iv = score_difference(cal_e, ref, scale_of(ref), cluster, level, resamples)
    d = below(d_iv, 0.0)
    if d == PASS and encshuf_rule != PASS:
        d = FAIL  # void: recorded as not passed
    same = bool(np.array_equal(err_e, err_raw))
    e = PASS if same and max_mass_error <= float(bands["consistency_tol"]) else FAIL
    res: dict[str, Any] = {
        "g5a": a,
        "g5b": b,
        "g5c": c,
        "g5d": d,
        "g5e": e,
        "control_of_record": ref_name,
        "control_means": means,
        "max_mass_error": max_mass_error,
        "encshuf_rule": encshuf_rule,
        "intervals": {
            "g5a": a_overall,
            "g5b": {"overall": b_overall, "slope": b_slope},
            "g5c": {"log_gain": c_gain, "auc": c_auc},
            "g5d": d_iv,
        },
        "slices": table,
    }
    res["overall"] = all_of([res[k] for k in ("g5a", "g5b", "g5c", "g5d", "g5e")])
    return res


def _summed(c: np.ndarray, scale: dict[str, float]) -> np.ndarray:
    from tma2.calib.gate4 import summed_score

    return summed_score(c, scale)


def encshuf_rule(encshuf_minus_control: dict[str, dict[str, float]]) -> str:
    """Validation: no encoder-only shuffle may beat the control of record (difference wholly
    below zero) for a G5-d pass to stand."""
    return FAIL if any(below(v, 0.0) == PASS for v in encshuf_minus_control.values()) else PASS
