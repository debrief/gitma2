"""Annex B's manoeuvre statistics as a prior over a period's manoeuvre history, and the
evidence of a history given the bearings (spec 013, owner decision 2026-11-11: a classical
estimator that uses what is known beforehand about how targets manoeuvre).

The prior follows generator 0.6.0 (``sim/scenario.py``, ``plan_target_legs``): steady legs
N(mean, sd) from a manoeuvre's end to the next start; a change is a turn, a speed change or
both, by weight; turn angle, turn rate, speed change and acceleration uniform. A period is cut
at random, so the time to its first manoeuvre follows the leg's forward recurrence and the time
after its last the leg's survival. Uniform ranges get Gaussian shoulders (a tenth of the width)
so an estimate just outside a range is unlikely, not impossible.

``log_evidence`` is Laplace's approximation: the fit's cost, the prior at the fit, and the
volume of parameter space the bearings and the prior leave (the Occam factor).

``version`` 1 is the prior Gate T registered, kept exactly. Version 2 (spec 014, research R2)
corrects three errors its panel recorded, each of which penalised an extra manoeuvre: an
interior leg's curvature was counted twice (as a residual and again in ``prior_precision``);
a uniform direction's stand-in precision 12 / W² gave it a volume of 0.72 W, not W; and the
leg's normal density allowed legs below the generator's minimum. ``kind`` "flat" (spec 014,
research R3) replaces what Annex B says about manoeuvres by uniform densities over the
solver's own box, keeping the state's prior: the search with no manoeuvre statistics.
``kind`` "mix" (spec 014, registered after the tuning seed showed the informed search declaring
a manoeuvre on four held-course periods in five) is Annex B's prior for a target that
manoeuvres, mixed with a target that never does: with probability ``QUIET`` there are no
manoeuvres at all. Only the weight of the no-manoeuvre history changes; ``QUIET`` is a stated
half, not a tuned value.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

LOG_2PI = math.log(2.0 * math.pi)
QUIET = 0.5  # kind "mix": the prior probability that the target never manoeuvres


@dataclass(frozen=True)
class ManoeuvrePrior:
    leg_mean: float
    leg_sd: float
    leg_min: float
    w_course: float
    w_speed: float
    w_both: float
    angle: tuple[float, float]
    turn_rate: tuple[float, float]
    dv: tuple[float, float]
    acc: tuple[float, float]
    speed: tuple[float, float]
    range0: tuple[float, float]
    version: int = 1
    kind: str = "annex-b"

    @classmethod
    def from_ranges(
        cls, r: dict[str, Any], version: int = 1, kind: str = "annex-b"
    ) -> ManoeuvrePrior:
        if version not in (1, 2) or kind not in ("annex-b", "flat", "mix"):
            raise ValueError(f"unknown prior version {version!r} or kind {kind!r}")

        def pair(k: str) -> tuple[float, float]:
            return float(r[k]["min"]), float(r[k]["max"])

        leg, w = r["target_leg_length_s"], r["target_change_kind_weights"]
        return cls(
            float(leg["mean"]),
            float(leg["sd"]),
            float(leg["min"]),
            float(w["course"]),
            float(w["speed"]),
            float(w["both"]),
            pair("target_manoeuvre_angle_abs_rad"),
            pair("target_turn_rate_rad_s"),
            pair("target_speed_change_abs_mps"),
            pair("target_speed_change_rate_mps2"),
            pair("target_speed_mps"),
            pair("target_range0_m"),
            version,
            kind,
        )


def _phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def log_soft_uniform(x: float, lo: float, hi: float) -> float:
    """Log density of a uniform on [lo, hi] with Gaussian shoulders of sd (hi − lo) / 10."""
    s = (hi - lo) / 10.0
    norm = (hi - lo) + s * math.sqrt(2.0 * math.pi)
    d = max(lo - x, x - hi, 0.0)
    return -0.5 * (d / s) ** 2 - math.log(norm)


def _leg_shoulder(p: ManoeuvrePrior) -> float:
    return p.leg_min / 10.0


def _leg_pdf(p: ManoeuvrePrior, g: float) -> float:
    """Log density of a steady leg of length g. Version 1: the normal, unbounded below.
    Version 2: the normal above the minimum with a Gaussian shoulder below it (sd a tenth of
    the minimum), renormalised to integrate to 1."""
    if p.version == 1:
        z = (max(g, 0.0) - p.leg_mean) / p.leg_sd
        return -0.5 * z * z - math.log(p.leg_sd) - 0.5 * LOG_2PI
    zmin = (p.leg_min - p.leg_mean) / p.leg_sd
    at_min = math.exp(-0.5 * zmin * zmin) / (p.leg_sd * math.sqrt(2.0 * math.pi))
    s = _leg_shoulder(p)
    norm = (1.0 - _phi(zmin)) + at_min * s * math.sqrt(math.pi / 2.0)
    if g >= p.leg_min:
        z = (g - p.leg_mean) / p.leg_sd
        return -0.5 * z * z - math.log(p.leg_sd) - 0.5 * LOG_2PI - math.log(norm)
    return math.log(at_min) - 0.5 * ((p.leg_min - g) / s) ** 2 - math.log(norm)


def _flat_box() -> tuple[float, float, float, float]:
    """The solver's own bounds: turn, speed change, shortest and longest duration."""
    from .arc import MAX_SPEED_CHANGE, MAX_TURN
    from .retest import MAX_DURATION, MIN_DURATION

    return MAX_TURN, MAX_SPEED_CHANGE, MIN_DURATION, MAX_DURATION


