"""Angles, units, float32 rounding and JavaScript-compatible helpers.

Ported from gitma ``packages/sim/src/geometry.ts`` (commit d0aec60), plus the two JavaScript
semantics the port must reproduce: ``Math.round`` (half-up) and ``Math.fround`` + 0 (float32 with
negative zero mapped to positive zero). Frame: x east, y north; bearings clockwise from north.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

TWO_PI = 2.0 * math.pi
KNOT_MPS = 1852.0 / 3600.0
DEG = math.pi / 180.0


@njit(cache=True)
def f32(x: float) -> float:
    """Round to the nearest float32 and map -0 to +0 (gitma ``f32``: ``Math.fround(x) + 0``)."""
    return float(np.float32(x)) + 0.0


@njit(cache=True)
def wrap2pi(a: float) -> float:
    """Wrap an angle to [0, 2π) (JavaScript ``%`` keeps the dividend's sign, as ``math.fmod``)."""
    w = np.fmod(a, TWO_PI)
    r = w + TWO_PI if w < 0 else w
    return 0.0 if r >= TWO_PI else r


@njit(cache=True)
def f32_angle(a: float) -> float:
    """Wrap to [0, 2π) and round to float32, keeping the result strictly below 2π."""
    v = f32(wrap2pi(a))
    return 0.0 if v >= TWO_PI else v


@njit(cache=True)
def wrap_pi(a: float) -> float:
    """Angle in (−π, π] (gitma ``wrapPi``: ``atan2(sin a, cos a)``)."""
    return math.atan2(math.sin(a), math.cos(a))


@njit(cache=True)
def bearing_of(dx: float, dy: float) -> float:
    """True bearing of the vector (dx east, dy north), clockwise from north, in [0, 2π)."""
    return float(wrap2pi(math.atan2(dx, dy)))


@njit(cache=True)
def js_round(x: float) -> int:
    """JavaScript ``Math.round``: round half towards +∞ (Python's ``round`` is half-to-even)."""
    return int(math.floor(x + 0.5))


@njit(cache=True)
def turn_rows(turn_s: float, dt: float) -> int:
    """Samples from a turn's start sample to the first sample after it ends (gitma ``turnRows``)."""
    k = 1
    while k * dt < turn_s:
        k += 1
    return k


@njit(cache=True)
def arc_position(
    x0: float, y0: float, c0: float, v: float, omega: float, tau: float
) -> tuple[float, float, float]:
    """Position and course on a constant-rate arc ``tau`` s after a turn starting at (x0, y0).

    ``omega`` is signed (rad/s, positive clockwise). Closed form as gitma ``arcPosition``:
    x = x0 + (v/ω)(cos c0 − cos c), y = y0 + (v/ω)(sin c − sin c0), c = c0 + ωτ.
    """
    r = v / omega
    c = c0 + omega * tau
    return x0 + r * (math.cos(c0) - math.cos(c)), y0 + r * (math.sin(c) - math.sin(c0)), wrap2pi(c)


def kt_to_mps(kt: float) -> float:
    return kt * KNOT_MPS


def mps_to_kt(mps: float) -> float:
    return mps / KNOT_MPS


def deg_to_rad(deg: float) -> float:
    return deg * DEG


def rad_to_deg(rad: float) -> float:
    return rad / DEG
