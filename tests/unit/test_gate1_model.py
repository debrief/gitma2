"""The Gate 1 model (spec 003 FR-008, FR-009, FR-013; research R1, R3)."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import numpy as np
import pytest
import torch

from tests.conftest import fixture_dir
from tma2.features.batch import generate_batch
from tma2.models.batching import model_inputs, run
from tma2.models.config import model_config
from tma2.models.gate1 import Gate1Model
from tma2.models.loss import gate1_loss
from tma2.models.rows import row_batch, scenario_tensors
from tma2.physics.layer import PhysicsInputs, PhysicsLayer
from tma2.types.generated.tma import PhysicsHead

RANGES = json.loads((fixture_dir("iter4-seed777") / "ranges.json").read_text())


@pytest.fixture(scope="module")
def inputs() -> Any:
    torch.set_default_dtype(torch.float64)
    b = generate_batch(4242, 0, 12, RANGES)
    tens = scenario_tensors(b, seed=7, draws=2)
    rows = row_batch(b, tens, np.random.default_rng(0), per_scenario=4)
    samples = np.tile(b.samples, 2)
    return model_inputs(tens, rows, samples)


def test_untrained_model_is_the_trivial_physics_layer(inputs: Any) -> None:
    """FR-009: zero-initialised heads give uniform weights and the grid start, so the model's
    estimate is the physics layer with trivial inputs (batch least squares)."""
    torch.manual_seed(0)
    model = Gate1Model(model_config("t"))
    with torch.no_grad():
        out = run(model, inputs)
        x = inputs
        ref = PhysicsLayer(knots=0)(
            PhysicsInputs(
                bearing=x.bearing[x.source],
                valid=x.valid[x.source],
                own=torch.stack([x.ox[x.source], x.oy[x.source]], dim=2),
                t=x.t[x.source],
                sigma=x.sigma[x.source],
                k=x.k,
                changepoint=torch.zeros_like(x.bearing[x.source]),
                speed_weight=torch.zeros_like(x.bearing[x.source]),
                log_weight=torch.zeros_like(x.bearing[x.source]),
                theta0=x.theta_grid,
            )
        )
    # The corrected start goes through the state at the row and back, so it differs from the
    # grid start in the last bits; the solve then lands on the same answer (P0's rule: to 1e-6
    # relative where the row is determined).
    rel = ((out.state - ref.state).abs() / ref.state.abs().clamp_min(1.0)).max(dim=1).values
    sd_r = torch.sqrt(ref.cov[:, 0, 0] + ref.cov[:, 1, 1])
    determined = ref.cov_ok & (sd_r < 0.5 * ref.range)
    assert int(determined.sum()) >= 10
    assert float(rel[determined].max()) <= 1e-6, float(rel[determined].max())


@pytest.mark.parametrize("head", [PhysicsHead.physics, PhysicsHead.direct])
def test_every_gradient_is_finite(inputs: Any, head: PhysicsHead) -> None:
    torch.manual_seed(1)
    cfg = model_config("t", head=head)
    model = Gate1Model(cfg)
    # give the zero-initialised heads something to differentiate
    for p in model.parameters():
        if p.dim() > 1 and float(p.detach().abs().max()) == 0.0:
            torch.nn.init.normal_(p, std=0.01)
    model.set_implicit(True)
    out = run(model, inputs)
    loss = gate1_loss(out, inputs.truth, inputs.bound_cov, inputs.okx(), inputs.oky(), cfg)
    assert loss.rows > 0
    loss.total.backward()  # type: ignore[no-untyped-call]
    for name, p in model.named_parameters():
        assert p.grad is None or bool(torch.isfinite(p.grad).all()), name
    assert any(p.grad is not None and float(p.grad.abs().max()) > 0 for p in model.parameters())


def test_implicit_gradient_matches_the_converged_solve(inputs: Any) -> None:
    """FR-013 / research R1: the implicit step's gradient with respect to a bearing log-weight
    equals central differences of the converged solve, where those differences are stable."""
    x = inputs
    n = 6
    base = PhysicsInputs(
        bearing=x.bearing[x.source][:n],
        valid=x.valid[x.source][:n],
        own=torch.stack([x.ox[x.source], x.oy[x.source]], dim=2)[:n],
        t=x.t[x.source][:n],
        sigma=x.sigma[x.source][:n],
        k=x.k[:n],
        changepoint=torch.zeros_like(x.bearing[x.source][:n]),
        speed_weight=torch.zeros_like(x.bearing[x.source][:n]),
        log_weight=0.3 * torch.sin(torch.arange(x.bearing.shape[1])).expand(n, -1).clone(),
        theta0=x.theta_grid[:n],
    )
    w = torch.tensor([1e-4, 1e-4, 1.0, 1.0])

    def value(lw: torch.Tensor, implicit: bool) -> torch.Tensor:
        out = PhysicsLayer(knots=0, implicit=implicit)(dataclasses.replace(base, log_weight=lw))
        v: torch.Tensor = (out.state * w).sum()
        return v

    lw = base.log_weight.clone().requires_grad_(True)
    value(lw, True).backward()  # type: ignore[no-untyped-call]
    assert lw.grad is not None
    checked = 0
    for b in range(n):
        for i in (int(base.k[b]) - 1, int(base.k[b]) // 2):
            if base.valid[b, i] == 0:
                continue
            fds = []
            for eps in (1e-3, 3e-4):
                p, m = base.log_weight.clone(), base.log_weight.clone()
                p[b, i] += eps
                m[b, i] -= eps
                with torch.no_grad():
                    fds.append(float((value(p, False) - value(m, False)) / (2 * eps)))
            if abs(fds[0] - fds[1]) > 1e-3 * max(abs(fds[0]), 1e-6):
                continue  # finite differences unstable here (the solver's stopping rule)
            checked += 1
            g = float(lw.grad[b, i])
            assert abs(g - fds[0]) <= 2e-3 * max(abs(fds[0]), 1e-6), (b, i, g, fds)
    assert checked >= 4


def test_a_training_step_is_deterministic(inputs: Any) -> None:
    def step() -> list[torch.Tensor]:
        torch.manual_seed(5)
        cfg = model_config("t")
        model = Gate1Model(cfg)
        model.set_implicit(True)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        out = run(model, inputs)
        gate1_loss(
            out, inputs.truth, inputs.bound_cov, inputs.okx(), inputs.oky(), cfg
        ).total.backward()  # type: ignore[no-untyped-call]
        opt.step()
        return [p.detach().clone() for p in model.parameters()]

    a, b = step(), step()
    assert all(torch.equal(x, y) for x, y in zip(a, b, strict=True))
