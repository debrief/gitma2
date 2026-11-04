"""``ownship_legs`` on generator 0.6.0 wander tracks (spec 006, T024).

Wander moves the recorded course on every steady row, so the default tolerance (1e-6) marks every
such row as turning. With a per-row tolerance between the largest wander step and the smallest
planned turn step (4.5°: helm wander and oscillation change the course by under 4° a row; planned
turns of 0.5–3°/s by 5–30° a row), it finds every planned turn from its first row and flags no
row outside one. The last row of a turn can be a partial step under the tolerance and is then
read as steady, so legs can start one row early. Spec 005's component O replaces this for wander
data; it remains exact on 0.5.0 tracks (no wander)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from tma2.detect.steady_leg import ownship_legs
from tma2.sim.generate import generate_scenario

ROOT = Path(__file__).resolve().parents[2]
TOL = math.radians(4.5)


def _turns(m: object) -> list[tuple[int, int]]:
    out = [(int(m.turn_start_index), int(m.zig_index))]  # type: ignore[attr-defined]
    if getattr(m, "turn2_start_index", None) is not None:
        out.append((int(m.turn2_start_index), int(m.zig2_index)))  # type: ignore[attr-defined]
    return out


def test_ownship_legs_on_wander_tracks() -> None:
    ranges = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())
    wandered = 0
    for i in range(60):
        s = generate_scenario(316, i, ranges).scenario
        m = s.metadata
        course = np.array([st.course_rad for st in s.ownship.states], dtype=np.float64)
        speed = np.array([st.speed_mps for st in s.ownship.states], dtype=np.float64)
        w = m.ownship_wander
        kind = str(getattr(w.kind, "value", w.kind)) if w is not None else None
        wandered += kind in ("wander", "oscillation")
        turning = ownship_legs(course, speed, TOL) < 0
        planned = np.zeros(course.shape[0], dtype=np.bool_)
        for a, b in _turns(m):
            planned[a : b + 1] = True
            assert turning[a], f"scenario {i}: turn at row {a} not found from its first row"
        assert not (turning & ~planned).any(), f"scenario {i}: a steady row flagged as turning"
        if kind in ("wander", "oscillation"):
            # the default tolerance cannot tell wander from turning
            assert (ownship_legs(course, speed) < 0).sum() > planned.sum()
    assert wandered >= 20
