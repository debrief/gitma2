"""Gate 2's model E, part E-w (spec 007 research R2, R3; task T013).

The Gate 1 encoder (``models.gate1``: causal transformer, smooth heads, zero last layers) reads
spec 003's per-row features plus C's code at the prefix (``gate2.inputs.code_channel``). Its
heads give
* a per-bearing log-weight, ``weight_bound · tanh(·)``, added to C's hand-over log-weights (so
  masked transition bearings stay masked), and
* at the scored row, a correction (Δ log range, Δ course, Δ log speed) to C's grid start.
The physics layer, with C's knots (cap ``KNOTS``), computes the estimate by its damped solve,
differentiated implicitly. With zero heads E-w is C's physics-layer solve exactly (FR-022).

Rows after k are cut from the encoder's input (valid = 0, code 0), so nothing after the prefix
reaches it (FR-023).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn

from tma2.models.gate1 import FEATURES, Encoder, Gate1Model, features
from tma2.models.heads import head
from tma2.physics.layer import PhysicsInputs, PhysicsLayer
from tma2.types.generated.tma import PhysicsModelConfig

from . import KNOTS


@dataclass
class EOutput:
    state: Tensor  # [N, 4] (x, y, vx, vy) at the row
    cov: Tensor  # [N, 4, 4]
    plausible: Tensor  # [N] bool
    log_weight: Tensor  # [N, R] the log-weights the solve used


class EWeights(nn.Module):
    def __init__(self, cfg: PhysicsModelConfig, knots: int = KNOTS) -> None:
        super().__init__()
        if not cfg.causal:
            raise ValueError("E-w is causal (FR-023)")
        self.cfg = cfg
        self.encoder = Encoder(cfg)
        self.encoder.embed = nn.Linear(FEATURES + 1, cfg.width)  # + C's code channel
        w = cfg.width
        self.weight_head = head(w, 1, cfg.head_activation)
        self.init_head = head(w, 3, cfg.head_activation)
        self.physics = PhysicsLayer(iterations=cfg.iterations, knots=knots)

    def set_implicit(self, implicit: bool) -> None:
        self.physics.implicit = implicit

    def forward(self, x: PhysicsInputs, code: Tensor) -> EOutput:
        """``x``: C's hand-over inputs for N prefixes (``cli.oracle.inputs_for``); ``code``: [N, R]
        C's code channel at each prefix."""
        r = x.bearing.shape[1]
        idx = torch.arange(r, device=x.bearing.device).unsqueeze(0)
        upto = (idx <= x.k.unsqueeze(1)).to(x.bearing.dtype)
        valid = x.valid * upto
        ox, oy = x.own[..., 0], x.own[..., 1]
        f = features(x.bearing * upto, valid, ox * upto, oy * upto, x.t * upto, x.sigma)
        f = torch.cat([f, (code * upto).unsqueeze(2)], dim=2)
        pad = idx > x.k.unsqueeze(1)
        h = self.encoder(f, pad)  # [N, R, W], causal
        rows = torch.arange(x.k.shape[0], device=h.device)
        hk = h[rows, x.k]
        log_w = x.log_weight + self.cfg.weight_bound * torch.tanh(self.weight_head(h)[..., 0])
        tk = x.t[rows, x.k]
        okx, oky = ox[rows, x.k], oy[rows, x.k]
        delta = self.init_head(hk)
        # the correction as a difference from the zero correction, so zero heads give C's start
        # bit for bit (the round trip through the row's state is not exact in floating point)
        moved, _ = Gate1Model._corrected_start(x.theta0, delta, tk, okx, oky)
        still, _ = Gate1Model._corrected_start(x.theta0, torch.zeros_like(delta), tk, okx, oky)
        theta0 = x.theta0 + (moved - still)
        out = self.physics(
            PhysicsInputs(
                bearing=x.bearing,
                valid=x.valid,
                own=x.own,
                t=x.t,
                sigma=x.sigma,
                k=x.k,
                changepoint=x.changepoint,
                speed_weight=x.speed_weight,
                log_weight=log_w,
                theta0=theta0,
                speed_skip=x.speed_skip,
            )
        )
        return EOutput(out.state, out.cov, out.plausible, log_w)
