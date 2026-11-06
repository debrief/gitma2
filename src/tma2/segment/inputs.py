"""A segmentation handed to the physics layer (spec 005 FR-030).

A transition interval [s, e] (inclusive rows, as truth labels make them from a span's
[start_index, end_index]) becomes a knot at s and a knot at e, the oracle's convention.
* **gap**: the bearings inside the transition (rows s … e − 1, as ``oracle_inputs``'s
  ``mask_turns``) get zero weight;
* **chord**: the bearings are kept, and with ``speed_prior`` the speed-continuity weight sits on
  the end knot and skips the start knot's increment for each course-only transition.

**An open transition at k** (the prefix ends inside it, [s, k]) is handed over by
``open_handover``:
* ``knot_at_k`` (spec 005, the default): as any transition, knots at s and at k; in gap mode
  rows s … k − 1 get zero weight; the speed prior at k;
* ``start_masked``: a knot at s only; rows s … k get zero weight (``oracle_inputs``'s
  ``mask_turns`` for a span in progress);
* ``start_chord``: a knot at s only; the bearings kept (``oracle_inputs``'s default for a span in
  progress).

A segmenter does not report kinds, so ``course_only`` defaults to every transition (the prior is
applied across each, as note 08's GLR + confirm did); the truth segmentation passes the spans'
kinds, which makes the result equal to ``oracle_inputs``. The estimate always comes from the
physics layer (constitution III).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from tma2.physics.segmentation import MASKED_LOG_WEIGHT, LayerInputs, trivial_inputs
from tma2.types.generated.tma import SegmentMode


def handover_of(p: object) -> str | None:
    """A ``SegmentParameters``' open-transition hand-over as a plain string (None: the default)."""
    ho = getattr(p, "open_handover", None)
    return None if ho is None else str(getattr(ho, "value", ho))


def segmentation_inputs(
    t: np.ndarray,
    ox: np.ndarray,
    oy: np.ndarray,
    z: np.ndarray,
    valid: np.ndarray,
    k: int,
    transitions: Sequence[tuple[int, int]],
    mode: SegmentMode | str,
    speed_prior: bool = True,
    course_only: Sequence[bool] | None = None,
    open_last: bool = False,
    open_handover: str | None = None,
) -> LayerInputs | None:
    """Physics-layer inputs on [0, k] for the given transitions; None without a valid bearing."""
    base = trivial_inputs(t, ox, oy, z, valid, k)
    if base is None:
        return None
    mode = SegmentMode(mode)
    n = t.shape[0]
    cp = np.zeros(n)
    sw = np.zeros(n)
    sk = np.zeros(n)
    lw = np.zeros(n)
    handover = open_handover or "knot_at_k"
    if handover not in ("knot_at_k", "start_masked", "start_chord"):
        raise ValueError(f"unknown open-transition hand-over {handover!r}")
    for i, (a, b) in enumerate(transitions):
        if open_last and i == len(transitions) - 1 and b == k and handover != "knot_at_k":
            if 0 < a <= k:
                cp[a] = 1.0
            if handover == "start_masked":
                lw[a : k + 1] = MASKED_LOG_WEIGHT
            continue
        for r in (a, b):
            if 0 < r <= k:
                cp[r] = 1.0
        if mode == SegmentMode.gap:
            lw[a : min(b, k + 1)] = MASKED_LOG_WEIGHT
        co = True if course_only is None else bool(course_only[i])
        if speed_prior and co and 0 < a <= k and b <= k:
            sw[b] = 1.0
            sk[b] = 1.0
    return LayerInputs(cp, sw, lw, base.theta0, sk)
