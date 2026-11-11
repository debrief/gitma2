"""Periods cut at random from engagements (spec 013 research R1).

The cut draws from its own stream, seeded from the scenario's seed, so the generator's draws
are untouched and existing data cannot change. A period keeps the engagement's arrays (for the
truth and the bound) and its own first row and length.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.segment.score import iter_selected
from tma2.sim.prng import create_rng, mix64, parse_seed, uniform_int

CUT_STREAM = np.uint64(0x7D3A_91C4_55E0_13B7)  # distinguishes the cut's stream
MIN_SECONDS = 1200.0


@dataclass
class Period:
    ordinal: int
    meta: dict[str, Any]
    own: np.ndarray  # the engagement's arrays [S, 5], [S, 5], [S, 3]
    tgt: np.ndarray
    obs: np.ndarray
    first: int  # first row of the period in the engagement
    rows: int
    dt: float

    @property
    def last(self) -> int:
        return self.first + self.rows - 1

    def spans(self) -> list[dict[str, Any]]:
        """Target manoeuvres overlapping the period, in the period's rows (clipped)."""
        out = []
        for s in self.meta.get("manoeuvres") or []:
            a, b = int(s["start_index"]), int(s["end_index"])
            if b < self.first or a > self.last:
                continue
            out.append(
                {
                    "kind": s["kind"],
                    "start_index": max(a, self.first) - self.first,
                    "end_index": min(b, self.last) - self.first,
                    "began_before": a < self.first,
                }
            )
        return out

    def ownship_turns(self) -> list[tuple[int, int]]:
        """Ownship turns overlapping the period, in the period's rows (clipped)."""
        m = self.meta
        raw = [
            (m.get("turn_start_index"), m.get("zig_index")),
            (m.get("turn2_start_index"), m.get("zig2_index")),
        ]
        out = []
        for a, b in raw:
            if a is None or b is None or int(a) < 0 or int(b) < 0:
                continue
            a, b = int(a), int(b)
            if b < self.first or a > self.last:
                continue
            out.append((max(a, self.first) - self.first, min(b, self.last) - self.first))
        return out


def cut(
    seed: np.uint64, samples: int, dt: float, min_seconds: float = MIN_SECONDS
) -> tuple[int, int]:
    """(first row, rows): the length uniform between ``min_seconds`` and the engagement, then the
    start uniform over what fits. An engagement shorter than the minimum is taken whole."""
    lo = int(round(min_seconds / dt))
    if samples <= lo:
        return 0, samples
    s = create_rng(np.uint64(mix64(np.uint64(seed) ^ CUT_STREAM)))
    rows = lo + uniform_int(s, samples - lo + 1)
    first = uniform_int(s, samples - rows + 1)
    return int(first), int(rows)


def iter_periods(
    path: str, start: int, count: int, whole: bool = False, min_seconds: float = MIN_SECONDS
) -> Iterator[Period]:
    """One period per σ = 1° engagement, ordinals start … start + count − 1. ``whole`` returns
    the engagements uncut (the stratum scored beside the cut periods)."""
    for j, m, own, tgt, obs in iter_selected(path, start, count):
        n = int(own.shape[0])
        dt = float(m["parameters"]["dt_s"])
        first, rows = (0, n) if whole else cut(parse_seed(str(m["seed"])), n, dt, min_seconds)
        yield Period(j, m, own, tgt, obs, first, rows, dt)
