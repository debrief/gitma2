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


def test_js_round_edge_cases_match_ecmascript() -> None:
    assert g.js_round(0.49999999999999994) == 0
    assert g.js_round(-0.5) == 0
    assert g.js_round(-1.5) == -1
    assert g.js_round(1e15 + 0.5) == 1e15 + 1


# Known-answer frame tests (P0 panel round 1): a frame error shared by gitma and gitma2 would
# pass every conformance check, so the conventions are pinned here against hand-computed answers.


def test_bearing_convention_true_clockwise_from_north() -> None:
    assert g.bearing_of(0.0, 1.0) == 0.0  # due north
    assert math.isclose(g.bearing_of(1.0, 0.0), math.pi / 2)  # due east
    assert math.isclose(g.bearing_of(0.0, -1.0), math.pi)  # due south
    assert math.isclose(g.bearing_of(-1.0, 0.0), 3 * math.pi / 2)  # due west


def test_positive_turn_rate_turns_clockwise() -> None:
    # Heading north at 10 m/s, turning at +0.1 rad/s: a quarter turn later the course is east
    # (90°) and the target is north-east of the start, at (r, r) with r = v/ω = 100 m.
    x, y, c = g.arc_position(0.0, 0.0, 0.0, 10.0, 0.1, (math.pi / 2) / 0.1)
    assert math.isclose(c, math.pi / 2)
    assert math.isclose(x, 100.0) and math.isclose(y, 100.0)
    # Negative rate turns anticlockwise: course west, target north-west.
    x, y, c = g.arc_position(0.0, 0.0, 0.0, 10.0, -0.1, (math.pi / 2) / 0.1)
    assert math.isclose(c, 3 * math.pi / 2)
    assert math.isclose(x, -100.0) and math.isclose(y, 100.0)


def test_course_90_moves_east_in_generated_truth() -> None:
    from tests.conftest import fixture_dir
    from tma2.data.f32pack import iter_pack_raw

    for _, meta, own, tgt, obs in iter_pack_raw(fixture_dir("iter4-seed777") / "test.f32pack"):
        # Straight-leg rows: displacement agrees with course (sin, cos) and speed.
        for i in range(3):
            dt = float(tgt[i + 1, 0] - tgt[i, 0])
            dx = float(tgt[i + 1, 1] - tgt[i, 1])
            dy = float(tgt[i + 1, 2] - tgt[i, 2])
            c, v = float(tgt[i, 3]), float(tgt[i, 4])
            assert math.isclose(dx, v * math.sin(c) * dt, abs_tol=0.05)
            assert math.isclose(dy, v * math.cos(c) * dt, abs_tol=0.05)
        # The first bearing points from ownship to the target, clockwise from north.
        true_b = g.bearing_of(float(tgt[0, 1] - own[0, 1]), float(tgt[0, 2] - own[0, 2]))
        sigma = float(meta["parameters"]["noise_sigma_rad"])
        if obs[0, 2] != 0:
            assert abs(g.wrap_pi(float(obs[0, 1]) - true_b)) < 5 * sigma
