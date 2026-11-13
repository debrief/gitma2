"""The regressor (spec 012 research R2): a causal transformer over folded rows.

``patch`` consecutive rows are folded into one token; token j covers rows
[offset + j·patch, offset + (j + 1)·patch) and its output is the state at its last row. A causal
attention mask means a token's output reads rows up to its own last row only. To predict at an
arbitrary row k, choose offset = (k + 1) mod patch so that k ends a token.

Spec 016 (research R7) reuses it for whole periods: ``causal=False`` drops the attention mask
(every token reads the whole period; tokens beyond the period's rows are masked out as keys, so
the output does not depend on the padding), and ``manoeuvre_head`` adds a logit per token that
a target manoeuvre is in progress. The defaults are spec 012's model, bit for bit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
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
    # Share of each batch drawn with ``held_ranges`` (the same ranges with target legs longer
    # than any window: the target holds course). MAN2 scenarios almost never do (1 in 2,000).
    held_fraction: float = 0.0
    held_ranges: str = "configs/regress/held-course-ranges.json"
    precision: str = "amp"  # "amp" | "float32"
    # Spec 016 (PERIOD_FIELDS below): the whole-period model. At these defaults the
    # configuration is spec 012's and ``to_json`` omits them, so its digests do not move.
    causal: bool = True
    manoeuvre_head: bool = False
    manoeuvre_weight: float = 0.1  # of the logit's cross-entropy beside the state's β-NLL
    n_features: int = N_FEATURES
    data: str = "scenarios"  # "scenarios" (spec 012's stream) | "periods" (regress/period_data)
    mix: str = "configs/regress/tlm-mix.json"  # the period stream's mix
    monitor_start: int = 1 << 40  # first stream index of the period monitor

    def __post_init__(self) -> None:
        if self.data not in ("scenarios", "periods"):
            raise ValueError(f"data {self.data!r}")
        if self.n_features != N_FEATURES + (2 if self.data == "periods" else 0):
            raise ValueError("n_features: 7 for scenarios, 9 for periods (time and length)")
        if self.data == "periods" and self.val_seed != self.stream_seed:
            # the period monitor is a slice of the training stream: no other seed is read
            raise ValueError("data periods: val_seed must equal stream_seed")
        if self.inputs not in ("full", "ownship_only"):
            raise ValueError(f"inputs {self.inputs!r}")
        if not 0.0 <= self.held_fraction <= 1.0:
            raise ValueError("held_fraction must be in [0, 1]")
        if self.max_rows % self.patch_rows:
            raise ValueError("max_rows must be a multiple of patch_rows")

    def to_json(self) -> dict[str, Any]:
        """Every spec 012 field, and a spec 016 field only where it differs from its default
        (so a spec 012 configuration's JSON, and the digest over it, are what they were)."""
        d = asdict(self)
        for f in fields(self):
            if f.name in PERIOD_FIELDS and d[f.name] == f.default:
                del d[f.name]
        return d


PERIOD_FIELDS = (
    "causal",
    "manoeuvre_head",
    "manoeuvre_weight",
    "n_features",
    "data",
    "mix",
    "monitor_start",
)
"""Spec 016's additions to the configuration (to enter ``schema/tma.yaml`` with that spec's
schema change)."""


class Regressor(nn.Module):
    def __init__(self, cfg: RegressorConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.patch = cfg.patch_rows
        self.tokens = cfg.max_rows // cfg.patch_rows
        self.embed = nn.Linear(cfg.patch_rows * cfg.n_features, cfg.width)
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
        if cfg.manoeuvre_head:
            self.man_head = nn.Linear(cfg.width, 1)
            nn.init.zeros_(self.man_head.weight)
            nn.init.zeros_(self.man_head.bias)
        # float32 whatever the process default (the physics layer's code sets double)
        self.float()

    def encode(self, f: Tensor, offset: int = 0, mask: Tensor | None = None) -> Tensor:
        """f [B, R, F] → hidden [B, T, width]. ``mask`` [B, R]: rows that exist; read only by
        the non-causal model, where a token whose first row does not exist is no key."""
        b, r, nf = f.shape
        if offset:
            f = torch.cat([f[:, offset:], f.new_zeros(b, offset, nf)], dim=1)
        x = self.embed(f.reshape(b, r // self.patch, self.patch * nf))
        t = x.shape[1]
        x = x + self.pos[:t]
        if self.cfg.causal:
            causal = torch.triu(torch.ones(t, t, dtype=torch.bool, device=f.device), diagonal=1)
            h = self.encoder(x, mask=causal)
        elif mask is None:
            h = self.encoder(x)
        else:
            if offset:
                mask = torch.cat([mask[:, offset:], mask.new_zeros(b, offset)], dim=1)
            h = self.encoder(x, src_key_padding_mask=~mask[:, :: self.patch])
        out: Tensor = self.norm(h)
        return out

    def forward(
        self, f: Tensor, offset: int = 0, mask: Tensor | None = None
    ) -> tuple[Tensor, Tensor]:
        """f [B, R, F] → (mean [B, T, 3], log-variance [B, T, 3]); token j ends at row
        offset + (j + 1)·patch − 1. Rows before ``offset`` are dropped; the tail is zero-padded."""
        out = self.head(self.encode(f, offset, mask))
        return out[..., :N_TARGETS], out[..., N_TARGETS:].clamp(-12.0, 8.0)

    def forward_all(
        self, f: Tensor, offset: int = 0, mask: Tensor | None = None
    ) -> tuple[Tensor, Tensor, Tensor]:
        """As ``forward``, with the manoeuvre logit [B, T] (``manoeuvre_head`` models only)."""
        h = self.encode(f, offset, mask)
        out = self.head(h)
        logit = self.man_head(h)[..., 0]
        return out[..., :N_TARGETS], out[..., N_TARGETS:].clamp(-12.0, 8.0), logit


def beta_nll(mean: Tensor, logvar: Tensor, y: Tensor, w: Tensor, beta: float) -> Tensor:
    """β-weighted Gaussian negative log-likelihood over supervised tokens (w [B, T] in {0, 1})."""
    var = logvar.exp()
    nll = 0.5 * (logvar + (y - mean) ** 2 / var)
    if beta > 0:
        nll = nll * var.detach() ** beta
    return (nll.sum(dim=-1) * w).sum() / w.sum().clamp_min(1.0)


def manoeuvre_bce(logit: Tensor, label: Tensor, w: Tensor) -> Tensor:
    """Binary cross-entropy of the manoeuvre logit over tokens that exist (w [B, T])."""
    bce = nn.functional.binary_cross_entropy_with_logits(logit, label, reduction="none")
    return (bce * w).sum() / w.sum().clamp_min(1.0)
