"""Per-prefix physics-layer inputs for Gate 2's model E (spec 007 T006).

E-w acts on C's segmentation: the hand-over of ``segment.inputs`` (knots, masked transition
bearings, the speed prior, the open-transition convention fixed in the decision record) is the
base, and E's learned per-bearing log-weights are added to its log-weights in the model. With
zero learned weights the inputs are C's exactly, so an untrained E is C (FR-022).

C's code channel: for a prefix k, rows 0 … k carry C's segmentation of [0, k] (steady 0,
transition 1, unknown ½) and rows after k carry 0. It is built from the segmentation at k alone,
so it is causal (FR-023); E runs its encoder once per scored prefix.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData
from tma2.segment import STEADY, TRANSITION, UNKNOWN, Interval, to_codes
from tma2.segment.inputs import segmentation_inputs

CODE_VALUE = {STEADY: 0.0, TRANSITION: 1.0, UNKNOWN: 0.5}


def prefix_inputs(
    d: BearingData,
    k: int,
    intervals: Sequence[Interval],
    mode: str,
    open_handover: str | None,
) -> LayerInputs | None:
    """C's hand-over of its segmentation of [0, k] (None without a valid bearing)."""
    trs = [(iv.start, iv.end) for iv in intervals if iv.kind == TRANSITION]
    last = intervals[-1] if intervals else None
    open_last = last is not None and last.kind == TRANSITION and bool(last.open)
    return segmentation_inputs(
        d.t, d.ox, d.oy, d.z, d.valid, k, trs, mode, True, None, open_last, open_handover
    )


def code_channel(intervals: Sequence[Interval], k: int, n: int) -> np.ndarray:
    """[n] C's per-row code at prefix k, as values for the encoder; 0 after k."""
    out = np.zeros(n)
    codes = to_codes(list(intervals), k + 1)
    for code, val in CODE_VALUE.items():
        out[: k + 1][codes == code] = val
    return out
