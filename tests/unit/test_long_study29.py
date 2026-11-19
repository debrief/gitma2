"""Spec 029: window classes by ownship turns."""

from __future__ import annotations

from types import SimpleNamespace

from tma2.long.study29 import klass, turns_in


def test_turns_overlapping_a_window() -> None:
    e = SimpleNamespace(meta={"ownship_turns": [[100, 130], [700, 720], [1000, 1010]]})
    assert turns_in(e, 0, 100) == 0  # ends just before the first turn
    assert turns_in(e, 0, 101) == 1
    assert turns_in(e, 120, 200) == 1  # a turn in progress at the start counts
    assert turns_in(e, 131, 569) == 0
    assert turns_in(e, 600, 500) == 2
    assert [klass(n) for n in (0, 1, 2, 5)] == ["held", "one", "more", "more"]
