"""Inputs for the physics layer from known information: trivial (batch least squares) and
oracle (truth manoeuvre spans). A learned segmenter (Annex A) will produce the same arrays."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch

from tma2.references import lsq


@dataclass
class LayerInputs:
    changepoint: np.ndarray  # [R] in [0, 1]
    speed_weight: np.ndarray  # [R] in [0, 1]
    log_weight: np.ndarray  # [R]
    theta0: np.ndarray  # [4]
    speed_skip: np.ndarray | None = None  # [R]


def trivial_inputs(
    t: np.ndarray, ox: np.ndarray, oy: np.ndarray, z: np.ndarray, valid: np.ndarray, k: int
) -> LayerInputs | None:
    """No knots, uniform weights, gitma's grid start on samples [0, k]; None without a valid
    bearing."""
    found, th0 = lsq.grid_start(t, ox, oy, z, valid.astype(np.uint8), k + 1)
    if not found:
        return None
    n = t.shape[0]
    return LayerInputs(np.zeros(n), np.zeros(n), np.zeros(n), np.array(th0, dtype=np.float64))


# exp(−60) ≈ 1e-26: a bearing with this log-weight carries no information.
MASKED_LOG_WEIGHT = -60.0


def oracle_inputs(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    k: int,
    spans: list[dict[str, Any]] | None,
    speed_prior: bool,
    mask_turns: bool = False,
) -> LayerInputs | None:
    """Truth segmentation: a hard knot at each span's start and end that is ≤ k (the chord
    approximation of docs/research/05); across a course-only span the speed-continuity weight is
    1 at the span's end knot when ``speed_prior``; grid start as the trivial inputs.

    Conventions: a span's ``start_index`` is the first sample after the manoeuvre begins (it
    begins exactly at row start_index − 1) and ``end_index`` the first sample after it ends. The
    speed prior is applied once the span has ended (end ≤ k); docs/research/05 also applied it
    across a span still in progress (min(end, k)), which differs only on in-turn rows, never on
    G5 rows after a completed manoeuvre. ``mask_turns`` (a diagnostic, panel round 1) gives the
    bearings inside each span (rows start … end − 1) zero weight, so the chord need not fit the
    arc: it shows how much of the oracle's error is the chord approximation."""
    base = trivial_inputs(t, ox, oy, z, valid, k)
    if base is None:
        return None
    n = t.shape[0]
    cp = np.zeros(n)
    sw = np.zeros(n)
    sk = np.zeros(n)
    lw = np.zeros(n)
    for s in spans or []:
        a, b = int(s["start_index"]), int(s["end_index"])
        for r in (a, b):
            if 0 < r <= k:
                cp[r] = 1.0
        if mask_turns:
            lw[a : min(b, k + 1)] = MASKED_LOG_WEIGHT
        if speed_prior and s.get("kind") == "course" and 0 < a <= k and b <= k:
            # The prior ties the speed after the manoeuvre to the speed before it: it sits on the
            # end knot and skips the start knot's increment (the chord leg inside the turn).
            sw[b] = 1.0
            sk[b] = 1.0
    return LayerInputs(cp, sw, lw, base.theta0, sk)


GRID_SPEEDS = (2.0, 5.0, 9.0)


def grid_start_tensor(
    t: torch.Tensor,
    ox: torch.Tensor,
    oy: torch.Tensor,
    z: torch.Tensor,
    valid: torch.Tensor,
    k: torch.Tensor,
) -> torch.Tensor:
    """gitma's coarse grid start (``lsq.grid_start``) in tensor operations, for the exported graph
    (spec 003): 12 log-spaced ranges 1–40 km along the first valid bearing up to row k, × 8
    courses × 3 speeds; the candidate with the lowest cost over valid samples ≤ k (the first one
    on ties, as the scalar loop's strict comparison). [B, R] inputs, k [B] → [B, 4]."""
    from tma2.physics.layer import atan2_export, cos_export, wrap_pi

    b, r = t.shape
    dt = t.dtype
    idx = torch.arange(r, device=t.device).unsqueeze(0)
    use = (valid > 0) & (idx <= k.unsqueeze(1))
    i0 = (
        torch.where(use, idx, torch.full_like(idx, r))
        .min(dim=1, keepdim=True)
        .values.clamp_max(r - 1)
    )
    t0 = torch.gather(t, 1, i0)
    ox0 = torch.gather(ox, 1, i0)
    oy0 = torch.gather(oy, 1, i0)
    b0 = torch.gather(z, 1, i0)
    ri = torch.arange(12, dtype=dt, device=t.device)
    rng = 1000.0 * torch.pow(torch.full_like(ri, 40.0), ri / 11.0)  # [12]
    course = torch.arange(8, dtype=dt, device=t.device) * (2.0 * math.pi / 8.0)
    speed = torch.tensor(GRID_SPEEDS, dtype=dt, device=t.device)
    # candidate order as the scalar loop: range-major, then course, then speed
    rr = rng.view(12, 1, 1).expand(12, 8, 3).reshape(-1)
    cc = course.view(1, 8, 1).expand(12, 8, 3).reshape(-1)
    ss = speed.view(1, 1, 3).expand(12, 8, 3).reshape(-1)
    px = ox0 + rr.unsqueeze(0) * torch.sin(b0)  # [B, 288]
    py = oy0 + rr.unsqueeze(0) * cos_export(b0)
    vx = (ss * torch.sin(cc)).unsqueeze(0).expand(b, -1)
    vy = (ss * cos_export(cc)).unsqueeze(0).expand(b, -1)
    x0 = px - vx * t0
    y0 = py - vy * t0
    dx = x0.unsqueeze(2) + vx.unsqueeze(2) * t.unsqueeze(1) - ox.unsqueeze(1)  # [B, 288, R]
    dy = y0.unsqueeze(2) + vy.unsqueeze(2) * t.unsqueeze(1) - oy.unsqueeze(1)
    res = wrap_pi(z.unsqueeze(1) - atan2_export(dx, dy))
    cost = (res * res * use.unsqueeze(1).to(dt)).sum(dim=2)  # [B, 288]
    best = torch.argmin(cost, dim=1, keepdim=True)
    return torch.stack(
        [
            torch.gather(x0, 1, best)[:, 0],
            torch.gather(y0, 1, best)[:, 0],
            torch.gather(vx, 1, best)[:, 0],
            torch.gather(vy, 1, best)[:, 0],
        ],
        dim=1,
    )
