"""Default detector configuration (spec 004 research R2–R5); every field lands in the plan."""

from __future__ import annotations

from typing import Any

from tma2.physics.reference import ITERATIONS
from tma2.types.generated.tma import DetectorConfig, DetectorVariant, HeadActivation

DEFAULTS: dict[str, Any] = {
    "variant": DetectorVariant.causal,
    # The Gate 1 encoder (spec 003 R3), so Gate 2 can start from it.
    "width": 64,
    "layers": 2,
    "heads": 4,
    "feedforward": 128,
    "head_activation": HeadActivation.tanh,  # R1: heads that cannot die
    "now_window_s": 60.0,  # Annex A §A.1
    "tolerance_s": 60.0,  # D1
    "held_leg_weight": 3.0,  # Annex A §A.4's held-leg weighting, declared before training
    "loss_now_weight": 1.0,
    "loss_boundary_weight": 1.0,
    "loss_kind_weight": 1.0,
    "loss_downstream_weight": 1.0,  # 0: the classification-only control
    "knots": 8,  # three manoeuvres need six; P0's count
    "iterations": ITERATIONS,
    "train_iterations": 50,  # spec 003 R4
    "downstream_rows": 2,  # a G5 row and a random post-zig row (R5)
    "noise_draws": 1,  # fresh scenarios every epoch
    "batch_scenarios": 64,  # T014: 27 ms per scenario locally at 64, 34 ms at 32
    "learning_rate": 1e-3,
    "weight_decay": 0.0,
    "epochs": 20,
    "patience": 4,
    "min_improvement": 1e-3,  # R11
    "seed": 1,
    "threads": 4,
}


def detector_config(id: str, **overrides: Any) -> DetectorConfig:
    return DetectorConfig(id=id, **{**DEFAULTS, **overrides})
