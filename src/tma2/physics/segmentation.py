"""Inputs for the physics layer from known information: trivial (batch least squares) and
oracle (truth manoeuvre spans). A learned segmenter (Annex A) will produce the same arrays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

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
