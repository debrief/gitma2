"""Spec 039 part 3: the time-late control cut at a scored row reads nothing after the row."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from tma2.headroom.cut import cut_state
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment.score import g5_rows, iter_selected


def test_cut_state_is_causal_and_finite(man2_pack: Path) -> None:
    for _j, m, own, _tgt, obs in iter_selected(man2_pack, 0, 4):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if ks:
            break
    k = ks[0]
    a = cut_state(d, k)
    assert a is not None
    state, (rng, course, speed), declared = a
    assert np.isfinite(state).all() and rng > 0 and 0 <= course < 2 * np.pi and speed > 0
    assert declared >= 0
    z = d.z.copy()
    z[k + 1 :] += 0.3  # nothing after the row may matter
    b = cut_state(replace(d, z=z), k)
    assert b is not None and np.array_equal(b[0], state)
