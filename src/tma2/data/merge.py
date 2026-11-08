"""Checks for merging sharded CI outputs (spec 008 FR-061, Gate 2 panel G11).

Standard library only: the workflows' merge jobs import it with ``PYTHONPATH=src`` and no
environment."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def ordinal_errors(name: str, ordinals: Iterable[int], a: int, b: int) -> list[str]:
    """Every ordinal in [a, b) exactly once, and none outside it."""
    seen = Counter(ordinals)
    errs = []
    dup = sorted(j for j, c in seen.items() if c > 1)
    if dup:
        errs.append(f"{name}: {len(dup)} duplicate ordinals, e.g. {dup[:5]}")
    miss = sorted(set(range(a, b)) - set(seen))
    if miss:
        errs.append(f"{name}: {len(miss)} ordinals missing, e.g. {miss[:5]}")
    out = sorted(j for j in seen if not a <= j < b)
    if out:
        errs.append(f"{name}: {len(out)} ordinals outside [{a}, {b}), e.g. {out[:5]}")
    return errs
