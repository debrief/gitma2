from __future__ import annotations

import math

import numpy as np

from tma2.sim import geometry as g


def test_f32_rounds_and_normalises_negative_zero() -> None:
    assert g.f32(0.1) == float(np.float32(0.1))
    assert math.copysign(1.0, g.f32(-0.0)) == 1.0
    assert g.f32(-1e-50) == 0.0 and math.copysign(1.0, g.f32(-1e-50)) == 1.0


def test_wrap_and_angle() -> None:
    assert g.wrap2pi(-0.5) == -0.5 + g.TWO_PI
    assert g.wrap2pi(g.TWO_PI) == 0.0
    assert g.f32_angle(g.TWO_PI - 1e-9) == 0.0  # rounds up to 2π, then wraps to 0
    assert 0.0 <= g.f32_angle(123.456) < g.TWO_PI
    assert g.wrap_pi(math.pi + 0.1) == pytest_approx(-math.pi + 0.1)


def pytest_approx(x: float) -> object:
    import pytest

    return pytest.approx(x, abs=1e-12)


def test_js_round_is_half_up() -> None:
    assert g.js_round(2.5) == 3
    assert g.js_round(-2.5) == -2
    assert g.js_round(-2.6) == -3
    assert g.js_round(2.4999) == 2


def test_turn_rows() -> None:
    assert g.turn_rows(0.0, 10.0) == 1
    assert g.turn_rows(10.0, 10.0) == 1
    assert g.turn_rows(10.5, 10.0) == 2
    assert g.turn_rows(95.0, 10.0) == 10


def test_bearing_of() -> None:
    assert g.bearing_of(0.0, 1.0) == 0.0
    assert g.bearing_of(1.0, 0.0) == pytest_approx(math.pi / 2)
    assert g.bearing_of(-1.0, 0.0) == pytest_approx(3 * math.pi / 2)


def test_arc_position_closes_a_full_circle() -> None:
    x, y, c = g.arc_position(1.0, 2.0, 0.3, 5.0, 0.01, g.TWO_PI / 0.01)
    assert (x, y) == (pytest_approx(1.0), pytest_approx(2.0))
    assert c == pytest_approx(0.3)
