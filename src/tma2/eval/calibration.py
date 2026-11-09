"""Calibration of stated uncertainty (spec 008, research R4).

Every estimator's rows are summarised in one array ``cal`` of shape [N, 9]:

| column | meaning |
| --- | --- |
| 0, 1, 2 | absolute error in log range (natural log), course (rad, wrapped), speed (m/s) |
| 3, 4, 5 | the stated standard deviations of the same three quantities |
| 6 | NEES of the 4-state error, eᵀP⁻¹e |
| 7 | 1 if the covariance is usable (``cov_ok``) |
| 8 | 1 if the estimate is plausible (the row is answered) |

A row with no plausible estimate or an unusable covariance has infinite errors, standard
deviations and NEES, and is **not covered** (spec FR-012).

**Spec 009's statement** extends the array to [N, 15] (``WIDTH``):

| column | meaning |
| --- | --- |
| 9 | X, the course arc half-width (rad) |
| 10 | P, the stated probability that the course lies within ±X |
| 11, 12 | the 95% half-widths of ln range ratio and speed |
| 13 | the course log score (log density of the statement at the true course) |
| 14 | 1 if the row carries an explicit statement (spec 009 fields), 0 if derived from its sds |

A row with no explicit statement but a usable covariance is given the Gaussian one: X =
min(Xmax, 1.96 sd), P the normal probability of ±X, half-widths 1.96 sd, a von Mises log score with
the stated sd. A row with neither states nothing: X = P = 0, half-widths 0 (not covered), the
uniform log score ("course unknown").

Measures, each a function of the paired columns so that the scorer's clustered bootstrap
(``eval.bootstrap.bootstrap_clustered_statistic``) gives its interval:

- **coverage** at z (1 for 68.3%, 1.96 for 95%): the share of all rows with
  |e| ≤ z · sd;
- **coverage on answered rows**: the same, among the rows the estimator answers;
- **NEES**: median over all rows (missing = ∞) divided by the χ²₄ median (3.357); and the share
  of rows below the χ²₄ 95% point (9.488);
- **interval score** (Gneiting and Raftery 2007) of the central 95% interval, per quantity in
  natural-log range, degrees and knots: (u − l) + (2/α)(l − y)⁺ + (2/α)(y − u)⁺ with α = 0.05.
  Its mean over rows is the score of record. A missing estimate is charged the 99th percentile of
  the estimator's own finite scores.
- **sharpness**: the median 95% interval width over answered rows.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.physics.uncertainty import unpack_cov

COLS = ("log_range", "course", "speed")
Z68 = 1.0
Z95 = 1.959963984540054
CHI2_4_MEDIAN = 3.356694
CHI2_4_95 = 9.487729
ALPHA = 0.05
KT_PER_MPS = 3600.0 / 1852.0
# interval scores and widths are reported in natural-log range, degrees and knots
UNITS = np.array([1.0, 180.0 / math.pi, KT_PER_MPS])
WIDTH = 15
XMAX = math.radians(45.0)  # spec 009 research R2: the largest usable course arc


def wrap(a: float) -> float:
    """An angle difference wrapped to (−π, π]."""
    return math.atan2(math.sin(a), math.cos(a))


def row_cal(
    est: dict[str, Any] | None,
    truth_state: np.ndarray,
    own_xy: tuple[float, float],
) -> np.ndarray:
    """The [9] calibration row for one estimate (a prediction row or ``None`` when absent).
    ``truth_state`` is (x, y, vx, vy) at the row."""
    out = np.full(WIDTH, np.inf)
    out[7] = out[8] = 0.0
    out[9:15] = (0.0, 0.0, 0.0, 0.0, -math.log(2 * math.pi), 0.0)
    if est is None or not est.get("converged", False):
        return out
    out[8] = 1.0
    tx, ty, tvx, tvy = (float(v) for v in truth_state)
    tr = math.hypot(tx - own_xy[0], ty - own_xy[1])
    out[0] = abs(math.log(float(est["range_m"]) / tr)) if est["range_m"] > 0 and tr > 0 else np.inf
    out[1] = abs(wrap(float(est["course_rad"]) - math.atan2(tvx, tvy)))
    out[2] = abs(float(est["speed_mps"]) - math.hypot(tvx, tvy))
    if not est.get("cov_ok") or est.get("cov_xyvv") is None:
        out[0:3] = np.inf
        return out
    out[7] = 1.0
    out[3] = float(est["log_range_sd"])
    out[4] = float(est["course_sd_rad"])
    out[5] = float(est["speed_sd_mps"])
    p = unpack_cov(est["cov_xyvv"])
    e = np.array(
        [float(est["x_m"]) - tx, float(est["y_m"]) - ty, *_velocity(est) - np.array([tvx, tvy])]
    )
    try:
        out[6] = float(e @ np.linalg.solve(p, e))
    except np.linalg.LinAlgError:
        out[6] = np.inf
    if est.get("course_arc_prob") is not None:
        from tma2.calib.statement import course_log_score as cls

        sd = float(est["course_sd_rad"])
        a = 1.0 / (math.sqrt(float(est["course_conc"])) * sd)
        out[9:15] = (
            float(est["course_arc_rad"]),
            float(est["course_arc_prob"]),
            float(est["range_ratio_q95"]),
            float(est["speed_q95_mps"]),
            float(cls(np.array([out[1]]), np.array([a]),
                                   np.array([float(est["course_mix_p"])]), np.array([sd]))[0]),
            1.0,
        )  # fmt: skip
    else:
        out[9:15] = statement_from_sds(out[None, :9])[0]
    return out


def statement_from_sds(cal9: np.ndarray, xmax: float = XMAX) -> np.ndarray:
    """[N, 6] columns 9–14 for rows that state only Gaussian sds (spec 008 files, the trackers,
    and arrays stored by earlier scoring runs): see the module docstring."""
    from tma2.calib.statement import course_log_score

    n = cal9.shape[0]
    out = np.zeros((n, 6))
    out[:, 4] = -math.log(2 * math.pi)
    ok = (cal9[:, 7] > 0) & (cal9[:, 8] > 0) & np.isfinite(cal9[:, 3:6]).all(axis=1)
    if ok.any():
        sd = cal9[ok, 3:6]
        x = np.minimum(xmax, Z95 * sd[:, 1])
        erf = np.vectorize(math.erf)
        out[ok, 0] = x
        out[ok, 1] = erf(x / (sd[:, 1] * math.sqrt(2.0)))
        out[ok, 2] = Z95 * sd[:, 0]
        out[ok, 3] = Z95 * sd[:, 2]
        e = np.where(np.isfinite(cal9[ok, 1]), cal9[ok, 1], math.pi)
        out[ok, 4] = course_log_score(e, np.ones(ok.sum()), np.full(ok.sum(), 1 - 1e-6), sd[:, 1])
    return out


def widen(cal: np.ndarray) -> np.ndarray:
    """A [N, 9] array (stored before spec 009) widened to [N, 15] by ``statement_from_sds``."""
    if cal.shape[1] >= WIDTH:
        return cal
    return np.concatenate([cal, statement_from_sds(cal)], axis=1)


def _velocity(est: dict[str, Any]) -> np.ndarray:
    c, s = float(est["course_rad"]), float(est["speed_mps"])
    return np.array([s * math.sin(c), s * math.cos(c)])


def covered(cal: np.ndarray, z: float) -> np.ndarray:
    """[N, 3] 0/1: |e| ≤ z · sd, and the row answered with a usable covariance."""
    ok = (cal[:, 7] > 0) & (cal[:, 8] > 0)
    with np.errstate(invalid="ignore"):
        c = cal[:, 0:3] <= z * cal[:, 3:6]
    return (c & ok[:, None]).astype(np.float64)


def interval_score(cal: np.ndarray) -> np.ndarray:
    """[N, 3] 95% interval score per quantity (log range, degrees, knots); ∞ where missing."""
    sd, e = cal[:, 3:6], cal[:, 0:3]
    with np.errstate(invalid="ignore"):
        width = 2 * Z95 * sd
        miss = np.maximum(e - Z95 * sd, 0.0)
        s: np.ndarray = np.asarray((width + (2 / ALPHA) * miss) * UNITS, dtype=np.float64)
    s[~np.isfinite(s)] = np.inf
    return s


def charged(scores: np.ndarray) -> np.ndarray:
    """Missing scores charged the 99th percentile of the column's finite scores."""
    out = scores.copy()
    for j in range(out.shape[1]):
        fin = np.isfinite(out[:, j])
        fill = float(np.percentile(out[fin, j], 99)) if fin.any() else math.nan
        out[~fin, j] = fill
    return out


