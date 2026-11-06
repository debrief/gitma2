"""L's evidence network (spec 005 FR-040, FR-041, FR-043, research R6, R8).

A small causal 1-D convolution over per-bearing features emits, at every row, a log-likelihood
ratio e of steady against transition. It is causal, so e at row r uses rows ≤ r only and one
forward pass over the window serves every prefix (FR-002). The head is zero-initialised, so an
untrained L emits e = 0 everywhere and equals C exactly (SC-003); there is no ReLU before it
(Gate 1's dead heads), only SiLU, which exports with standard ONNX operators.

**Inputs** (FR-043), all from bearings, ownship navigation and O's labels, normalised from inputs
only:
* sin and cos of the bearing, the valid flag;
* ownship position (÷ 10 km) and time (÷ 1 h), relative to the window's first row;
* O's ownship labels, one-hot (steady, transition, unknown);
* the per-timestep batch least-squares innovation (GLR's input): the wrapped bearing residual
  against the previous row's estimate propagated, ÷ σ, clipped to ± 10, 0 where unavailable.
"""

from __future__ import annotations

import math

import numpy as np
import torch
from torch import Tensor, nn

from tma2.references.classical import BearingData
from tma2.types.generated.tma import SegmentParameters

from . import STEADY, TRANSITION, UNKNOWN, to_codes
from .ownship import segment_ownship

CHANNELS = 10


def innovations(d: BearingData, state: np.ndarray, ok: np.ndarray) -> np.ndarray:
    """Per-row bearing residual against the previous row's least-squares state propagated, ÷ σ
    (clipped to ± 10); 0 where the previous row has no usable estimate or the bearing is
    missing."""
    n = d.n
    out = np.zeros(n)
    s = max(float(d.sigma), 1e-4)
    for r in range(1, n):
        if not (ok[r - 1] and d.valid[r]):
            continue
        dt = float(d.t[r] - d.t[r - 1])
        x = state[r - 1, 0] + state[r - 1, 2] * dt - d.ox[r]
        y = state[r - 1, 1] + state[r - 1, 3] * dt - d.oy[r]
        res = (float(d.z[r]) - math.atan2(x, y) + math.pi) % (2 * math.pi) - math.pi
        out[r] = max(-10.0, min(10.0, res / s))
    return out


def features(d: BearingData, own_codes: np.ndarray, innov: np.ndarray) -> np.ndarray:
    """[CHANNELS, R] features for one scenario."""
    n = d.n
    f = np.zeros((CHANNELS, n))
    v = d.valid.astype(np.float64)
    f[0] = np.sin(d.z) * v
    f[1] = np.cos(d.z) * v
    f[2] = v
    f[3] = (d.ox - d.ox[0]) / 1e4
    f[4] = (d.oy - d.oy[0]) / 1e4
    f[5] = (d.t - d.t[0]) / 3600.0
    f[6] = own_codes[:n] == STEADY
    f[7] = own_codes[:n] == TRANSITION
    f[8] = own_codes[:n] == UNKNOWN
    f[9] = innov[:n]
    return f


def online_ownship_codes(
    course: np.ndarray, speed: np.ndarray, n: int, p: SegmentParameters
) -> np.ndarray:
    """O's label of each row r from O run on the prefix [0, r] alone: the causal ownship channel.
    (O on the whole window would label a row from ownship navigation after it, and the label of
    a row near a prefix's end changes with the prefix; this way one forward pass serves every
    prefix, FR-002.)"""
    out = np.full(n, UNKNOWN, dtype=np.int8)
    for r in range(n):
        out[r] = to_codes(segment_ownship(course, speed, r, p), r + 1)[r]
    return out


def scenario_features(d: BearingData, own: np.ndarray, p: SegmentParameters) -> np.ndarray:
    """[CHANNELS, n] causal features of one scenario: online O labels and per-timestep least
    squares innovations (``own`` columns 3 and 4 are course and speed)."""
    from tma2.detect.controls import ls_states
    from tma2.references.classical import classical_predict

    lst, lok = ls_states(d, classical_predict(d, "per_timestep")["rows"])
    oc = online_ownship_codes(own[:, 3], own[:, 4], d.n, p)
    return features(d, oc, innovations(d, lst, lok))


class CausalConv(nn.Module):
    def __init__(self, cin: int, cout: int, kernel: int, dilation: int) -> None:
        super().__init__()
        self.pad = (kernel - 1) * dilation
        self.conv = nn.Conv1d(cin, cout, kernel, dilation=dilation)

    def forward(self, x: Tensor) -> Tensor:
        out: Tensor = self.conv(nn.functional.pad(x, (self.pad, 0)))
        return out


class EvidenceNet(nn.Module):
    """[B, CHANNELS, R] → e [B, R]."""

    def __init__(
        self,
        width: int = 32,
        kernel: int = 5,
        dilations: tuple[int, ...] = (1, 2, 4, 8),
        channels: int = CHANNELS,
    ) -> None:
        super().__init__()
        self.inp = CausalConv(channels, width, kernel, 1)
        self.blocks = nn.ModuleList([CausalConv(width, width, kernel, d) for d in dilations])
        self.act = nn.SiLU()
        self.head = nn.Conv1d(width, 1, 1)
        nn.init.zeros_(self.head.weight)
        assert self.head.bias is not None
        nn.init.zeros_(self.head.bias)

    def forward(self, x: Tensor) -> Tensor:
        h = self.act(self.inp(x))
        for b in self.blocks:
            h = h + self.act(b(h))
        out: Tensor = self.head(h)[:, 0, :]
        return out

    def receptive_field(self) -> int:
        return 1 + sum(m.pad for m in self.modules() if isinstance(m, CausalConv))


def evidence_for(net: EvidenceNet, feats: list[np.ndarray]) -> list[np.ndarray]:
    """Evidence per scenario (variable lengths, padded on the right: causal, so padding never
    reaches an earlier row)."""
    r = max(f.shape[1] for f in feats)
    x = np.zeros((len(feats), feats[0].shape[0], r))
    for i, f in enumerate(feats):
        x[i, :, : f.shape[1]] = f
    with torch.no_grad():
        e = net(torch.tensor(x, dtype=next(net.parameters()).dtype)).numpy()
    return [e[i, : f.shape[1]].astype(np.float64) for i, f in enumerate(feats)]