def _leg_sf(p: ManoeuvrePrior, g: float) -> float:
    """P(leg > g)."""
    return 1.0 if g < p.leg_min else 1.0 - _phi((g - p.leg_mean) / p.leg_sd)


def _leg_tail(p: ManoeuvrePrior, g: float) -> float:
    """∫_g^∞ P(leg > u) du (numerically)."""
    u = np.linspace(g, max(g, p.leg_mean + 8 * p.leg_sd), 400)
    sf = np.array([_leg_sf(p, float(x)) for x in u])
    return float(np.sum(0.5 * (sf[1:] + sf[:-1]) * np.diff(u)))


def log_prior(
    p: ManoeuvrePrior,
    theta: np.ndarray,
    spans: np.ndarray,
    kinds: np.ndarray,
    t_end: float,
    range0: float,
) -> dict[str, float]:
    """The log prior density of a history, by part: ``legs`` (when), ``changes`` (what) and
    ``state`` (where the target starts). ``kinds`` [M, 2] says which changes each manoeuvre has."""
    m = spans.shape[0]
    if p.kind == "flat":
        return _log_prior_flat(p, theta, spans, kinds, t_end, range0)
    mean_leg = _leg_tail(p, 0.0)
    legs = 0.0
    if m == 0:
        legs = math.log(max(_leg_tail(p, t_end) / mean_leg, 1e-300))
    else:
        legs += math.log(max(_leg_sf(p, float(spans[0, 0])) / mean_leg, 1e-300))
        for i in range(m - 1):
            legs += _leg_pdf(p, float(spans[i + 1, 0] - spans[i, 1]))
        legs += math.log(max(_leg_sf(p, t_end - float(spans[-1, 1])), 1e-300))
    changes = 0.0
    speed = float(theta[3])
    state = log_soft_uniform(speed, *p.speed)
    for i in range(m):
        dc, dv = float(theta[4 + 2 * i]), float(theta[5 + 2 * i])
        dur = float(spans[i, 1] - spans[i, 0])
        has_c, has_v = bool(kinds[i, 0]), bool(kinds[i, 1])
        w = p.w_both if has_c and has_v else (p.w_course if has_c else p.w_speed)
        changes += math.log(w)
        if has_c:  # sign ½, |angle| uniform, rate uniform: duration = |angle| / rate
            a = max(abs(dc), 1e-6)
            changes += math.log(0.5) + log_soft_uniform(a, *p.angle)
            changes += log_soft_uniform(a / dur, *p.turn_rate) + math.log(a / (dur * dur))
        if has_v:
            a = max(abs(dv), 1e-6)
            changes += math.log(0.5) + log_soft_uniform(a, *p.dv)
            if not has_c:  # a "both" manoeuvre's duration is counted once, with its turn
                changes += log_soft_uniform(a / dur, *p.acc) + math.log(a / (dur * dur))
            speed += dv
            state += log_soft_uniform(speed, *p.speed) - log_soft_uniform(
                0.5 * (p.speed[0] + p.speed[1]), *p.speed
            )
    state += _log_position(p, range0)
    if p.kind == "mix":
        legs = (
            math.log(QUIET + (1.0 - QUIET) * math.exp(legs))
            if m == 0
            else (legs + math.log(1.0 - QUIET))
        )
    return {"legs": legs, "changes": changes, "state": state}


def _log_position(p: ManoeuvrePrior, range0: float) -> float:
    """Position: range log-uniform (widened: the period starts later than the engagement),
    bearing uniform; course uniform."""
    lo, hi = p.range0[0] / 4.0, p.range0[1] * 4.0
    r = min(max(range0, 1.0), 1e9)
    out = -math.log(r) - math.log(math.log(hi / lo)) - LOG_2PI - math.log(r) - LOG_2PI
    if not lo <= r <= hi:
        out += -0.5 * (math.log(r / min(max(r, lo), hi)) / 0.3) ** 2
    return out


def _log_prior_flat(
    p: ManoeuvrePrior,
    theta: np.ndarray,
    spans: np.ndarray,
    kinds: np.ndarray,
    t_end: float,
    range0: float,
) -> dict[str, float]:
    """No manoeuvre statistics: ordered starts uniform over the period, durations, turns and
    speed changes uniform over the solver's box, the three kinds equally likely. The state's
    prior (speed on every leg, position, course) is the informed prior's."""
    m = spans.shape[0]
    turn, dvmax, dmin, dmax = _flat_box()
    legs = math.lgamma(m + 1) - m * math.log(max(t_end, 1.0))
    changes = 0.0
    speed = float(theta[3])
    state = log_soft_uniform(speed, *p.speed)
    for i in range(m):
        has_c, has_v = bool(kinds[i, 0]), bool(kinds[i, 1])
        changes += -math.log(3.0) - math.log(dmax - dmin)
        if has_c:
            changes += -math.log(2.0 * turn)
        if has_v:
            changes += -math.log(2.0 * dvmax)
            speed += float(theta[5 + 2 * i])
            state += log_soft_uniform(speed, *p.speed) - log_soft_uniform(
                0.5 * (p.speed[0] + p.speed[1]), *p.speed
            )
    state += _log_position(p, range0)
    return {"legs": legs, "changes": changes, "state": state}