Stat = Callable[[dict[str, np.ndarray]], float]


@dataclass(frozen=True)
class Measure:
    name: str
    stat: Stat


def _cov(z: float, j: int) -> Stat:
    def f(d: dict[str, np.ndarray]) -> float:
        return float(covered(d["c"], z)[:, j].mean())

    return f


def _score(j: int) -> Stat:
    def f(d: dict[str, np.ndarray]) -> float:
        return float(charged(interval_score(d["c"]))[:, j].mean())

    return f


def _answered_stat(j: int) -> Stat:
    def f(d: dict[str, np.ndarray]) -> float:
        return _answered(d["c"], j)

    return f


def _sharp_stat(j: int) -> Stat:
    def f(d: dict[str, np.ndarray]) -> float:
        return _sharp(d["c"], j)

    return f


def _nees_ratio(d: dict[str, np.ndarray]) -> float:
    return float(np.median(d["c"][:, 6]) / CHI2_4_MEDIAN)


def _nees_within(d: dict[str, np.ndarray]) -> float:
    return float((d["c"][:, 6] <= CHI2_4_95).mean())


def _no_estimate(d: dict[str, np.ndarray]) -> float:
    return float(1.0 - (d["c"][:, 8] > 0).mean())


def _st_hit(c: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        hit: np.ndarray = (c[:, 1] <= c[:, 9]) & (c[:, 9] > 0)
    return hit.astype(np.float64)


def _st_reliability(d: dict[str, np.ndarray]) -> float:
    """Hit rate minus mean stated P (spec 009 G4-b): 0 when P is reliable."""
    c = d["c"]
    return float(_st_hit(c).mean() - c[:, 10].mean())


def _st_mean_p(d: dict[str, np.ndarray]) -> float:
    return float(d["c"][:, 10].mean())


def _st_mean_x(d: dict[str, np.ndarray]) -> float:
    return float(np.degrees(d["c"][:, 9].mean()))


def _st_log_gain(d: dict[str, np.ndarray]) -> float:
    """Mean course log score minus the uniform's (positive: more informative than "unknown")."""
    return float(d["c"][:, 13].mean() + math.log(2 * math.pi))


def _st_cov(j: int) -> Stat:
    def f(d: dict[str, np.ndarray]) -> float:
        c = d["c"]
        e, q = c[:, 0 if j == 0 else 2], c[:, 11 + j]
        with np.errstate(invalid="ignore"):
            return float(((e <= q) & (q > 0)).mean())

    return f


def _st_is(j: int) -> Stat:
    def f(d: dict[str, np.ndarray]) -> float:
        c = d["c"]
        e, q = c[:, 0 if j == 0 else 2], c[:, 11 + j]
        with np.errstate(invalid="ignore"):
            s = 2 * q + (2 / ALPHA) * np.maximum(e - q, 0.0)
        s = np.where(np.isfinite(s), s, np.nan)
        fill = np.nanpercentile(s, 99) if np.isfinite(s).any() else math.nan
        return float(np.where(np.isnan(s), fill, s).mean() * (1.0 if j == 0 else KT_PER_MPS))

    return f


def reliability_bins(c: np.ndarray, bins: int = 5) -> list[dict[str, float]]:
    """Equal-count bins of stated P: {mean P, hit rate, rows} (spec 009 G4-b, points)."""
    order = np.argsort(c[:, 10], kind="stable")
    hit = _st_hit(c)
    out = []
    for i in np.array_split(order, bins):
        if len(i):
            out.append({"p": float(c[i, 10].mean()), "hit": float(hit[i].mean()), "rows": len(i)})
    return out


def measures() -> list[Measure]:
    """Every per-estimator measure as a statistic of its ``cal`` column (name ``c``)."""
    out: list[Measure] = []
    for j, q in enumerate(COLS):
        out.append(Measure(f"coverage68_{q}", _cov(Z68, j)))
        out.append(Measure(f"coverage95_{q}", _cov(Z95, j)))
        out.append(Measure(f"coverage95_answered_{q}", _answered_stat(j)))
        out.append(Measure(f"interval_score95_{q}", _score(j)))
        out.append(Measure(f"sharpness95_{q}", _sharp_stat(j)))
    out.append(Measure("nees_median_ratio", _nees_ratio))
    out.append(Measure("nees_within95", _nees_within))
    out.append(Measure("no_estimate_share", _no_estimate))
    out.append(Measure("statement_reliability", _st_reliability))
    out.append(Measure("statement_mean_p", _st_mean_p))
    out.append(Measure("statement_mean_arc_deg", _st_mean_x))
    out.append(Measure("statement_course_log_gain", _st_log_gain))
    out.append(Measure("statement_coverage95_log_range", _st_cov(0)))
    out.append(Measure("statement_coverage95_speed", _st_cov(1)))
    out.append(Measure("statement_interval_score_log_range", _st_is(0)))
    out.append(Measure("statement_interval_score_speed_kt", _st_is(1)))
    return out


def _answered(cal: np.ndarray, j: int) -> float:
    ok = (cal[:, 7] > 0) & (cal[:, 8] > 0)
    return float(covered(cal[ok], Z95)[:, j].mean()) if ok.any() else math.nan


def _sharp(cal: np.ndarray, j: int) -> float:
    ok = (cal[:, 7] > 0) & (cal[:, 8] > 0)
    return float(np.median(2 * Z95 * cal[ok, 3 + j]) * UNITS[j]) if ok.any() else math.nan


def summarise(
    cal: np.ndarray,
    cluster: np.ndarray,
    level: float,
    resamples: int,
    names: set[str] | None = None,
) -> dict[str, dict[str, float]]:
    """{measure: {value, lo, hi}} with the scorer's clustered bootstrap; ``names`` limits which
    measures get intervals (the rest are points, lo = hi = NaN)."""
    from tma2.eval.bootstrap import bootstrap_clustered_statistic

    out: dict[str, dict[str, float]] = {}
    for m in measures():
        if names is None or m.name in names:
            si = bootstrap_clustered_statistic({"c": cal}, cluster, m.stat, level, resamples)
            out[m.name] = {"value": si.value, "lo": si.lo, "hi": si.hi}
        else:
            out[m.name] = {"value": m.stat({"c": cal}), "lo": math.nan, "hi": math.nan}
    return out


SLICE_INTERVALS = {
    "coverage95_log_range",
    "coverage95_course",
    "coverage95_speed",
    "nees_median_ratio",
    "nees_within95",
    "statement_reliability",
    "statement_coverage95_log_range",
    "statement_coverage95_speed",
}


def report(
    cals: dict[str, np.ndarray],
    cluster: np.ndarray,
    slices: dict[str, dict[str, np.ndarray]],
    level: float,
    resamples: int,
    gross: dict[str, np.ndarray],
) -> dict[str, Any]:
    """{estimator: {"overall": measures, "by_<slice>": {value: measures}, "by_gross": …}}.

    ``slices`` maps a slice name to {label: row mask}, shared by every estimator. Each
    estimator also gets ``by_gross`` from its own rows (``gross[name]``: the scorer's relative
    range error over 0.5, or no estimate, as Gate 2's gross rate). Overall measures all carry
    intervals; per-slice ones only ``SLICE_INTERVALS``."""
    out: dict[str, Any] = {}
    for name, cal in cals.items():
        rec: dict[str, Any] = {"overall": summarise(cal, cluster, level, resamples)}
        rec["reliability_bins"] = reliability_bins(cal)
        g = gross[name]
        own = {"gross": {"gross": g, "not_gross": ~g}}
        for sname, labels in {**slices, **own}.items():
            rec[f"by_{sname}"] = {
                lab: {"n_rows": int(mask.sum())}
                | summarise(cal[mask], cluster[mask], level, resamples, SLICE_INTERVALS)
                for lab, mask in labels.items()
                if mask.sum() > 0
            }
        out[name] = rec
    return out
