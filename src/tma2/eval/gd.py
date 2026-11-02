"""Gate D (SRD Annex A §A.5; spec 004 FR-029–FR-031; research R8, R10).

On the σ = 1° slice of the test split, per carried detector variant:

* ``D-delay``: median detection delay ÷ the best control's (CUSUM or GLR, whichever has the
  lower median delay on the scored split), each over the manoeuvres it detects; wholly below 1.
* ``D-miss``: miss rate − the best control's (the lower miss rate); wholly at or below 0.
* ``D-false``: fraction of held-leg G5 rows flagged; wholly below the D3 limit (5%, or the frozen
  IMM's own validation rate at μ_CT > 0.5 if lower; fixed in the decision record).
* ``D-downstream-all``: median range error of the physics layer fed by the detector's knots ÷ the
  IMM's, all G5 rows; wholly below 1.
* ``D-downstream-settled-{range,course,speed}``: medians on settled G5 rows ÷ batch least
  squares'; each wholly below 1.1.
* Reported, not gated: ``D-kind`` (kind accuracy), ``D-gap`` (share of the batch least squares →
  oracle gap in median range error recovered, all G5 rows).

Intervals: scenario-clustered paired percentile bootstraps at the decision's level (D2: 97.5%)
with gitma's seeded PRNG. Every statistic of one call uses the same resampled scenario sets, so the
detector and its comparators are paired. Errors use the one convergence definition
(``errors.plausible_row``): a missing or implausible row scores +∞ and is gross.

A check passes when its point and its whole interval meet the limit, fails when the interval lies
wholly beyond it, and is inconclusive otherwise. A variant passes when every gated check passes and
fails when any fails; the gate passes when a variant passes, fails when every variant fails, and is
inconclusive otherwise. The validation rule carries a variant only if every gated check's point
meets its limit and none fails.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numba import njit

from tma2.detect.matching import ScenarioDetection
from tma2.sim.prng import create_rng, uniform_int

from .bootstrap import BOOTSTRAP_SEED, bootstrap_clustered_quantile_ratio
from .errors import Truth, row_error
from .rows import G5_GATE_MIN, G5_SLICE_SIGMA_RAD, settled_row
from .stats import ascending, percentile

DELAY_LIMIT = 1.0
MISS_LIMIT = 0.0
DOWNSTREAM_ALL_LIMIT = 1.0
SETTLED_LIMIT = 1.1
GATED = (
    "D-delay",
    "D-miss",
    "D-false",
    "D-downstream-all",
    "D-downstream-settled-range",
    "D-downstream-settled-course",
    "D-downstream-settled-speed",
)
METRICS = ("range_rel", "course_deg", "speed_kt")
LABEL = {"range_rel": "range", "course_deg": "course", "speed_kt": "speed"}


@dataclass
class GdCheck:
    name: str
    result: str  # pass | fail | inconclusive | reported
    value: float
    lo: float
    hi: float
    limit: float | None
    n: int
    detail: str = ""


@dataclass
class G5Rows:
    """σ = 1° G5 rows of a split and each estimator's errors there (+∞ where gross)."""

    scenario: np.ndarray  # [N] scenario index (the cluster)
    settled: np.ndarray  # [N] bool
    errors: dict[str, dict[str, np.ndarray]] = field(default_factory=dict)


