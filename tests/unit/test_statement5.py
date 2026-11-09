"""Spec 010's truncated course statement (T003)."""

from __future__ import annotations

import math

import numpy as np
import torch

from tma2.calib.statement import (
    arc_norm,
    platt_apply,
    platt_fit,
    truncated_log_score,
    truncated_log_score_t,
    vm_arc_mass,
)


def _dense(f, a: float, b: float, n: int = 400001) -> float:  # type: ignore[no-untyped-def]
    g = np.linspace(a, b, n)
    return float(np.trapezoid(f(g), g))


def test_arc_norm_matches_dense_integral_narrow_and_broad() -> None:
    for kappa, x in [(0.5, 0.7), (20.0, 0.785), (3e4, 0.785), (1e6, 0.3)]:
        want = _dense(lambda t, k=kappa: np.exp(k * (np.cos(t) - 1.0)), -x, x)
        got = float(arc_norm(np.array([kappa]), np.array([x]))[0])
        assert abs(got / want - 1.0) < 1e-6, (kappa, got, want)


def test_density_integrates_to_one_and_arc_mass_is_p() -> None:
    x, p, kappa = 0.6, 0.73, 15.0
    f = lambda e: np.exp(  # noqa: E731
        truncated_log_score(e, np.full_like(e, x), np.full_like(e, p), np.full_like(e, kappa))
    )
    total = _dense(f, -math.pi, math.pi, 2_000_001)
    inside = _dense(f, -x, x)
    assert abs(total - 1.0) < 1e-4
    assert abs(inside - p) < 1e-6


def test_vm_arc_mass_whole_circle_is_one() -> None:
    assert abs(float(vm_arc_mass(np.array([4.0]), np.array([math.pi]))[0]) - 1.0) < 1e-9


def test_log_score_is_proper_in_p() -> None:
    """The expected log score over a population with hit rate 0.6 peaks at P = 0.6."""
    rng = np.random.default_rng(3)
    x, kappa = 0.5, 10.0
    hit = rng.random(20000) < 0.6
    e = np.where(hit, rng.uniform(-x, x, hit.size), rng.uniform(x + 1e-6, math.pi, hit.size))
    ps = np.linspace(0.3, 0.9, 61)
    scores = [
        truncated_log_score(
            e, np.full_like(e, x), np.full_like(e, p), np.full_like(e, kappa)
        ).mean()
        for p in ps
    ]
    assert abs(ps[int(np.argmax(scores))] - hit.mean()) < 0.011


def test_torch_matches_numpy() -> None:
    e = np.array([0.1, -0.4, 2.0, 3.1])
    x, p, k = np.full(4, 0.5), np.full(4, 0.7), np.array([2.0, 50.0, 5.0, 1e5])
    a = truncated_log_score(e, x, p, k)
    b = truncated_log_score_t(*(torch.tensor(v) for v in (e, x, p, k))).numpy()
    assert np.allclose(a, b, rtol=0, atol=1e-12)


def test_platt_recovers_a_known_map() -> None:
    rng = np.random.default_rng(4)
    p = rng.uniform(0.2, 0.9, 50000)
    lp = np.log(p / (1 - p))
    true = 1 / (1 + np.exp(-(0.3 + 0.5 * lp)))
    hit = (rng.random(p.size) < true).astype(float)
    a, b = platt_fit(p, hit)
    assert abs(a - 0.3) < 0.05 and abs(b - 0.5) < 0.05
    assert np.allclose(platt_apply(p, (a, b)), true, atol=0.03)
