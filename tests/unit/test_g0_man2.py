"""Spec 006 G0-MAN2 helpers: the zig leg (research R3) and the planned ownship segments."""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.cli.g0_man2 import _planned_courses
from tma2.eval.rows import zig_leg


def _meta(
    spans: list[tuple[int, int]], n: int = 300, turn: int = 100, zig: int = 110
) -> dict[str, Any]:
    return {
        "samples": n,
        "turn_start_index": turn,
        "zig_index": zig,
        "manoeuvres": [{"start_index": a, "end_index": b} for a, b in spans],
    }


def test_zig_leg_bounds() -> None:
    assert zig_leg(_meta([])) == (0, 299)
    # a change before the turn starts the leg at its end row; one after the zig ends it
    assert zig_leg(_meta([(40, 50), (200, 210)])) == (50, 198)
    # a span overlapping the ownship turn: no zig leg
    assert zig_leg(_meta([(105, 115)])) is None
    assert zig_leg(_meta([(90, 101)])) is None
    # too few rows before the turn, or after the zig
    assert zig_leg(_meta([(80, 95)])) is None
    assert zig_leg(_meta([(135, 140)])) is None


def test_planned_courses_read_turn_rows() -> None:
    n = 60
    c = np.full(n, 1.0)
    c[20:26] = np.linspace(1.1, 1.5, 6)  # turn rows 20..25, zig row 25 carries the new course
    c[26:] = 1.5 + 0.01 * np.sin(np.arange(n - 26))  # wander on the next leg
    m = {"samples": n, "turn_start_index": 20, "zig_index": 25}
    segs = _planned_courses(m, c)
    assert segs[0] == (0, 18, 1.0)
    assert segs[1][0] == 26 and segs[1][1] == n - 1 and segs[1][2] == c[25]
