"""Nominate-then-confirm with turn windows (tma2.detect.confirm; docs/research/08 §6)."""

from __future__ import annotations

import math

import numpy as np

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.detect.confirm import Accepted, knot_inputs, knots_at, tau_4dof, window_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays

D = fixture_dir("phase4-seed777")


def _scenario() -> BearingData:
    _, meta, own, _tgt, obs = next(iter(iter_pack_raw(D / "test.f32pack")))
    return bearing_data_from_arrays(meta, own, obs)


def test_tau_4dof_matches_tail_probability() -> None:
    for tau in (6.0, 9.21, 13.8, 20.0):
        x = tau_4dof(tau)
        assert math.isclose(math.exp(-x / 2) * (1 + x / 2), math.exp(-tau / 2), rel_tol=1e-12)
    assert abs(tau_4dof(13.8155) - 18.4668) < 1e-3  # the 0.1% points


def test_knots_at_uses_window_end_once_passed() -> None:
    acc = [Accepted(alarm=50, alarm_end=55, row=40, cost_drop=30.0, end=58)]
    assert knots_at(acc, 49) == []
    assert knots_at(acc, 50) == [40]
    assert knots_at(acc, 58) == [40, 58]
    point = [Accepted(alarm=50, alarm_end=55, row=40, cost_drop=30.0)]
    assert knots_at(point, 80) == [40]


def test_window_inputs() -> None:
    d = _scenario()
    k = d.n - 1
    point = [Accepted(50, 55, 40, 30.0)]
    a = window_inputs(d, k, point, True)
    b = knot_inputs(d, k, [40], True)
    assert a is not None and b is not None
    for x, y in ((a.changepoint, b.changepoint), (a.speed_weight, b.speed_weight)):
        np.testing.assert_array_equal(x, y)
    win = [Accepted(50, 55, 40, 30.0, end=58)]
    open_ = window_inputs(d, 55, win, True)
    assert open_ is not None
    assert np.flatnonzero(open_.changepoint).tolist() == [40]
    assert np.flatnonzero(open_.speed_weight).tolist() == [40]
    closed = window_inputs(d, k, win, True)
    assert closed is not None
    assert np.flatnonzero(closed.changepoint).tolist() == [40, 58]
    # the speed prior sits on the end knot and skips the start knot's increment (the chord)
    assert np.flatnonzero(closed.speed_weight).tolist() == [58]
    assert closed.speed_skip is not None
    assert np.flatnonzero(closed.speed_skip).tolist() == [58]
    no_prior = window_inputs(d, k, win, False)
    assert no_prior is not None and not no_prior.speed_weight.any()
