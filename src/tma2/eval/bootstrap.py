"""Seeded percentile bootstrap intervals (gitma ``packages/eval/src/bootstrap.ts``).

Uses gitma's PRNG (xoshiro128** from seed 20261011) and nearest-rank quantiles, so intervals equal
gitma's on the same inputs. Paired variants share one draw between the two estimators; clustered
variants resample clusters (scenarios) with all their rows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from tma2.sim.prng import create_rng, uniform_int

from .stats import ascending, percentile

BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261011


def _nan_to_inf(a: np.ndarray) -> np.ndarray:
    b = np.asarray(a, dtype=np.float64).copy()
    b[np.isnan(b)] = np.inf
    return b


def _quantile_unsorted(buf: np.ndarray, q: float) -> float:
    """Nearest-rank quantile of an unsorted array (gitma selects; sorting gives the same value)."""
    n = buf.shape[0]
    if n == 0:
        return math.nan
    k = max(1, math.ceil(q * n)) - 1
    return float(np.partition(buf, k)[k])


@dataclass
class RatioInterval:
    ratio: float
    lo: float
    hi: float
    n: int
    resamples: int
    seed: str
    level: float = 0.95
    clusters: int | None = None


@dataclass
class MedianInterval:
    median: float
    lo: float
    hi: float
    n: int
    resamples: int
    seed: str
    level: float = 0.95


def bootstrap_median(
    xs: np.ndarray,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    level: float = 0.95,
) -> MedianInterval:
    x = _nan_to_inf(xs)
    n = x.shape[0]
    if n == 0:
        raise ValueError("bootstrap needs a non-empty sample")
    rng = create_rng(np.uint64(seed))
    meds = np.empty(resamples)
    idx = np.empty(n, dtype=np.int64)
    for b in range(resamples):
        for i in range(n):
            idx[i] = uniform_int(rng, n)
        meds[b] = _quantile_unsorted(x[idx], 0.5)
    s = ascending(meds)
    tail = (1 - level) / 2
    return MedianInterval(
        percentile(ascending(x), 0.5),
        percentile(s, tail),
        percentile(s, 1 - tail),
        n,
        resamples,
        str(seed),
        level,
    )


def bootstrap_median_ratio(
    a: np.ndarray,
    b: np.ndarray,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    level: float = 0.95,
) -> RatioInterval:
    """Seeded paired bootstrap of median(a) / median(b)."""
    return bootstrap_clustered_quantile_ratio(
        a, b, np.arange(a.shape[0], dtype=np.int64), 0.5, level, resamples, seed
    )


def bootstrap_clustered_quantile_ratio(
    a: np.ndarray,
    b: np.ndarray,
    cluster: np.ndarray,
    q: float,
    level: float,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> RatioInterval:
    """Scenario-clustered paired bootstrap of the q-quantile ratio a / b (gitma G5)."""
    x = _nan_to_inf(a)
    y = _nan_to_inf(b)
    n = x.shape[0]
    if n == 0 or y.shape[0] != n or cluster.shape[0] != n:
        raise ValueError("bootstrap needs two equal, non-empty samples and a cluster per row")
    # Members per cluster in first-appearance order (gitma's Map insertion order).
    order: dict[int, list[int]] = {}
    for i in range(n):
        order.setdefault(int(cluster[i]), []).append(i)
    groups = [np.array(m, dtype=np.int64) for m in order.values()]
    g = len(groups)
    rng = create_rng(np.uint64(seed))
    ratios = np.empty(resamples)
    for r in range(resamples):
        picks = [groups[uniform_int(rng, g)] for _ in range(g)]
        idx = np.concatenate(picks)
        ratios[r] = _quantile_unsorted(x[idx], q) / _quantile_unsorted(y[idx], q)
    s = ascending(ratios)
    tail = (1 - level) / 2
    return RatioInterval(
        ratio=percentile(ascending(x), q) / percentile(ascending(y), q),
        lo=percentile(s, tail),
        hi=percentile(s, 1 - tail),
        n=n,
        resamples=resamples,
        seed=str(seed),
        level=level,
        clusters=g,
    )


@dataclass
class DifferenceInterval:
    difference: float
    lo: float
    hi: float
    n: int
    resamples: int
    seed: str
    level: float = 0.95
    clusters: int | None = None


def bootstrap_clustered_rate_difference(
    a: np.ndarray,
    b: np.ndarray,
    cluster: np.ndarray,
    level: float,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> DifferenceInterval:
    """Scenario-clustered paired bootstrap of mean(a) − mean(b) for 0/1 arrays (gitma G5-gross)."""
    n = a.shape[0]
    if n == 0 or b.shape[0] != n or cluster.shape[0] != n:
        raise ValueError("bootstrap needs two equal, non-empty samples and a cluster per row")
    sums: dict[int, list[float]] = {}
    for i in range(n):
        s = sums.setdefault(int(cluster[i]), [0.0, 0.0])
        s[0] += float(a[i]) - float(b[i])
        s[1] += 1
    groups = list(sums.values())
    g = len(groups)
    rng = create_rng(np.uint64(seed))
    diffs = np.empty(resamples)
    for r in range(resamples):
        d = 0.0
        m = 0.0
        for _ in range(g):
            sd, sn = groups[uniform_int(rng, g)]
            d += sd
            m += sn
        diffs[r] = d / m if m > 0 else 0.0
    s_ = ascending(diffs)
    tail = (1 - level) / 2
    return DifferenceInterval(
        difference=float((a.astype(float) - b.astype(float)).sum() / n),
        lo=percentile(s_, tail),
        hi=percentile(s_, 1 - tail),
        n=n,
        resamples=resamples,
        seed=str(seed),
        level=level,
        clusters=g,
    )
