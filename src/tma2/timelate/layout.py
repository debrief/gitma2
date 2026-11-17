"""Several periods of one target, separated by gaps (spec 023, research R3).

An engagement is laid out as two or three periods with gaps between them, from a stream of
its own seeded from the engagement's seed, so the generator's draws are untouched and
existing data cannot change. Inside a gap no system uses a bearing: the joint solve sees the
whole span with the gaps' bearings marked missing (``span``, ``masked=True``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tma2.sim.prng import create_rng, mix64, uniform_int

from .periods import Period

LAYOUT_STREAM = np.uint64(0x2C6F_0B93_D1A4_7E55)  # distinguishes the layout's stream
PERIOD_S = (900.0, 1800.0)  # each period's length, uniform
GAP_S = (300.0, 1800.0)  # each gap's length, uniform
COUNTS = (2, 3)  # periods per engagement, equal odds


@dataclass(frozen=True)
class Layout:
    first: int  # the span's first row in the engagement
    periods: tuple[tuple[int, int], ...]  # (first row, rows) of each period, in the engagement

    @property
    def rows(self) -> int:
        a, n = self.periods[-1]
        return a + n - self.first

    def gaps(self) -> list[tuple[int, int]]:
        """(first row, rows) of each gap, in the engagement."""
        out = []
        for (a, n), (b, _m) in zip(self.periods[:-1], self.periods[1:], strict=True):
            out.append((a + n, b - (a + n)))
        return out


def _draw(s: np.ndarray, lo: float, hi: float, dt: float) -> int:
    a, b = int(round(lo / dt)), int(round(hi / dt))
    return a + int(uniform_int(s, b - a + 1))


def layout(
    seed: np.uint64,
    samples: int,
    dt: float,
    period_s: tuple[float, float] = PERIOD_S,
    gap_s: tuple[float, float] = GAP_S,
    counts: tuple[int, ...] = COUNTS,
) -> Layout | None:
    """The engagement's periods and gaps, or ``None`` if not even two periods fit.

    Draw order (fixed): the number of periods; each period's length and each gap's length,
    alternating from the first period; then the span's start. If the drawn span does not fit
    the engagement, the last period and the gap before it are dropped until it does."""
    s = create_rng(np.uint64(mix64(np.uint64(seed) ^ LAYOUT_STREAM)))
    k = int(counts[int(uniform_int(s, len(counts)))])
    lens, gaps = [], []
    for i in range(k):
        lens.append(_draw(s, *period_s, dt))
        if i < k - 1:
            gaps.append(_draw(s, *gap_s, dt))
    while len(lens) >= 2 and sum(lens) + sum(gaps) > samples:
        lens.pop()
        gaps.pop()
    if len(lens) < 2:
        return None
    total = sum(lens) + sum(gaps)
    first = int(uniform_int(s, samples - total + 1))
    periods, at = [], first
    for i, n in enumerate(lens):
        periods.append((at, n))
        at += n + (gaps[i] if i < len(gaps) else 0)
    return Layout(first, tuple(periods))


def period(x: Period, a: int, n: int) -> Period:
    """One period of an engagement (``x``'s arrays, the bearings as given)."""
    return Period(x.ordinal, x.meta, x.own, x.tgt, x.obs, a, n, x.dt)


def span(x: Period, lay: Layout, masked: bool) -> Period:
    """The span from the first period's start to the last period's end; with ``masked`` the
    gaps' bearings are marked missing (the observation array is copied, never changed)."""
    obs = x.obs
    if masked:
        obs = obs.copy()
        for a, n in lay.gaps():
            obs[a : a + n, 2] = 0
    return Period(x.ordinal, x.meta, x.own, x.tgt, obs, lay.first, lay.rows, x.dt)