def g5_rows(truths: Sequence[Truth]) -> list[tuple[Truth, int, bool]]:
    out = []
    for t in truths:
        if abs(float(t.meta["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) > 1e-6:
            continue
        for m in G5_GATE_MIN:
            k = t.zig_index + int(round(m * 60 / t.dt))
            if k < t.samples:
                out.append((t, k, settled_row(t.meta, k)))
    return out


def downstream_rows(
    truths: Sequence[Truth], preds: dict[str, dict[int, dict[float, dict[str, Any]]]]
) -> G5Rows:
    """Errors at the σ = 1° G5 rows for each estimator's per-timestep predictions
    (``preds[name][scenario][timestamp_s] = row``)."""
    rows = g5_rows(truths)
    out = G5Rows(
        scenario=np.array([t.index for t, _, _ in rows], dtype=np.int64),
        settled=np.array([s for _, _, s in rows], dtype=bool),
    )
    for name, p in preds.items():
        errs = {m: np.full(len(rows), math.inf) for m in METRICS}
        for i, (t, k, _) in enumerate(rows):
            r = p.get(t.index, {}).get(float(t.own[k, 0]))
            if r is None:
                continue
            e = row_error(t, r, "plausible")
            for m in METRICS:
                errs[m][i] = getattr(e, m)
        out.errors[name] = errs
    return out


@njit(cache=True)
def _draw_picks(seed: np.uint64, g: int, resamples: int) -> np.ndarray:
    """[resamples, g] cluster positions, resample-major (gitma's draw order)."""
    rng = create_rng(seed)
    out = np.empty((resamples, g), dtype=np.int64)
    for r in range(resamples):
        for i in range(g):
            out[r, i] = uniform_int(rng, g)
    return out


class Resampler:
    """Shared scenario resamples (gitma's PRNG): ``picks[r]`` are positions into ``scenarios``."""

    def __init__(self, scenarios: Sequence[int], resamples: int, seed: int = BOOTSTRAP_SEED):
        self.scenarios = list(scenarios)
        self.picks = list(_draw_picks(np.uint64(seed), len(self.scenarios), resamples))

    def interval(
        self, stat: Callable[[np.ndarray], float], level: float
    ) -> tuple[float, float, float]:
        """(point, lo, hi) of ``stat`` evaluated on all positions and on each resample."""
        point = stat(np.arange(len(self.scenarios), dtype=np.int64))
        vals = ascending(np.array([stat(p) for p in self.picks]))
        tail = (1 - level) / 2
        return point, percentile(vals, tail), percentile(vals, 1 - tail)


def _below(
    name: str, v: tuple[float, float, float], limit: float, n: int, detail: str = ""
) -> GdCheck:
    point, lo, hi = v
    if point < limit and hi < limit:
        res = "pass"
    elif lo >= limit:
        res = "fail"
    else:
        res = "inconclusive"
    return GdCheck(name, res, point, lo, hi, limit, n, detail)


def _at_or_below(
    name: str, v: tuple[float, float, float], limit: float, n: int, detail: str = ""
) -> GdCheck:
    point, lo, hi = v
    if point <= limit and hi <= limit:
        res = "pass"
    elif lo > limit:
        res = "fail"
    else:
        res = "inconclusive"
    return GdCheck(name, res, point, lo, hi, limit, n, detail)


def _per_scenario(scores: Sequence[ScenarioDetection], order: list[int]) -> dict[str, Any]:
    """Per-scenario aggregates aligned with ``order`` (scenario indices)."""
    by = {sc.record.scenario_index: sc for sc in scores}
    delays: list[np.ndarray] = []
    missed = np.zeros(len(order))
    resolved = np.zeros(len(order))
    flagged = np.zeros(len(order))
    g5 = np.zeros(len(order))
    for i, s in enumerate(order):
        sc = by.get(s)
        if sc is None:
            raise ValueError(f"no detection record for scenario {s}")
        spans = sc.record.spans or []
        delays.append(
            np.array(
                [x.delay_s for x in spans if x.outcome == "detected" and x.delay_s is not None]
            )
        )
        missed[i] = sum(1 for x in spans if x.outcome == "missed")
        resolved[i] = sum(1 for x in spans if x.outcome != "unresolved")
        flagged[i] = sc.record.held_leg_g5_flagged
        g5[i] = sc.record.held_leg_g5_rows
    return {"delays": delays, "missed": missed, "resolved": resolved, "flagged": flagged, "g5": g5}


def _median_delay(agg: dict[str, Any], picks: np.ndarray) -> float:
    """Median delay over the detected manoeuvres; +∞ when none is detected (a detector that never
    alarms has no finite delay, so its D-delay ratio is +∞ and a control's that never alarms
    makes the ratio 0)."""
    d = [agg["delays"][i] for i in picks]
    x = np.concatenate(d) if d else np.zeros(0)
    return percentile(ascending(x), 0.5) if x.size else math.inf


def _rate(num: np.ndarray, den: np.ndarray, picks: np.ndarray) -> float:
    s = float(den[picks].sum())
    return float(num[picks].sum()) / s if s > 0 else math.nan


def _div(a: float, b: float) -> float:
    with np.errstate(divide="ignore", invalid="ignore"):
        return float(np.float64(a) / np.float64(b))


def variant_checks(
    detector: Sequence[ScenarioDetection],
    controls: Mapping[str, Sequence[ScenarioDetection]],
    rows: G5Rows,
    downstream: str,
    false_alarm_limit: float,
    level: float,
    resamples: int,
    seed: int = BOOTSTRAP_SEED,
) -> list[GdCheck]:
    """Gate D's checks for one detector (σ = 1° scenarios only in every input)."""
    order = sorted(sc.record.scenario_index for sc in detector)
    rs = Resampler(order, resamples, seed)
    det = _per_scenario(detector, order)
    ctl = {k: _per_scenario(v, order) for k, v in controls.items()}
    all_pos = np.arange(len(order), dtype=np.int64)
    checks: list[GdCheck] = []
    # D-delay against the control with the lower median delay on this split.
    best_delay = min(ctl, key=lambda k: (_median_delay(ctl[k], all_pos), k))
    v = rs.interval(lambda p: _div(_median_delay(det, p), _median_delay(ctl[best_delay], p)), level)
    n_det = int(sum(a.size for a in det["delays"]))
    checks.append(_below("D-delay", v, DELAY_LIMIT, n_det, f"against {best_delay}"))
    # D-miss against the control with the lower miss rate.
    best_miss = min(ctl, key=lambda k: (_rate(ctl[k]["missed"], ctl[k]["resolved"], all_pos), k))
    c = ctl[best_miss]
    v = rs.interval(
        lambda p: _rate(det["missed"], det["resolved"], p) - _rate(c["missed"], c["resolved"], p),
        level,
    )
    checks.append(
        _at_or_below("D-miss", v, MISS_LIMIT, int(det["resolved"].sum()), f"against {best_miss}")
    )
    v = rs.interval(lambda p: _rate(det["flagged"], det["g5"], p), level)
    checks.append(_below("D-false", v, false_alarm_limit, int(det["g5"].sum())))
    # Downstream: rows of the scored scenarios, gitma's clustered quantile-ratio bootstrap.
    keep = np.isin(rows.scenario, np.array(order, dtype=np.int64))
    e = {k: {m: a[keep] for m, a in v_.items()} for k, v_ in rows.errors.items()}
    cl = rows.scenario[keep]
    st = rows.settled[keep]
    iv = bootstrap_clustered_quantile_ratio(
        e[downstream]["range_rel"], e["imm"]["range_rel"], cl, 0.5, level, resamples, seed
    )
    checks.append(
        _below("D-downstream-all", (iv.ratio, iv.lo, iv.hi), DOWNSTREAM_ALL_LIMIT, int(keep.sum()))
    )
    for m in METRICS:
        iv = bootstrap_clustered_quantile_ratio(
            e[downstream][m][st], e["least_squares"][m][st], cl[st], 0.5, level, resamples, seed
        )
        checks.append(
            _below(
                f"D-downstream-settled-{LABEL[m]}",
                (iv.ratio, iv.lo, iv.hi),
                SETTLED_LIMIT,
                int(st.sum()),
            )
        )
    # Reported: kind accuracy and the gap recovered.
    kind_n = sum(sc.kind_scored for sc in detector)
    kind_ok = sum(sc.kind_correct for sc in detector)
    checks.append(
        GdCheck(
            "D-kind",
            "reported",
            kind_ok / kind_n if kind_n else math.nan,
            math.nan,
            math.nan,
            None,
            kind_n,
        )
    )
    if "oracle" in e:
        med = {
            k: percentile(ascending(e[k]["range_rel"]), 0.5)
            for k in (downstream, "least_squares", "oracle")
        }
        gap = _div(med["least_squares"] - med[downstream], med["least_squares"] - med["oracle"])
        checks.append(
            GdCheck(
                "D-gap",
                "reported",
                gap,
                math.nan,
                math.nan,
                None,
                int(keep.sum()),
                f"medians: least squares {med['least_squares']:.4f}, detector "
                f"{med[downstream]:.4f}, oracle {med['oracle']:.4f}",
            )
        )
    return checks


def variant_result(checks: Sequence[GdCheck]) -> str:
    gated = [c for c in checks if c.name in GATED]
    if any(c.result == "fail" for c in gated):
        return "fail"
    if gated and all(c.result == "pass" for c in gated):
        return "pass"
    return "inconclusive"


def gate_result(variants: dict[str, Sequence[GdCheck]]) -> str:
    res = [variant_result(c) for c in variants.values()]
    if "pass" in res:
        return "pass"
    if res and all(r == "fail" for r in res):
        return "fail"
    return "inconclusive"


def validation_carries(checks: Sequence[GdCheck]) -> bool:
    """Annex A §A.5's validation rule for one variant."""
    for c in checks:
        if c.name not in GATED:
            continue
        if c.result == "fail" or c.limit is None:
            return False
        meets = c.value <= c.limit if c.name == "D-miss" else c.value < c.limit
        if not meets:
            return False
    return True
