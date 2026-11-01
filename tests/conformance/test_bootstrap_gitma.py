"""Bootstrap intervals equal gitma's on the same inputs (spec 002 US4 acceptance 3).

The fixture is gitma's own ``bootstrap.js`` run on inputs with ties, +∞, NaN and shuffled,
uneven clusters (``scripts/bootstrap_fixture.mjs``); never regenerate it from gitma2.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.eval.bootstrap import (
    bootstrap_clustered_quantile_ratio,
    bootstrap_clustered_rate_difference,
    bootstrap_median,
    bootstrap_median_ratio,
)

CASES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "gitma" / "bootstrap" / "cases.json").read_text()
)


def _arr(xs: list[Any]) -> np.ndarray:
    return np.array([float(x) for x in xs], dtype=np.float64)  # float("NaN"/"Infinity") parse


A = _arr(CASES["inputs"]["a"])
B = _arr(CASES["inputs"]["b"])
CL = np.array(CASES["inputs"]["cluster"], dtype=np.int64)
GA = np.array(CASES["inputs"]["gross_a"], dtype=np.uint8)
GB = np.array(CASES["inputs"]["gross_b"], dtype=np.uint8)


def _same(mine: float, theirs: Any) -> None:
    t = float(theirs)
    assert (math.isnan(mine) and math.isnan(t)) or mine == t, (mine, t)


def test_inputs_exercise_edge_cases() -> None:
    assert np.isnan(A).any() and np.isinf(A).any() and np.isinf(B).any()
    assert len(np.unique(A[np.isfinite(A)])) < np.isfinite(A).sum()  # ties


def test_median() -> None:
    r = bootstrap_median(A, 500)
    g = CASES["median"]
    for k in ("median", "lo", "hi"):
        _same(getattr(r, k), g[k])


def test_median_ratio() -> None:
    r = bootstrap_median_ratio(A, B, 500)
    g = CASES["median_ratio"]
    for k in ("ratio", "lo", "hi"):
        _same(getattr(r, k), g[k])


@pytest.mark.parametrize(
    ("key", "q", "level"), [("clustered_q50", 0.5, 0.975), ("clustered_q90", 0.9, 0.95)]
)
def test_clustered_quantile_ratio(key: str, q: float, level: float) -> None:
    r = bootstrap_clustered_quantile_ratio(A, B, CL, q, level, 500)
    g = CASES[key]
    assert r.clusters == g["clusters"]
    for k in ("ratio", "lo", "hi"):
        _same(getattr(r, k), g[k])


def test_clustered_rate_difference() -> None:
    r = bootstrap_clustered_rate_difference(GA, GB, CL, 0.975, 500)
    g = CASES["clustered_rate_difference"]
    assert r.clusters == g["clusters"]
    for k in ("difference", "lo", "hi"):
        _same(getattr(r, k), g[k])


def test_zero_median_does_not_raise() -> None:
    zeros = np.zeros(20)
    r = bootstrap_clustered_quantile_ratio(np.ones(20), zeros, np.arange(20), 0.5, 0.95, 50)
    assert math.isinf(r.ratio) and math.isinf(r.lo)


def test_zero_median_denominator_equals_gitma() -> None:
    """A denominator whose median is 0 in some resamples: ratios are ∞ there, as in gitma."""
    z = _arr(CASES["inputs"]["zeroish"])
    r = bootstrap_clustered_quantile_ratio(A, z, CL, 0.5, 0.95, 200)
    g = CASES["zero_median"]
    for k in ("ratio", "lo", "hi"):
        _same(getattr(r, k), g[k])
