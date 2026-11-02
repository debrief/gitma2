"""Heads that cannot silently die (spec 004 R1, FR-001, FR-002; Gate 1 panel follow-up)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch
from safetensors.torch import load_file

from tma2.models.gate1 import Gate1Model, features
from tma2.models.heads import head, is_alive, liveness
from tma2.models.train import load_plan, model_from_plan
from tma2.types.generated.tma import HeadActivation

G1_MODELS = Path("experiments/20261101-g1-a-models/models")


def _train(module: torch.nn.Sequential, x: torch.Tensor, y: torch.Tensor, steps: int) -> None:
    opt = torch.optim.Adam(module.parameters(), lr=1e-2)
    for _ in range(steps):
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(module(x)[:, 0], y)
        loss.backward()  # type: ignore[no-untyped-call]
        opt.step()


def test_a_tanh_head_trained_on_varying_labels_is_alive() -> None:
    torch.manual_seed(0)
    x = torch.randn(512, 16, dtype=torch.float64)
    y = (x[:, 0] + 0.5 * x[:, 1] > 0).to(torch.float64)
    h = head(16, 1, HeadActivation.tanh).double()
    _train(h, x, y, 300)
    rec = liveness("test", h, x)
    assert is_alive(rec), rec


def test_an_untrained_or_dead_head_fails_the_check() -> None:
    x = torch.randn(256, 16, dtype=torch.float64)
    untrained = head(16, 1, HeadActivation.tanh).double()  # zero output layer: constant output
    assert not is_alive(liveness("untrained", untrained, x))
    dead = head(16, 1, None).double()  # relu with every hidden unit pushed negative
    first, last = dead[0], dead[2]
    assert isinstance(first, torch.nn.Linear) and isinstance(last, torch.nn.Linear)
    with torch.no_grad():
        first.bias.fill_(-100.0)
        last.weight.fill_(1.0)
    rec = liveness("dead", dead, x)
    assert rec.alive_share == 0.0 and not is_alive(rec)


@pytest.mark.skipif(not G1_MODELS.exists(), reason="Gate 1 models not present")
def test_gate1_weights_still_load_and_their_heads_are_dead() -> None:
    """Gate 1's committed weights load unchanged (relu heads, same keys), and the liveness check
    flags the carried model's heads as dead: the failure Gate 1's panel found."""
    torch.set_default_dtype(torch.float64)
    plan, _ = load_plan("configs/gate1/plan.json")
    cfg = model_from_plan(plan, "g1-physics-s2")
    model = Gate1Model(cfg)
    model.load_state_dict(load_file(str(G1_MODELS / "g1-physics-s2" / "best.safetensors")))
    ranges = json.loads(Path("tests/fixtures/gitma/iter4-seed777/ranges.json").read_text())
    from tma2.features.batch import generate_batch

    b = generate_batch(1, 0, 16, ranges)
    t = torch.from_numpy(b.t.astype("float64"))
    x = features(
        torch.from_numpy(b.bearing.astype("float64")),
        torch.from_numpy(b.valid.astype("float64")),
        torch.from_numpy(b.own[..., 0].astype("float64")),
        torch.from_numpy(b.own[..., 1].astype("float64")),
        t,
        torch.from_numpy(b.sigma.astype("float64")),
    )
    with torch.no_grad():
        h = model.encoder(x, torch.zeros_like(t, dtype=torch.bool))
    for name in ("weight_head", "init_head", "scale_head"):
        assert not is_alive(liveness(name, getattr(model, name), h)), name
