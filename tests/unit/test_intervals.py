"""Spec 037 research R1: intervals from the regressor's variance head."""

import math

import numpy as np

from tma2.regress.intervals import Z95, row_intervals, velocity_halfwidths


def test_tight_velocity_matches_the_linearised_widths() -> None:
    # speed 5 along +y, small isotropic sd: speed half-width ≈ 1.96 s, course ≈ 1.96 s / 5
    sp, arc = velocity_halfwidths(0.0, 5.0, 0.05, 0.05)
    assert abs(sp - Z95 * 0.05) < 0.01
    assert abs(arc - Z95 * 0.05 / 5.0) < 0.003


def test_coverage_by_simulation() -> None:
    rng = np.random.default_rng(7)
    vx, vy, sx, sy = 2.0, 3.0, 0.8, 1.5
    sp, arc = velocity_halfwidths(vx, vy, sx, sy)
    px, py = vx + sx * rng.standard_normal(200_000), vy + sy * rng.standard_normal(200_000)
    cov_s = np.mean(np.abs(np.hypot(px, py) - math.hypot(vx, vy)) <= sp)
    d = np.arctan2(px, py) - math.atan2(vx, vy)
    cov_c = np.mean(np.abs((d + math.pi) % (2 * math.pi) - math.pi) <= arc)
    assert abs(cov_s - 0.95) < 0.02
    assert abs(cov_c - 0.95) < 0.02


def test_undetermined_course_is_not_stated() -> None:
    _, arc = velocity_halfwidths(0.0, 0.1, 2.0, 2.0)
    assert math.isnan(arc)
    row = row_intervals(
        np.array([0.0, 0.0, 0.01]), np.log(np.array([0.04, 4.0, 4.0])), 10.0, (1, 1, 1)
    )
    assert "course_arc_rad" not in row
    assert abs(row["range_ratio_q95"] - Z95 * 0.2) < 1e-12


def test_scales_widen_their_own_quantity_only() -> None:
    p, lv = np.array([0.0, 0.0, 0.5]), np.log(np.array([0.01, 0.0004, 0.0004]))
    a = row_intervals(p, lv, 10.0, (1.0, 1.0, 1.0))
    b = row_intervals(p, lv, 10.0, (2.0, 1.0, 1.0))
    c = row_intervals(p, lv, 10.0, (1.0, 2.0, 1.0))
    assert b["range_ratio_q95"] == 2 * a["range_ratio_q95"]
    assert b["speed_q95_mps"] == a["speed_q95_mps"] and b["course_arc_rad"] == a["course_arc_rad"]
    assert (
        c["course_arc_rad"] > 1.8 * a["course_arc_rad"] and c["speed_q95_mps"] == a["speed_q95_mps"]
    )
