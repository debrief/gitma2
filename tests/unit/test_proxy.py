"""Spec 010's causal unsettled proxy (T004)."""

from __future__ import annotations

import math

import numpy as np

from tma2.calib.proxy import DESIGN_NAMES, design, fit_proxy, residual_features, score


def _cv_track(n: int = 200, sigma: float = 0.01, seed: int = 0) -> tuple[np.ndarray, ...]:
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 10.0
    own = np.stack([t, 50.0 * np.sin(t / 300.0) * 0 + 3.0 * t, np.zeros(n)], axis=1)
    tgt = np.stack([5000.0 + 2.0 * t, 8000.0 - 1.0 * t], axis=1)
    b = np.arctan2(tgt[:, 0] - own[:, 1], tgt[:, 1] - own[:, 2]) + rng.normal(0, sigma, n)
    obs = np.stack([t, b, np.ones(n)], axis=1)
    return own, obs, tgt


def test_future_bearings_do_not_matter() -> None:
    own, obs, tgt = _cv_track()
    k = 150
    st = np.array([tgt[k, 0], tgt[k, 1], 2.0, -1.0])
    a = residual_features(st, k, own, obs, 0.01)
    obs2 = obs.copy()
    obs2[k + 1 :, 1] += 1.0
    assert residual_features(st, k, own, obs2, 0.01) == a


def test_true_cv_state_gives_small_bias() -> None:
    own, obs, tgt = _cv_track(seed=1)
    k = 150
    st = np.array([tgt[k, 0], tgt[k, 1], 2.0, -1.0])
    f = residual_features(st, k, own, obs, 0.01)
    assert f["bias6"] < 3.5 and f["bias30"] < 3.5
    assert 0.5 < f["chi60"] < 1.6


def test_a_manoeuvre_shows_in_the_recent_bias() -> None:
    own, obs, tgt = _cv_track(seed=2)
    k = 150
    st = np.array([tgt[k, 0], tgt[k, 1], 2.0, -1.0])
    obs2 = obs.copy()
    obs2[k - 5 : k + 1, 1] += 0.05  # a 5σ step in the last six bearings
    assert residual_features(st, k, own, obs2, 0.01)["bias6"] > 8.0


def test_proxy_fit_and_score() -> None:
    rng = np.random.default_rng(3)
    n = 4000
    feats = {f"bias{w}": np.abs(rng.normal(0, 1, n)) for w in (6, 12, 30)}
    feats["chi60"] = rng.gamma(2.0, 0.5, n)
    y = rng.random(n) < 1 / (1 + np.exp(-(feats["bias6"] - 1.0)))
    x = design(feats, rng.random(n) < 0.1, rng.normal(0, 1, (n, 3)), rng.integers(5, 21, n))
    d = fit_proxy(x, y)
    assert d["features"] == list(DESIGN_NAMES)
    s = score(d, x)
    assert np.corrcoef(s, feats["bias6"])[0, 1] > 0.5
    assert math.isfinite(d["intercept"])
