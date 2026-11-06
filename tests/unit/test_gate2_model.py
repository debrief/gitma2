"""E-w (spec 007 T010): untrained it is C's physics-layer solve; its gradients are finite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from tma2.cli.oracle import inputs_for
from tma2.data.f32pack import iter_pack_raw
from tma2.gate2 import KNOTS
from tma2.gate2.inputs import code_channel, prefix_inputs
from tma2.gate2.model import EWeights
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment import STEADY, TRANSITION, Interval
from tma2.segment.score import g5_rows
from tma2.types.generated.tma import HeadActivation, PhysicsHead, PhysicsModelConfig


def _cfg() -> PhysicsModelConfig:
    return PhysicsModelConfig(
        id="ew-test",
        head=PhysicsHead.physics,
        causal=True,
        width=16,
        layers=1,
        heads=2,
        feedforward=32,
        weight_bound=3.0,
        scale_bound=2.0,
        iterations=40,
        head_activation=HeadActivation.tanh,
        loss_init_weight=0.0,
        loss_nll_weight=0.0,
        nll_beta=0.5,
        loss_cap=100.0,
        rows_per_scenario=4,
        noise_draws=1,
        batch_scenarios=4,
        learning_rate=1e-3,
        weight_decay=0.0,
        epochs=1,
        seed=1,
        patience=1,
        shuffle_labels=False,
        threads=1,
    )


def _items(pack: Path) -> tuple[list[tuple[BearingData, int, Any]], list[np.ndarray]]:
    items, codes = [], []
    for q, (_, m, own, _tgt, obs) in enumerate(iter_pack_raw(pack)):
        if q == 3:
            break
        d = bearing_data_from_arrays(m, own, obs)
        for k in g5_rows(m, d.n)[:2]:
            s = max(1, k - 60)
            ivs = [
                Interval(STEADY, 0, s - 1),
                Interval(TRANSITION, s, s + 11),
                Interval(STEADY, s + 12, k),
            ]
            inp = prefix_inputs(d, k, ivs, "gap", None)
            if inp is not None:
                items.append((d, k, inp))
                codes.append(code_channel(ivs, k, d.n))
    return items, codes


@pytest.fixture(scope="module")
def batch(man2_pack: Path) -> tuple[Any, torch.Tensor]:
    torch.set_default_dtype(torch.float64)
    items, codes = _items(man2_pack)
    r = max(d.n for d, _, _ in items)
    code = torch.tensor(np.stack([np.pad(c, (0, r - c.size)) for c in codes]))
    return (items, r), code


def test_untrained_ew_is_cs_solve(batch: tuple[Any, torch.Tensor]) -> None:
    (items, r), code = batch
    torch.manual_seed(0)
    model = EWeights(_cfg()).double()
    with torch.no_grad():
        e = model(inputs_for(items, r), code)
        c = PhysicsLayer(iterations=40, knots=KNOTS)(inputs_for(items, r))
    np.testing.assert_allclose(e.state.numpy(), c.state.numpy(), rtol=1e-12, atol=1e-9)


def test_gradients_are_finite(batch: tuple[Any, torch.Tensor]) -> None:
    (items, r), code = batch
    torch.manual_seed(1)
    model = EWeights(_cfg()).double()
    for p in model.parameters():  # move off zero so every head carries a gradient
        torch.nn.init.normal_(p, std=0.01)
    model.set_implicit(True)
    e = model(inputs_for(items, r), code)
    loss = (e.state[:, :2] ** 2).sum() * 1e-8 + (e.state[:, 2:] ** 2).sum()
    loss.backward()
    for name, p in model.named_parameters():
        if name.startswith("init_head."):
            # implicit differentiation gives the solve's start no gradient (spec 003 R1); the
            # init head is trained by the auxiliary initial-state loss
            assert p.grad is None
            continue
        assert p.grad is not None and torch.isfinite(p.grad).all(), name
    g = [p.grad for n, p in model.named_parameters() if n.startswith("weight_head.")]
    assert any(x is not None and float(x.abs().sum()) > 0 for x in g)
