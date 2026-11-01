"""Default Gate 1 model configuration (research R3); every field lands in the manifest."""

from __future__ import annotations

from typing import Any

from tma2.physics.reference import ITERATIONS
from tma2.types.generated.tma import PhysicsHead, PhysicsModelConfig

DEFAULTS: dict[str, Any] = {
    "head": PhysicsHead.physics,
    "causal": True,
    "width": 64,
    "layers": 2,
    "heads": 4,
    "feedforward": 128,
    "weight_bound": 2.0,
    "scale_bound": 2.0,
    "iterations": ITERATIONS,
    "loss_init_weight": 0.1,
    "loss_nll_weight": 1.0,
    "nll_beta": 0.5,
    "loss_cap": 100.0,
    "rows_per_scenario": 4,
    "noise_draws": 2,
    "batch_scenarios": 64,
    "learning_rate": 1e-3,
    "weight_decay": 0.0,
    "epochs": 20,
    "patience": 4,
    "seed": 1,
    "shuffle_labels": False,
    "threads": 4,
}


def model_config(id: str, **overrides: Any) -> PhysicsModelConfig:
    return PhysicsModelConfig(id=id, **{**DEFAULTS, **overrides})
