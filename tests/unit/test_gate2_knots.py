"""Gate 2's physics layer keeps up to 12 knots (spec 007 research R5, task T002)."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch

from tma2.cli.oracle import inputs_for
from tma2.gate2 import KNOTS
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import BearingData
from tma2.segment.inputs import segmentation_inputs


def _scenario(n: int = 400) -> BearingData:
    t = np.arange(n) * 10.0
    ox = 3.0 * t
    oy = np.where(t < 2000, 0.0, 5.0 * (t - 2000))
    tx, ty = 8000.0 + 2.0 * t, 6000.0 - 1.0 * t
    z = np.arctan2(tx - ox, ty - oy)
    return BearingData(
        t=t, ox=ox, oy=oy, z=z, valid=np.ones(n, dtype=np.uint8), zig_index=200, sigma=0.01, index=0
    )


def _run(d: BearingData, k: int, trs: list[tuple[int, int]], knots: int) -> Any:
    torch.set_default_dtype(torch.float64)
    inp = segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, trs, "gap", True)
    assert inp is not None
    with torch.no_grad():
        return PhysicsLayer(knots=knots)(inputs_for([(d, k, inp)], d.n))


def test_knot_cap_is_12() -> None:
    assert KNOTS == 12


def test_ten_knots_are_all_active() -> None:
    """Five transitions (ten knots): all ten are used at cap 12; cap 8 drops two."""
    d = _scenario()
    trs = [(40, 50), (90, 100), (150, 160), (230, 240), (300, 310)]
    want = {r for tr in trs for r in tr}
    k = 390
    used12 = set(_run(d, k, trs, KNOTS).knots[0].tolist())
    used8 = set(_run(d, k, trs, 8).knots[0].tolist())
    assert want <= used12
    assert len(want & used8) == 8


def test_eight_knots_agree_between_caps() -> None:
    d = _scenario()
    trs = [(40, 50), (90, 100), (150, 160), (230, 240)]
    k = 390
    a, b = _run(d, k, trs, KNOTS).state[0].numpy(), _run(d, k, trs, 8).state[0].numpy()
    np.testing.assert_allclose(a, b, rtol=1e-9, atol=1e-6)
