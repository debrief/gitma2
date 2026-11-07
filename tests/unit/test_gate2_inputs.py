"""Gate 2's per-prefix inputs (spec 007 T006)."""

from __future__ import annotations

import numpy as np

from tma2.gate2.inputs import code_channel, prefix_inputs
from tma2.references.classical import BearingData
from tma2.segment import STEADY, TRANSITION, UNKNOWN, Interval
from tma2.segment.inputs import segmentation_inputs


def _d(n: int = 120) -> BearingData:
    t = np.arange(n) * 10.0
    return BearingData(
        t=t,
        ox=t * 0.0,
        oy=t * 3.0,
        z=np.linspace(0.2, 0.6, n),
        valid=np.ones(n, dtype=np.uint8),
        zig_index=40,
        sigma=0.01,
        index=0,
    )


def test_prefix_inputs_are_cs_hand_over() -> None:
    d = _d()
    ivs = [
        Interval(STEADY, 0, 49),
        Interval(TRANSITION, 50, 60),
        Interval(STEADY, 61, 99),
        Interval(TRANSITION, 100, 110, True),
    ]
    for ho in (None, "start_masked", "start_chord"):
        a = prefix_inputs(d, 110, ivs, "gap", ho)
        b = segmentation_inputs(
            d.t, d.ox, d.oy, d.z, d.valid, 110, [(50, 60), (100, 110)], "gap", True, None, True, ho
        )
        assert a is not None and b is not None
        for f in ("changepoint", "speed_weight", "log_weight", "theta0"):
            np.testing.assert_array_equal(getattr(a, f), getattr(b, f))


def test_code_channel_is_causal() -> None:
    ivs = [Interval(STEADY, 0, 49), Interval(TRANSITION, 50, 60), Interval(UNKNOWN, 61, 70)]
    ch = code_channel(ivs, 70, 120)
    assert (ch[:50] == 0).all() and (ch[50:61] == 1).all() and (ch[61:71] == 0.5).all()
    assert (ch[71:] == 0).all()
