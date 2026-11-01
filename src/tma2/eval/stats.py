"""Nearest-rank statistics (gitma ``packages/eval/src/stats.ts``): NaN sorts as +∞."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np


def ascending(xs: Sequence[float] | np.ndarray) -> np.ndarray:
    a = np.asarray(xs, dtype=np.float64).copy()
    a[np.isnan(a)] = np.inf
    a.sort()
    return a


def percentile(sorted_xs: np.ndarray, p: float) -> float:
    """Nearest-rank percentile (p in (0, 1]) of an ascending array; NaN when empty."""
    n = int(sorted_xs.shape[0])
    if n == 0:
        return math.nan
    k = max(1, math.ceil(p * n))
    return float(sorted_xs[k - 1])


def median(sorted_xs: np.ndarray) -> float:
    return percentile(sorted_xs, 0.5)


def mean(xs: Sequence[float] | np.ndarray) -> float:
    a = np.asarray(xs, dtype=np.float64)
    return math.nan if a.size == 0 else float(a.sum() / a.size)
