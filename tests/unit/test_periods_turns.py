"""Spec 033: ``Period.ownship_turns`` reads the long simulator's full list of turns, and the
generator's two index keys exactly as before."""

from __future__ import annotations

from typing import Any

import numpy as np

from tma2.timelate.periods import Period


def _period(meta: dict[str, Any], first: int, rows: int) -> Period:
    z = np.zeros((400, 5))
    return Period(0, meta, z, z, np.zeros((400, 3)), first, rows, 5.0)


def test_long_simulator_list_gives_every_turn_clipped() -> None:
    meta: dict[str, Any] = {"ownship_turns": [[10, 20], [100, 112], [200, 215], [390, 399]]}
    p = _period(meta, 105, 150)  # rows 105 .. 254
    assert p.ownship_turns() == [(0, 7), (95, 110)]


def test_generator_keys_unchanged() -> None:
    meta: dict[str, Any] = {
        "turn_start_index": 50,
        "zig_index": 60,
        "turn2_start_index": -1,
        "zig2_index": -1,
    }
    assert _period(meta, 0, 400).ownship_turns() == [(50, 60)]
    meta2 = {**meta, "turn2_start_index": 300, "zig2_index": 310}
    assert _period(meta2, 40, 300).ownship_turns() == [(10, 20), (260, 270)]