def prior_precision(p: ManoeuvrePrior, m: int, range0: float, t_end: float = 0.0) -> np.ndarray:
    """A diagonal precision for (x, y, course, speed, [Δcourse, Δspeed]·M, start·M, duration·M)
    that stands for the prior's curvature where the bearings leave a direction open.

    Version 2: a uniform direction of width W gets 2π / W², so that the Gaussian volume
    √(2π / precision) is W; only the first start keeps a stand-in for its (non-Gaussian) leg,
    because the interior legs' curvature is already in ``prior_residuals``."""
    r = max(range0, p.range0[0])
    two_pi = 2.0 * math.pi
    if p.version == 1 and p.kind != "flat":
        d = [1 / r**2, 1 / r**2, 1 / math.pi**2, 12 / (p.speed[1] - p.speed[0]) ** 2]
        for _ in range(m):
            d += [12 / (2 * p.angle[1]) ** 2, 12 / (2 * p.dv[1]) ** 2]
        d += [1 / p.leg_sd**2] * m
        d += [1 / (p.angle[1] / p.turn_rate[0] / 2) ** 2] * m
        return np.array(d)
    d = [1 / r**2, 1 / r**2, 1 / two_pi, two_pi / (p.speed[1] - p.speed[0]) ** 2]
    if p.kind == "flat":
        turn, dvmax, dmin, dmax = _flat_box()
        for _ in range(m):
            d += [two_pi / (2 * turn) ** 2, two_pi / (2 * dvmax) ** 2]
        d += [two_pi / max(t_end, 1.0) ** 2] * m
        d += [two_pi / (dmax - dmin) ** 2] * m
        return np.array(d)
    for _ in range(m):
        d += [
            two_pi / (2 * (p.angle[1] - p.angle[0])) ** 2,
            two_pi / (2 * (p.dv[1] - p.dv[0])) ** 2,
        ]
    d += ([1 / p.leg_sd**2] + [0.0] * (m - 1)) if m else []
    d += [1 / (p.angle[1] / p.turn_rate[0] / 2) ** 2] * m
    return np.array(d)


def _shoulder(x: float, lo: float, hi: float) -> float:
    """The soft uniform's shoulder as a residual: distance outside [lo, hi] over its sd."""
    return max(lo - x, x - hi, 0.0) / ((hi - lo) / 10.0)


def prior_residuals(
    p: ManoeuvrePrior, theta: np.ndarray, spans: np.ndarray, kinds: np.ndarray
) -> np.ndarray:
    """The Gaussian parts of ``log_prior`` as residuals (−½ Σ r² is their log density), so a
    least-squares fit that appends them is a fit to the posterior, not to the likelihood: the
    speed on every leg, each change's size and rate, and the interior legs' lengths. A fixed
    number of residuals for a given history (zeros where a term does not apply)."""
    m = spans.shape[0]
    flat = p.kind == "flat"
    out = [_shoulder(float(theta[3]), *p.speed)]
    speed = float(theta[3])
    for i in range(m):
        dc, dv = float(theta[4 + 2 * i]), float(theta[5 + 2 * i])
        dur = max(float(spans[i, 1] - spans[i, 0]), 1e-3)
        has_c, has_v = bool(kinds[i, 0]), bool(kinds[i, 1])
        a = abs(dc)
        out.append(_shoulder(a, *p.angle) if has_c and not flat else 0.0)
        out.append(_shoulder(a / dur, *p.turn_rate) if has_c and not flat else 0.0)
        b = abs(dv)
        out.append(_shoulder(b, *p.dv) if has_v and not flat else 0.0)
        out.append(_shoulder(b / dur, *p.acc) if has_v and not has_c and not flat else 0.0)
        speed += dv if has_v else 0.0
        out.append(_shoulder(speed, *p.speed))
    zmin = (p.leg_min - p.leg_mean) / p.leg_sd
    for i in range(m - 1):
        g = float(spans[i + 1, 0] - spans[i, 1])
        if flat:
            out.append(0.0)
        elif p.version == 1:
            out.append((max(g, 0.0) - p.leg_mean) / p.leg_sd)
        elif g >= p.leg_min:
            out.append((g - p.leg_mean) / p.leg_sd)
        else:  # −½ r² continues the density below the minimum
            out.append(-math.sqrt(zmin * zmin + ((p.leg_min - g) / _leg_shoulder(p)) ** 2))
    return np.array(out, dtype=np.float64)
