"""The on-the-fly training stream (spec 012 FR-002): scenarios from a seed, never stored."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tma2.features.batch import Batch, generate_indices

from .frame import features, targets
from .model import RegressorConfig


@dataclass
class Tensors:
    f: np.ndarray  # [B, R, 7]
    y: np.ndarray  # [B, R, 3]
    mask: np.ndarray  # [B, R] rows that exist
    zig: np.ndarray  # [B]
    index: np.ndarray  # [B]


def load_ranges(path: str) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(Path(path).read_text())
    return out


def tensors_of(b: Batch, cfg: RegressorConfig) -> Tensors:
    own = b.own[..., :2].astype(np.float64)
    f, th = features(b.t, own, b.bearing, b.valid, b.mask, b.sigma, cfg.inputs == "ownship_only")
    y = targets(own, b.tgt, th)
    r = cfg.max_rows
    if f.shape[1] < r:
        pad = r - f.shape[1]
        f = np.pad(f, ((0, 0), (0, pad), (0, 0)))
        y = np.pad(y, ((0, 0), (0, pad), (0, 0)))
        mask = np.pad(b.mask, ((0, 0), (0, pad)))
    else:
        f, y, mask = f[:, :r], y[:, :r], b.mask[:, :r]
    return Tensors(f, y, mask, b.zig_index.astype(np.int64), b.index)


def stream_indices(cfg: RegressorConfig, update: int) -> np.ndarray:
    """The scenario indices of update ``update`` (a pure function of the config, so a resumed
    run continues the same stream)."""
    lo = update * cfg.batch_scenarios
    idx = np.arange(lo, lo + cfg.batch_scenarios, dtype=np.int64)
    if cfg.stream_repeat > 0:
        idx = idx % cfg.stream_repeat
    return cfg.stream_start + idx


def batch_at(cfg: RegressorConfig, ranges: dict[str, Any], update: int) -> Tensors:
    return tensors_of(generate_indices(cfg.stream_seed, stream_indices(cfg, update), ranges), cfg)


def validation(cfg: RegressorConfig, ranges: dict[str, Any]) -> Tensors:
    idx = np.arange(cfg.val_count, dtype=np.int64)
    return tensors_of(generate_indices(cfg.val_seed, idx, ranges), cfg)


def supervised(mask: np.ndarray, patch: int, offset: int) -> np.ndarray:
    """[B, T] the tokens whose last row exists, and the row index [T] each token ends at."""
    r = mask.shape[1]
    last = offset + (np.arange(r // patch) + 1) * patch - 1
    ok = last < r
    w = np.zeros((mask.shape[0], r // patch), dtype=np.float32)
    w[:, ok] = mask[:, last[ok]]
    return w
