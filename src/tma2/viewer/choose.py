"""The rule that picks the viewer's demo engagements (spec 020 research R2).

Over the σ = 1° scenarios of a split in ordinal order (at most ``limit``), skipping any whose
four G5 rows do not all fall inside the window: classes by the number of target manoeuvres in
the window (quiet 0, one 1, busy 3 or more; two is no class). Picks, in this order: the first
quiet, the first one, the first busy, the first engagement not yet picked in which E's median
range error over its G5 rows is worse than C″'s, then the next one and the next busy. A class
that cannot be filled within ``limit`` is reported, never widened.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

QUIET, ONE, BUSY, LOSES = "quiet", "one manoeuvre", "busy", "E worse than C″"
ORDER = (QUIET, ONE, BUSY, LOSES, ONE, BUSY)


@dataclass(frozen=True)
class Pick:
    ordinal: int
    reason: str  # one of ORDER
    manoeuvres: int


def manoeuvre_class(meta: dict[str, Any]) -> str | None:
    n = len(meta.get("manoeuvres") or [])
    return {0: QUIET, 1: ONE}.get(n, BUSY if n >= 3 else None)


def choose(
    candidates: Iterable[tuple[int, dict[str, Any]]],
    e_loses: Callable[[int], bool],
) -> tuple[list[Pick], list[str]]:
    """``candidates``: (ordinal, meta) of the eligible engagements in ordinal order.
    ``e_loses(ordinal)`` is asked only for engagements the LOSES slot still needs, in order.
    Returns the picks in ``ORDER``'s order and the slots left empty."""
    pool = list(candidates)
    taken: set[int] = set()
    picks: list[Pick] = []
    missing: list[str] = []
    for slot in ORDER:
        found = None
        for j, meta in pool:
            if j in taken:
                continue
            ok = e_loses(j) if slot == LOSES else manoeuvre_class(meta) == slot
            if ok:
                found = Pick(j, slot, len(meta.get("manoeuvres") or []))
                break
        if found is None:
            missing.append(slot)
            continue
        taken.add(found.ordinal)
        picks.append(found)
    return picks, missing
