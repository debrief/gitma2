"""Spec 016's classical controls: the hedged track, the declaration rule, pooling, the
correlation estimate and the effective sd."""

from __future__ import annotations

import math

import numpy as np

from tma2.timelate.corr import MIN_SHARE, edited, effective, effective_sigma, estimate
from tma2.timelate.hedge import declared, hedged, pool, weights, with_quiet
from tma2.timelate.retest import Structure
from tma2.timelate.search import History

SIGMA = math.radians(1.0)


def _history(spans: list[list[float]], evidence: float, legs: float = -5.0) -> History:
    sp = np.array(spans, dtype=np.float64).reshape(-1, 2)
    theta = np.zeros(4 + 2 * sp.shape[0])
    fit = Structure(theta, sp, 0.0, np.zeros((3, 4)))
    kinds = np.ones((sp.shape[0], 2), dtype=bool)
    return History(fit, kinds, evidence, {"legs": legs})


def test_weights_follow_the_evidence_and_the_temperature() -> None:
    w = weights(np.array([0.0, -math.log(3.0), -np.inf]), 1.0)
    assert np.allclose(w, [0.75, 0.25, 0.0])
    flat = weights(np.array([0.0, -math.log(3.0)]), 1e9)
    assert np.allclose(flat, [0.5, 0.5], atol=1e-6)
    assert np.allclose(weights(np.array([-np.inf]), 1.0), [0.0])


def test_the_hedged_track_lies_between_its_candidates() -> None:
    a, b = np.zeros((4, 4)), np.ones((4, 4))
    h = hedged([a, b], np.array([0.0, -math.log(3.0)]), 1.0)
    assert np.allclose(h, 0.25)
    assert np.allclose(hedged([a], np.array([-7.0]), 3.0), a)  # one candidate: itself


def test_declaration_walks_the_path_until_every_manoeuvre_pays() -> None:
    path = [
        _history([[100, 200], [900, 1000]], -10.0),
        _history([[100, 200]], -10.5),  # the second manoeuvre is worth 0.5
        _history([], -14.5, legs=-4.0),  # the first is worth 4
    ]
    assert declared(path, 0.0) == 0
    assert declared(path, 1.0) == 1
    assert declared(path, 3.0) == 1
    assert declared(path, 5.0) == 2
    assert declared(path[:1], 99.0) == 0  # nothing to remove


def test_a_stated_quiet_probability_moves_only_the_last_step() -> None:
    some, none = _history([[100, 200]], -10.0), _history([], -11.0, legs=-4.0)
    assert with_quiet(some, 0.0) == some.evidence
    assert math.isclose(with_quiet(some, 0.1), -10.0 + math.log(0.9))
    gain = math.log(0.1 + 0.9 * math.exp(-4.0)) + 4.0
    assert math.isclose(with_quiet(none, 0.1), -11.0 + gain)
    assert declared([some, none], 0.5, 0.0) == 0
    assert declared([some, none], 0.5, 0.1) == 1  # quiet is now more probable


def test_pooling_keeps_a_history_once_and_orders_by_evidence() -> None:
    a = [(_history([[100, 200]], -3.0), "plain/v3"), (_history([], -9.0), "plain/v3")]
    b = [
        (_history([[130, 230]], -2.0), "plain/broad"),
        (_history([[600, 700]], -4.0), "plain/broad"),
    ]
    out = pool([a, b], 10)
    assert [g for _, g in out] == ["plain/broad", "plain/broad", "plain/v3"]
    assert [h.evidence for h, _ in out] == [-2.0, -4.0, -9.0]
    assert len(pool([a, b], 2)) == 2


def _bearings(share: float, tau: float, outliers: float, seed: int) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    n = 900
    t = np.arange(n) * 5.0
    rho = math.exp(-5.0 / tau) if tau else 0.0
    c = np.zeros(n)
    c[0] = rng.normal()
    for i in range(1, n):
        c[i] = rho * c[i - 1] + math.sqrt(1 - rho * rho) * rng.normal()
    e = (math.sqrt(1 - share) * rng.normal(size=n) + math.sqrt(share) * c) * SIGMA
    e += (rng.random(n) < outliers) * rng.normal(size=n) * 10 * SIGMA
    z = 0.3 * np.sin(t / 2000.0) + 1e-4 * t + e
    return t, np.zeros(n), np.zeros(n), z, np.ones(n, dtype=bool)


def test_the_correlation_estimate_on_white_correlated_and_wild_errors() -> None:
    for seed in range(5):
        t, ox, oy, z, v = _bearings(0.0, 0.0, 0.0, seed)
        assert estimate((t, ox, oy, z, v, SIGMA))[0] < MIN_SHARE
        t, ox, oy, z, v = _bearings(0.0, 0.0, 0.02, seed)
        assert estimate((t, ox, oy, z, v, SIGMA))[0] < MIN_SHARE  # outliers are not correlation
        t, ox, oy, z, v = _bearings(0.5, 60.0, 0.0, seed)
        share, tau = estimate((t, ox, oy, z, v, SIGMA))
        assert 0.3 < share < 0.7 and 25.0 < tau < 130.0


def test_the_effective_sd_matches_the_long_run_variance() -> None:
    assert effective_sigma(SIGMA, 0.0, 60.0, 5.0) == SIGMA
    rho = math.exp(-5.0 / 60.0)
    want = SIGMA * math.sqrt(0.5 + 0.5 * (1 + rho) / (1 - rho))
    assert math.isclose(effective_sigma(SIGMA, 0.5, 60.0, 5.0), want)
    # the variance of a long mean of such errors is that of independent errors of this sd
    rng = np.random.default_rng(3)
    n, reps = 2000, 400
    means = []
    for _ in range(reps):
        c = np.zeros(n)
        c[0] = rng.normal()
        g = rng.normal(size=n)
        for i in range(1, n):
            c[i] = rho * c[i - 1] + math.sqrt(1 - rho * rho) * g[i]
        means.append(float((math.sqrt(0.5) * rng.normal(size=n) + math.sqrt(0.5) * c).mean()))
    ratio = np.var(means) * n / (want / SIGMA) ** 2
    assert 0.8 < ratio < 1.2
    t, ox, oy, z, v = _bearings(0.5, 60.0, 0.0, 0)
    assert math.isclose(float(effective((t, ox, oy, z, v, SIGMA), 0.5, 60.0)[5]), want)


def test_editing_removes_wild_bearings_and_little_else() -> None:
    t, ox, oy, z, v = _bearings(0.0, 0.0, 0.0, 1)
    wild = np.arange(50, 900, 100)
    z[wild] += 10 * SIGMA
    pb, n = edited((t, ox, oy, z, v, SIGMA))
    assert not pb[4][wild].any()
    assert len(wild) <= n <= len(wild) + 5
