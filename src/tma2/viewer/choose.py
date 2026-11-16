"""The rule that picks the viewer's demo engagements (spec 020 research R2).

Over the σ = 1° scenarios of a split in ordinal order (at most ``limit``), skipping any whose
four G5 rows do not all fall inside the window: classes by the number of target manoeuvres that
overlap the span the viewer shows, from the first G5 row (zig + 5 min) to the end of the window
(quiet 0, one 1, busy 2 or more). Counting over the whole window left no quiet target in the
first 200 ordinals of seed 319: MAN2 targets manoeuvre every 10 to 40 minutes. Picks, in this
order: the first quiet, the first one, the first busy, the first engagement not yet picked in
which E's median range error over its G5 rows is worse than C″'s, then the next one and the
next busy. A class
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
    manoeuvres: int  # overlapping the shown span


def shown_manoeuvres(meta: dict[str, Any], start: int) -> int:
    """Target manoeuvres overlapping rows ``start`` onward."""
    return sum(1 for m in meta.get("manoeuvres") or [] if int(m["end_index"]) >= start)


def manoeuvre_class(meta: dict[str, Any], start: int) -> str:
    n = shown_manoeuvres(meta, start)
    return {0: QUIET, 1: ONE}.get(n, BUSY)


def choose(
    candidates: Iterable[tuple[int, dict[str, Any], int]],
    e_loses: Callable[[int], bool],
    usable: Callable[[int], bool] = lambda _j: True,
) -> tuple[list[Pick], list[str]]:
    """``candidates``: (ordinal, meta, first shown row) of the eligible engagements in ordinal
    order.
    ``e_loses(ordinal)`` is asked only for engagements the LOSES slot still needs, in order;
    ``usable(ordinal)`` (E has an input at some shown row) is asked of each match before it is
    taken.
    Returns the picks in ``ORDER``'s order and the slots left empty."""
    pool = list(candidates)
    taken: set[int] = set()
    picks: list[Pick] = []
    missing: list[str] = []
    for slot in ORDER:
        found = None
        for j, meta, start in pool:
            if j in taken:
                continue
            ok = e_loses(j) if slot == LOSES else manoeuvre_class(meta, start) == slot
            ok = ok and usable(j)
            if ok:
                found = Pick(j, slot, shown_manoeuvres(meta, start))
                break
        if found is None:
            missing.append(slot)
            continue
        taken.add(found.ordinal)
        picks.append(found)
    return picks, missing
