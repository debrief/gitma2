"""Stated 95% intervals from the regressor's variance head (spec 037 research R1).

The head gives a Gaussian for ln range and for the two velocity components (frame units of
10 m/s, independent). Range: the half-width of ln(estimated ÷ true range) is 1.96 sd. Speed and
course have no closed form, so the velocity Gaussian is represented by one fixed seeded sample
and the half-widths are its 95% quantiles of |speed − estimated speed| and of the angle from the
estimated course. A course half-width over a quarter turn (the arc is then more than a half
circle) is no statement and is returned as NaN: "undetermined".
"""

from __future__ import annotations

import math

import numpy as np

Z95 = 1.959963984540054
LEVEL = 0.95
POINTS = 4096
MAX_ARC = 0.5 * math.pi

# A fixed standard normal sample (seeded, antithetic): the same points for every row.
_g = np.random.default_rng(37).standard_normal((POINTS // 2, 2))
_g = np.concatenate([_g, -_g])
_GX, _GY = _g[:, 0].copy(), _g[:, 1].copy()
_GW = np.full(POINTS, 1.0 / POINTS)


def _wquantile(v: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return float(v[o][min(int(np.searchsorted(c, q * c[-1])), v.size - 1)])


def velocity_halfwidths(
    vx: float, vy: float, sx: float, sy: float, scale_speed: float = 1.0, scale_course: float = 1.0
) -> tuple[float, float]:
    """(speed half-width, course half-width in radians or NaN) for a velocity N((vx, vy),
    diag(sx², sy²)), any one unit. The scales multiply the sds for the quantity they name."""
    out: list[float] = []
    for s in (scale_speed, scale_course):
        px, py = vx + s * sx * _GX, vy + s * sy * _GY
        if len(out) == 0:
            out.append(_wquantile(np.abs(np.hypot(px, py) - math.hypot(vx, vy)), _GW, LEVEL))
        else:
            d = np.arctan2(px, py) - math.atan2(vx, vy)
            d = np.abs((d + math.pi) % (2.0 * math.pi) - math.pi)
            a = _wquantile(d, _GW, LEVEL)
            out.append(a if a <= MAX_ARC else math.nan)
    return out[0], out[1]


def row_intervals(
    pred: np.ndarray, logvar: np.ndarray, v_unit: float, scale: tuple[float, float, float]
) -> dict[str, float]:
    """The interval fields of one prediction row (schema names of spec 009). ``pred``,
    ``logvar`` [3]: ln range, v′x, v′y in the model's units; ``scale``: range, course, speed."""
    sd = np.exp(0.5 * np.asarray(logvar, dtype=np.float64))
    sp, arc = velocity_halfwidths(
        float(pred[1]), float(pred[2]), float(sd[1]), float(sd[2]), scale[2], scale[1]
    )
    out = {
        "range_ratio_q95": Z95 * scale[0] * float(sd[0]),
        "speed_q95_mps": v_unit * sp,
    }
    if math.isfinite(arc):
        out["course_arc_rad"] = arc
        out["course_arc_prob"] = LEVEL
    return out
