"""A toy model for the export harness: a small per-row MLP produces the physics layer's learned
inputs (changepoint, speed-continuity and bearing weights) from per-row features; the physics
layer produces the estimate. It exists to prove the export path before any real model (spec 002
US3); nothing about it is tuned."""

from __future__ import annotations

import torch
from torch import Tensor, nn

from tma2.physics.layer import PhysicsInputs, PhysicsLayer, cos_export
from tma2.physics.reference import ITERATIONS, TRIALS


class ToyEncoder(nn.Module):
    def __init__(self, hidden: int = 16) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(6, hidden), nn.Tanh(), nn.Linear(hidden, 4))

    def forward(
        self, bearing: Tensor, valid: Tensor, own: Tensor, t: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        feats = torch.stack(
            [
                torch.sin(bearing),
                cos_export(bearing),
                valid,
                own[..., 0] / 1e4,
                own[..., 1] / 1e4,
                t / 3600.0,
            ],
            dim=2,
        )
        h = self.net(feats)
        changepoint = torch.sigmoid(h[..., 0]) * valid
        speed_weight = torch.sigmoid(h[..., 1])
        log_weight = 0.5 * torch.tanh(h[..., 2])
        speed_skip = torch.sigmoid(h[..., 3])
        return changepoint, speed_weight, log_weight, speed_skip


class ToyModel(nn.Module):
    """Encoder + physics layer; forward takes flat tensors so it exports as one graph. The
    defaults are the production physics configuration (iterations, knots, damping trials and the
    speed-skip path the oracle uses), so the export check covers what gates run."""

    def __init__(self, iterations: int = ITERATIONS, knots: int = 8, trials: int = TRIALS) -> None:
        super().__init__()
        self.encoder = ToyEncoder()
        self.physics = PhysicsLayer(iterations=iterations, knots=knots, trials=trials)

    def forward(
        self,
        bearing: Tensor,
        valid: Tensor,
        own: Tensor,
        t: Tensor,
        sigma: Tensor,
        k: Tensor,
        theta0: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        cp, sw, lw, skip = self.encoder(bearing, valid, own, t)
        out = self.physics(
            PhysicsInputs(bearing, valid, own, t, sigma, k, cp, sw, lw, theta0, speed_skip=skip)
        )
        return out.state, out.cov, out.cost, out.plausible.to(bearing.dtype)
