"""The detector model (spec 004 FR-012, FR-013, FR-015; R2)."""

from __future__ import annotations

import math

import numpy as np
import torch

from tma2.models.detector import (
    FEATURES,
    MIN_RATE_SAMPLES,
    RATE_WINDOW_ROWS,
    W_BIAS0,
    Detector,
    bearing_rate,
    features,
)
from tma2.types.generated.tma import DetectorConfig, DetectorVariant, HeadActivation


def config(variant: DetectorVariant = DetectorVariant.causal) -> DetectorConfig:
    return DetectorConfig(
        id="det-test",
        variant=variant,
        width=16,
        layers=1,
        heads=2,
        feedforward=32,
        head_activation=HeadActivation.tanh,
        now_window_s=60.0,
        tolerance_s=60.0,
        held_leg_weight=3.0,
        loss_now_weight=1.0,
        loss_boundary_weight=1.0,
        loss_kind_weight=1.0,
        loss_downstream_weight=1.0,
        knots=8,
        iterations=100,
        train_iterations=50,
        downstream_rows=2,
        noise_draws=1,
        batch_scenarios=4,
        learning_rate=1e-3,
        weight_decay=0.0,
        epochs=1,
        patience=1,
        min_improvement=1e-3,
        seed=1,
        threads=1,
    )


def _gitma_rate(t: np.ndarray, b: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """gitma ``trailingBearingRate`` transcribed."""
    n = t.shape[0]
    rate = np.zeros(n)
    ok = np.zeros(n)
    for i in range(n):
        if not v[i]:
            continue
        m = st = su = stt = stu = 0.0
        for k in range(max(0, i - RATE_WINDOW_ROWS + 1), i + 1):
            if not v[k]:
                continue
            tau = t[k] - t[i]
            d = b[k] - b[i]
            u = d - 2 * math.pi * math.floor(d / (2 * math.pi) + 0.5)
            m += 1
            st += tau
            su += u
            stt += tau * tau
            stu += tau * u
        den = m * stt - st * st
        if m < MIN_RATE_SAMPLES or not den > 0:
            continue
        rate[i] = (m * stu - st * su) / den
        ok[i] = 1
    return rate, ok


def _inputs(b: int = 3, r: int = 60, seed: int = 0) -> tuple[torch.Tensor, ...]:
    g = np.random.default_rng(seed)
    t = np.tile(np.arange(r) * 10.0, (b, 1))
    bearing = (0.3 + 1e-3 * t + 0.01 * g.standard_normal((b, r)) + 6.2 * (t > 300)) % (2 * math.pi)
    valid = (g.random((b, r)) > 0.1).astype(np.float64)
    window = np.ones((b, r))
    window[1, 40:] = 0
    own = np.zeros((b, r, 4))
    own[..., 0] = 5.0 * t
    own[..., 2] = 1.0
    own[..., 3] = 5.0
    return tuple(torch.tensor(a) for a in (bearing, valid, own, t, window))


def test_bearing_rate_matches_gitma() -> None:
    bearing, valid, _own, t, _w = _inputs()
    rate, ok = bearing_rate(t, bearing, valid)
    for i in range(t.shape[0]):
        er, eo = _gitma_rate(t[i].numpy(), bearing[i].numpy(), valid[i].numpy() > 0)
        np.testing.assert_allclose(rate[i].numpy(), er, rtol=1e-12, atol=1e-15)
        np.testing.assert_array_equal(ok[i].numpy(), eo)


def test_untrained_detector_outputs_no_knots() -> None:
    torch.manual_seed(0)
    bearing, valid, own, t, window = _inputs()
    x = features(bearing, valid, own, t, window)
    assert x.shape[2] == FEATURES and torch.isfinite(x).all()
    det = Detector(config()).double()
    q = torch.tensor([[59, 30], [39, -1], [10, 59]])
    out = det(x, window, q)
    assert torch.equal(out.p_change, torch.full_like(out.p_change, 0.5))
    assert torch.equal(out.p_kind, torch.full_like(out.p_kind, 0.5))
    w0 = 1.0 / (1.0 + math.exp(-W_BIAS0))
    assert out.w_change.max() <= w0 * (1 + 1e-12)
    assert out.w_change[0, 1, 31:].sum() == 0  # j > k
    assert out.w_change[1, 1].sum() == 0  # absent query
    assert out.w_change[1, 0, 40:].sum() == 0  # padded rows
    assert out.w_change[:, :, 0].sum() == 0  # no knot at row 0


def test_causal_variant_does_not_look_ahead() -> None:
    torch.manual_seed(1)
    bearing, valid, own, t, window = _inputs()
    det = Detector(config()).double()
    with torch.no_grad():
        for p in det.parameters():
            p.add_(0.1 * torch.randn_like(p))  # break the zero initialisation
    q = torch.tensor([[30, 20], [30, 20], [30, 20]])
    a = det(features(bearing, valid, own, t, window), window, q)
    b2 = bearing.clone()
    b2[:, 31:] += 0.5
    b = det(features(b2, valid, own, t, window), window, q)
    assert torch.allclose(a.p_change[:, :31], b.p_change[:, :31])
    assert torch.allclose(a.w_change, b.w_change) and torch.allclose(a.p_kind, b.p_kind)
    late = Detector(config(DetectorVariant.time_late)).double()
    late.load_state_dict(det.state_dict())
    c = late(features(bearing, valid, own, t, window), window, q)
    d = late(features(b2, valid, own, t, window), window, q)
    assert not torch.allclose(c.p_change[:, :31], d.p_change[:, :31])
