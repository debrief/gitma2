"""The usable uncertainty statement (spec 009 T003)."""

from __future__ import annotations

import math

import numpy as np
import torch

from tma2.calib.statement import (
    arc,
    arc_prob,
    course_log_score,
    interval_score,
    interval_score_t,
    isotonic_apply,
    isotonic_fit,
    wrap,
)


def test_arc_prob_matches_the_mixture_integral() -> None:
    """P equals the numerical integral of the mixture density over ±X."""
    a, p, sd, xmax = np.array([1.3]), np.array([0.7]), np.array([0.12]), math.radians(45)
    x = arc(a, sd, xmax)
    grid = np.linspace(-x[0], x[0], 20001)
    dens = np.exp(course_log_score(grid, np.full_like(grid, a[0]), np.full_like(grid, p[0]),
                                   np.full_like(grid, sd[0])))  # fmt: skip
    integral = float(np.trapezoid(dens, grid))
    assert abs(arc_prob(p, a, sd, x)[0] - integral) < 2e-3


def test_unknown_course_is_uniform() -> None:
    x = np.array([math.radians(30)])
    assert abs(arc_prob(np.array([0.0]), np.array([1.0]), np.array([0.1]), x)[0] - 30 / 180) < 1e-12
    e = np.array([0.3, 2.5])
    ls = course_log_score(e, np.ones(2), np.zeros(2), np.full(2, 0.1))
    assert np.allclose(ls, -math.log(2 * math.pi), atol=1e-5)


def test_interval_score_minimised_at_the_95_quantile() -> None:
    rng = np.random.default_rng(1)
    abs_e = np.abs(rng.standard_t(3, 200_000))
    qs = np.linspace(1.0, 6.0, 501)
    best = qs[int(np.argmin([interval_score(abs_e, np.full_like(abs_e, q)).mean() for q in qs]))]
    assert abs(best - np.quantile(abs_e, 0.95)) < 0.05
    t = interval_score_t(torch.tensor([1.0, 3.0]), torch.tensor([2.0, 2.0]))
    assert torch.allclose(t, torch.tensor([4.0, 4.0 + 40.0]))


def test_isotonic_map() -> None:
    rng = np.random.default_rng(2)
    x = rng.random(5000)
    y = (rng.random(5000) < 0.2 + 0.6 * x).astype(float)  # increasing truth, noisy
    knots = isotonic_fit(x, y, 10)
    assert np.all(np.diff(knots[1]) >= -1e-12)
    f = isotonic_apply(np.array([0.05, 0.95]), knots)
    assert f[0] < 0.35 and f[1] > 0.65
    # already calibrated: close to the identity
    y2 = (rng.random(5000) < x).astype(float)
    g = isotonic_apply(np.array([0.25, 0.75]), isotonic_fit(x, y2, 10))
    assert np.allclose(g, [0.25, 0.75], atol=0.06)


def test_wrap() -> None:
    assert np.allclose(
        wrap(np.array([3 * math.pi / 2, -3 * math.pi / 2])), [-math.pi / 2, math.pi / 2]
    )
