"""From the detector's soft segmentation to the physics layer's inputs, and the exported knots
(spec 004 FR-014; research R4).

For a scored row k (the detector's query row):

* changepoint = ``w_change[k, :]`` (the layer keeps the ``knots`` largest weights ≤ k, as P0);
* speed-continuity weight and its skip at a knot j = ``p_kind[k, j]``: a course change ties the
  speed after the knot to the speed before the previous knot (R4 measured this on every course
  knot, start and end alike, at 0.442 of batch least squares against the oracle's 0.435);
* per-bearing log-weights 0 (trivial) and gitma's grid start (``grid_start_tensor``).

The exported segmentation is the local maxima of ``w_change[k, :]`` at or above the decision
record's threshold (default 0.5; a plateau counts once, at its first row), the ``max_knots``
largest kept, each with its kind (``p_kind ≥ 0.5``: course change).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from tma2.physics.layer import PhysicsInputs
from tma2.physics.segmentation import grid_start_tensor

KNOT_THRESHOLD = 0.5
MAX_KNOTS = 8


def physics_inputs(
    w_change: Tensor,
    p_kind: Tensor,
    bearing: Tensor,
    valid: Tensor,
    own_xy: Tensor,
    t: Tensor,
    sigma: Tensor,
    k: Tensor,
    k_state: Tensor | None = None,
    theta0: Tensor | None = None,
) -> PhysicsInputs:
    """One question per scenario: w_change, p_kind [B, R] (row k's), the scenario's bearings,
    valid (0/1), ownship [B, R, 2], t [B, R], σ [B], k [B] → the layer's inputs. ``theta0``, the
    grid start, is computed in tensors when absent (the exported graph); training passes the
    numba one (``lsq.grid_start``, the same candidates; no gradient reaches it)."""
    if theta0 is None:
        theta0 = grid_start_tensor(t, own_xy[..., 0], own_xy[..., 1], bearing, valid, k)
    return PhysicsInputs(
        bearing=bearing,
        valid=valid,
        own=own_xy,
        t=t,
        sigma=sigma,
        k=k,
        changepoint=w_change,
        speed_weight=p_kind,
        log_weight=torch.zeros_like(t),
        theta0=theta0,
        speed_skip=p_kind,
        k_state=k_state,
    )


@dataclass
class Knot:
    row: int
    weight: float
    p_kind: float

    @property
    def kind(self) -> str:
        return "course" if self.p_kind >= 0.5 else "speed"


def export_knots(
    w_row: np.ndarray,
    p_kind_row: np.ndarray,
    k: int,
    threshold: float = KNOT_THRESHOLD,
    max_knots: int = MAX_KNOTS,
) -> list[Knot]:
    """Local maxima of w_row[1 … k] at or above ``threshold``, the ``max_knots`` largest (ties:
    earlier row), returned in row order."""
    w = np.asarray(w_row[: k + 1], dtype=np.float64)
    peaks: list[int] = []
    j = 1
    while j <= k:
        if w[j] < threshold:
            j += 1
            continue
        end = j
        while end + 1 <= k and w[end + 1] == w[j]:
            end += 1
        left = w[j - 1] if j - 1 >= 1 else -np.inf
        right = w[end + 1] if end + 1 <= k else -np.inf
        if w[j] > left and w[j] > right:
            peaks.append(j)
        j = end + 1
    peaks.sort(key=lambda r: (-w[r], r))
    return sorted(
        (Knot(r, float(w[r]), float(p_kind_row[r])) for r in peaks[:max_knots]),
        key=lambda x: x.row,
    )


def knot_arrays(knots: list[Knot], rows: int) -> tuple[np.ndarray, np.ndarray]:
    """Hard (changepoint, p_kind) arrays [rows] from exported knots: weight 1 at each knot and its
    kind as 1 (course) or 0 (speed): the downstream solve of Gate D (FR-027)."""
    cp = np.zeros(rows)
    kind = np.zeros(rows)
    for kn in knots:
        cp[kn.row] = 1.0
        kind[kn.row] = 1.0 if kn.kind == "course" else 0.0
    return cp, kind
