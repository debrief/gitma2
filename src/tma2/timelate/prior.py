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
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

LOG_2PI = math.log(2.0 * math.pi)


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

    @classmethod
    def from_ranges(cls, r: dict[str, Any]) -> ManoeuvrePrior:
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
        )


def _phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def log_soft_uniform(x: float, lo: float, hi: float) -> float:
    """Log density of a uniform on [lo, hi] with Gaussian shoulders of sd (hi − lo) / 10."""
    s = (hi - lo) / 10.0
    norm = (hi - lo) + s * math.sqrt(2.0 * math.pi)
    d = max(lo - x, x - hi, 0.0)
    return -0.5 * (d / s) ** 2 - math.log(norm)


def _leg_pdf(p: ManoeuvrePrior, g: float) -> float:
    """Log density of a steady leg of length g (the clip at the minimum spread as a shoulder)."""
    z = (max(g, 0.0) - p.leg_mean) / p.leg_sd
    return -0.5 * z * z - math.log(p.leg_sd) - 0.5 * LOG_2PI


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
    # position: range log-uniform (widened: the period starts later than the engagement),
    # bearing uniform; course uniform
    lo, hi = p.range0[0] / 4.0, p.range0[1] * 4.0
    r = min(max(range0, 1.0), 1e9)
    state += -math.log(r) - math.log(math.log(hi / lo)) - LOG_2PI - math.log(r) - LOG_2PI
    if not lo <= r <= hi:
        state += -0.5 * (math.log(r / min(max(r, lo), hi)) / 0.3) ** 2
    return {"legs": legs, "changes": changes, "state": state}


def prior_precision(p: ManoeuvrePrior, m: int, range0: float) -> np.ndarray:
    """A diagonal precision for (x, y, course, speed, [Δcourse, Δspeed]·M, start·M, duration·M)
    that stands for the prior's curvature where the bearings leave a direction open."""
    r = max(range0, p.range0[0])
    d = [1 / r**2, 1 / r**2, 1 / math.pi**2, 12 / (p.speed[1] - p.speed[0]) ** 2]
    for _ in range(m):
        d += [12 / (2 * p.angle[1]) ** 2, 12 / (2 * p.dv[1]) ** 2]
    d += [1 / p.leg_sd**2] * m
    d += [1 / (p.angle[1] / p.turn_rate[0] / 2) ** 2] * m
    return np.array(d)
