"""The regressor (spec 012 research R2): a causal transformer over folded rows.

``patch`` consecutive rows are folded into one token; token j covers rows
[offset + j·patch, offset + (j + 1)·patch) and its output is the state at its last row. A causal
attention mask means a token's output reads rows up to its own last row only. To predict at an
arbitrary row k, choose offset = (k + 1) mod patch so that k ends a token.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import torch
from torch import Tensor, nn

from .frame import N_FEATURES, N_TARGETS


@dataclass(frozen=True)
class RegressorConfig:
    id: str = "toy"
    seed: int = 1
    patch_rows: int = 3
    layers: int = 8
    width: int = 256
    heads: int = 8
    feedforward: int = 1024
    max_rows: int = 720
    beta: float = 0.5
    batch_scenarios: int = 256
    learning_rate: float = 3.0e-4
    warmup_updates: int = 2000
    total_updates: int = 40000
    weight_decay: float = 0.01
    stream_seed: int = 326
    stream_start: int = 0
    stream_repeat: int = 0  # 0: never repeat; n: cycle the first n scenarios
    inputs: str = "full"  # "full" | "ownship_only"
    limit_seconds: int = 3600
    checkpoint_seconds: int = 900
    val_seed: int = 327
    val_count: int = 512
    val_every_updates: int = 1000
    ranges: str = "configs/man2-ranges.json"
    precision: str = "amp"  # "amp" | "float32"

    def __post_init__(self) -> None:
        if self.inputs not in ("full", "ownship_only"):
            raise ValueError(f"inputs {self.inputs!r}")
        if self.max_rows % self.patch_rows:
            raise ValueError("max_rows must be a multiple of patch_rows")

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class Regressor(nn.Module):
    def __init__(self, cfg: RegressorConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.patch = cfg.patch_rows
        self.tokens = cfg.max_rows // cfg.patch_rows
        self.embed = nn.Linear(cfg.patch_rows * N_FEATURES, cfg.width)
        self.pos = nn.Parameter(torch.zeros(self.tokens, cfg.width))
        layer = nn.TransformerEncoderLayer(
            cfg.width,
            cfg.heads,
            cfg.feedforward,
            dropout=0.0,
            batch_first=True,
            norm_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, cfg.layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(cfg.width)
        self.head = nn.Linear(cfg.width, 2 * N_TARGETS)
        nn.init.normal_(self.pos, std=0.02)
        nn.init.zeros_(self.head.weight)
        nn.init.zeros_(self.head.bias)

    def forward(self, f: Tensor, offset: int = 0) -> tuple[Tensor, Tensor]:
        """f [B, R, 7] → (mean [B, T, 3], log-variance [B, T, 3]); token j ends at row
        offset + (j + 1)·patch − 1. Rows before ``offset`` are dropped; the tail is zero-padded."""
        b, r, nf = f.shape
        if offset:
            f = torch.cat([f[:, offset:], f.new_zeros(b, offset, nf)], dim=1)
        x = self.embed(f.reshape(b, r // self.patch, self.patch * nf))
        t = x.shape[1]
        x = x + self.pos[:t]
        causal = torch.triu(torch.ones(t, t, dtype=torch.bool, device=f.device), diagonal=1)
        h = self.norm(self.encoder(x, mask=causal))
        out = self.head(h)
        return out[..., :N_TARGETS], out[..., N_TARGETS:].clamp(-12.0, 8.0)


def beta_nll(mean: Tensor, logvar: Tensor, y: Tensor, w: Tensor, beta: float) -> Tensor:
    """β-weighted Gaussian negative log-likelihood over supervised tokens (w [B, T] in {0, 1})."""
    var = logvar.exp()
    nll = 0.5 * (logvar + (y - mean) ** 2 / var)
    if beta > 0:
        nll = nll * var.detach() ** beta
    return (nll.sum(dim=-1) * w).sum() / w.sum().clamp_min(1.0)
