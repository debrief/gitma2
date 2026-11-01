"""The Gate 1 model (spec 003; research R3).

A causal transformer reads per-timestep bearing features. Its heads give the physics layer what
physics cannot know: a log-weight per bearing (from that bearing's token), and at the scored row
a correction to the classical grid start and a covariance log-scale. The physics layer (no
knots) computes the estimate. The last layer of every head starts at zero, so the untrained
model is exactly the physics layer with trivial inputs, i.e. batch least squares (FR-009).

Control (a), ``head = direct``, regresses log range, course and log speed at the row from the
same encoder, with a log-variance head for the NLL term. Control (d), ``causal = false``, uses
an unmasked encoder and the physics layer over the whole window, reporting the row's state.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor, nn
from torch.nn import functional as F  # noqa: N812

from tma2.physics.layer import PhysicsInputs, PhysicsLayer, cos_export
from tma2.types.generated.tma import PhysicsHead, PhysicsModelConfig

FEATURES = 7
POS_SCALE_M = 1e4
TIME_SCALE_S = 3600.0
SIGMA_SCALE_RAD = math.radians(2.0)


def features(
    bearing: Tensor, valid: Tensor, ox: Tensor, oy: Tensor, t: Tensor, sigma: Tensor
) -> Tensor:
    """[S, R, 7] with fixed scales only (no statistics from data; constitution IV)."""
    v = valid
    return torch.stack(
        [
            torch.sin(bearing) * v,
            cos_export(bearing) * v,
            v,
            (ox - ox[:, :1]) / POS_SCALE_M,
            (oy - oy[:, :1]) / POS_SCALE_M,
            t / TIME_SCALE_S,
            (sigma / SIGMA_SCALE_RAD).unsqueeze(1).expand_as(t),
        ],
        dim=2,
    )


class Block(nn.Module):
    """Pre-norm transformer layer written out in standard operators (matrix products, softmax,
    layer norm), so the export needs no fused attention kernel and the algorithm note can state
    it: h ← h + Wₒ·softmax(QKᵀ/√d + M)V over heads, then h ← h + W₂·relu(W₁·LN(h)), with
    Q, K, V = LN(h)·W_q, W_k, W_v and M = −∞ on masked pairs (future rows when causal, padded
    rows otherwise)."""

    def __init__(self, width: int, heads: int, feedforward: int) -> None:
        super().__init__()
        self.heads = heads
        self.norm1 = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.out = nn.Linear(width, width)
        self.norm2 = nn.LayerNorm(width)
        self.ff1 = nn.Linear(width, feedforward)
        self.ff2 = nn.Linear(feedforward, width)

    def forward(self, h: Tensor, masked: Tensor) -> Tensor:
        """h [S, R, W]; masked [S or 1, R, R] bool, True where query i may not see key j."""
        s_, r, w = h.shape
        d = w // self.heads
        q, k, v = self.qkv(self.norm1(h)).chunk(3, dim=2)

        def split(x: Tensor) -> Tensor:
            return x.reshape(s_, r, self.heads, d).transpose(1, 2)  # [S, H, R, d]

        if torch.jit.is_tracing():  # type: ignore[attr-defined,no-untyped-call]
            # The export: the equations as written (standard operators only).
            scores = split(q) @ split(k).transpose(2, 3) / math.sqrt(d)
            scores = torch.where(masked.unsqueeze(1), torch.full_like(scores, -math.inf), scores)
            att = torch.softmax(scores, dim=3) @ split(v)  # [S, H, R, d]
        else:
            # Training and prediction: PyTorch's fused kernel, the same function to ~1e-15 in
            # double and 7x faster (spec 003 research R4; True in its mask = may attend).
            att = F.scaled_dot_product_attention(
                split(q), split(k), split(v), attn_mask=~masked.unsqueeze(1)
            )
        h = h + self.out(att.transpose(1, 2).reshape(s_, r, w))
        out: Tensor = h + self.ff2(torch.relu(self.ff1(self.norm2(h))))
        return out


class Encoder(nn.Module):
    """Linear embedding, pre-norm transformer blocks and a final layer norm; causal unless
    ``causal`` is false (then padded rows are masked as keys)."""

    def __init__(self, cfg: PhysicsModelConfig) -> None:
        super().__init__()
        self.causal = cfg.causal
        self.embed = nn.Linear(FEATURES, cfg.width)
        self.layers = nn.ModuleList(
            Block(cfg.width, cfg.heads, cfg.feedforward) for _ in range(cfg.layers)
        )
        self.norm = nn.LayerNorm(cfg.width)

    def forward(self, x: Tensor, pad: Tensor) -> Tensor:
        r = x.shape[1]
        if self.causal:
            idx = torch.arange(r, device=x.device)
            masked = (idx.unsqueeze(0) > idx.unsqueeze(1)).unsqueeze(0)  # key j > query i
        else:
            masked = pad.unsqueeze(1).expand(-1, r, -1)  # padded keys
        h = self.embed(x)
        for layer in self.layers:
            h = layer(h, masked)
        out: Tensor = self.norm(h)
        return out


def _zero_linear(n_in: int, n_out: int) -> nn.Linear:
    lin = nn.Linear(n_in, n_out)
    nn.init.zeros_(lin.weight)
    nn.init.zeros_(lin.bias)
    return lin


@dataclass
class ModelOutput:
    state: Tensor  # [N, 4] (x, y, vx, vy) at the row
    cov: Tensor  # [N, 4, 4] calibrated covariance
    init_state: Tensor  # [N, 4] the initial state's (x, y, vx, vy) at the row
    cov_ok: Tensor  # [N] bool
    plausible: Tensor  # [N] bool
    # Control (a) only: log variances of (log range, vx, vy) relative to the bound's.
    log_var_rel: Tensor | None = None


class Gate1Model(nn.Module):
    def __init__(self, cfg: PhysicsModelConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.encoder = Encoder(cfg)
        w = cfg.width
        self.weight_head = nn.Sequential(nn.Linear(w, w), nn.ReLU(), _zero_linear(w, 1))
        self.init_head = nn.Sequential(nn.Linear(w, w), nn.ReLU(), _zero_linear(w, 3))
        self.scale_head = nn.Sequential(nn.Linear(w, w), nn.ReLU(), _zero_linear(w, 1))
        self.direct_head = nn.Sequential(nn.Linear(w, w), nn.ReLU(), _zero_linear(w, 6))
        self.physics = PhysicsLayer(iterations=cfg.iterations, knots=0)

    def set_implicit(self, implicit: bool) -> None:
        self.physics.implicit = implicit

    def forward(
        self,
        bearing: Tensor,  # [S, R]
        valid: Tensor,
        ox: Tensor,
        oy: Tensor,
        t: Tensor,
        sigma: Tensor,  # [S]
        n_rows: Tensor,  # [S] int64: samples in each window (for the time-late solve)
        source: Tensor,  # [N] int64 into S
        k: Tensor,  # [N] int64
        theta_grid: Tensor,  # [N, 4]
    ) -> ModelOutput:
        cfg = self.cfg
        r = bearing.shape[1]
        pad = torch.arange(r, device=bearing.device).unsqueeze(0) >= n_rows.unsqueeze(1)
        h = self.encoder(features(bearing, valid, ox, oy, t, sigma), pad)  # [S, R, W]
        hk = h[source, k]  # [N, W]
        tk = t[source, k]
        okx, oky = ox[source, k], oy[source, k]
        if cfg.head == PhysicsHead.direct:
            return self._direct(hk, tk, okx, oky, theta_grid)
        log_w = cfg.weight_bound * torch.tanh(self.weight_head(h)[..., 0])  # [S, R]
        delta = self.init_head(hk)  # [N, 3]: Δ log range, Δ course, Δ log speed
        theta0, init_state = self._corrected_start(theta_grid, delta, tk, okx, oky)
        k_solve = k if cfg.causal else (n_rows[source] - 1)
        out = self.physics(
            PhysicsInputs(
                bearing=bearing[source],
                valid=valid[source],
                own=torch.stack([ox[source], oy[source]], dim=2),
                t=t[source],
                sigma=sigma[source],
                k=k_solve,
                changepoint=torch.zeros_like(bearing[source]),
                speed_weight=torch.zeros_like(bearing[source]),
                log_weight=log_w[source],
                theta0=theta0,
                k_state=None if cfg.causal else k,
            )
        )
        scale = cfg.scale_bound * torch.tanh(self.scale_head(hk)[..., 0])
        cov = out.cov * torch.exp(2.0 * scale).view(-1, 1, 1)
        return ModelOutput(out.state, cov, init_state, out.cov_ok, out.plausible)

    @staticmethod
    def _corrected_start(
        theta_grid: Tensor, delta: Tensor, tk: Tensor, okx: Tensor, oky: Tensor
    ) -> tuple[Tensor, Tensor]:
        """Apply (Δ log range, Δ course, Δ log speed) to the grid start's state at the row and
        return the window-start state for the solve and the corrected state at the row."""
        px = theta_grid[:, 0] + theta_grid[:, 2] * tk
        py = theta_grid[:, 1] + theta_grid[:, 3] * tk
        rx, ry = px - okx, py - oky
        grow = torch.exp(delta[:, 0])
        px, py = okx + rx * grow, oky + ry * grow
        vx, vy = theta_grid[:, 2], theta_grid[:, 3]
        ca, sa = cos_export(delta[:, 1]), torch.sin(delta[:, 1])
        sp = torch.exp(delta[:, 2])
        # course is clockwise from north: rotating (vx, vy) by +δ clockwise
        vx2 = sp * (vx * ca + vy * sa)
        vy2 = sp * (-vx * sa + vy * ca)
        state = torch.stack([px, py, vx2, vy2], dim=1)
        theta0 = torch.stack([px - vx2 * tk, py - vy2 * tk, vx2, vy2], dim=1)
        return theta0, state

    def _direct(
        self, hk: Tensor, tk: Tensor, okx: Tensor, oky: Tensor, theta_grid: Tensor
    ) -> ModelOutput:
        """Control (a): corrections (Δ log range, Δ course, Δ log speed) to the grid start's state
        at the row, so it starts where the physics model starts, and three log-variances relative
        to the bound for the NLL term; no physics layer."""
        o = self.direct_head(hk)  # [N, 7]
        _, state = self._corrected_start(theta_grid, o[:, :3], tk, okx, oky)
        n = hk.shape[0]
        ok = torch.ones(n, dtype=torch.bool, device=hk.device)
        cov = torch.zeros(n, 4, 4, dtype=hk.dtype, device=hk.device)
        log_var = 6.0 * torch.tanh(o[:, 3:6])
        return ModelOutput(state, cov, state, ok, ok, log_var)
