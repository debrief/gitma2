"""Spec 015: prior version 3 pairs every open factor's density with its volume; one rule for
a history's identity; earlier registrations unchanged."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from tma2.timelate.prior import ManoeuvrePrior, _leg_sf, _leg_tail, log_prior, open_precision

RANGES = json.loads(Path("configs/timelate/tl-ranges.json").read_text())
T_END = 2400.0


def _total(p: ManoeuvrePrior, theta: np.ndarray, spans: np.ndarray, kinds: np.ndarray) -> float:
    return float(sum(log_prior(p, theta, spans, kinds, T_END, 9000.0).values()))


@pytest.mark.parametrize(
    ("kind", "what"),
    [
        ((True, False), "speed"),
        ((True, False), "turn"),
        ((True, False), "duration"),
        ((False, True), "dv"),
        ((False, True), "duration"),
        ((True, True), "duration"),
    ],
)
def test_density_times_volume_is_one_for_each_open_factor(
    kind: tuple[bool, bool], what: str
) -> None:
    """∫ prior dθ along one parameter equals the prior at the point × the volume the evidence
    allows there: what a direction the bearings leave wholly open must contribute."""
    p = ManoeuvrePrior.from_ranges(RANGES, version=3)
    kinds = np.array([kind])
    theta = np.array([0.0, 9000.0, 1.0, 5.0, 0.9 if kind[0] else 0.0, 1.6 if kind[1] else 0.0])
    spans = np.array([[900.0, 960.0]])
    prec = open_precision(p, theta, spans, kinds, 9000.0, T_END)
    index = {"speed": 3, "turn": 4, "dv": 5, "duration": 7}[what]
    volume = math.sqrt(2.0 * math.pi / prec[index])

    def at(x: float) -> float:
        th, sp = theta.copy(), spans.copy()
        if what == "duration":
            sp[0, 1] = sp[0, 0] + x
        else:
            th[index] = x
        return math.exp(_total(p, th, sp, kinds))

    grid = {
        "speed": np.linspace(0.2, 16.0, 8001),
        "turn": np.linspace(0.05, 3.0, 8001),
        "dv": np.linspace(0.05, 8.0, 8001),
        "duration": np.linspace(2.0, 1200.0, 40001),
    }[what]
    if what == "speed" and kind[1]:
        return
    integral = float(np.sum([at(float(x)) for x in grid]) * (grid[1] - grid[0]))
    here = at(float(spans[0, 1] - spans[0, 0]) if what == "duration" else float(theta[index]))
    side = 0.5 if what in ("turn", "dv") else 1.0  # one sign's branch of a signed change
    assert integral == pytest.approx(here * volume * side, rel=0.03)


def test_version_3_duration_volume_is_the_priors_not_600_seconds() -> None:
    p3 = ManoeuvrePrior.from_ranges(RANGES, version=3)
    kinds = np.array([[False, True]])
    theta = np.array([0.0, 9000.0, 1.0, 5.0, 0.0, 1.1])
    spans = np.array([[900.0, 925.0]])
    v3 = math.sqrt(2 * math.pi / open_precision(p3, theta, spans, kinds, 9000.0, T_END)[7])
    assert 5.0 < v3 < 200.0
    from tma2.timelate.prior import prior_precision

    v2 = math.sqrt(
        2 * math.pi / prior_precision(ManoeuvrePrior.from_ranges(RANGES, version=2), 1, 9000.0)[7]
    )
    assert v2 > 3 * v3


def test_version_3_leg_survival_is_of_the_renormalised_density() -> None:
    p3 = ManoeuvrePrior.from_ranges(RANGES, version=3)
    assert _leg_sf(p3, p3.leg_min) == pytest.approx(1.0)
    assert _leg_sf(p3, p3.leg_min - 1.0) == 1.0
    p2 = ManoeuvrePrior.from_ranges(RANGES, version=2)
    assert _leg_sf(p2, p2.leg_min) < 1.0
    assert _leg_tail(p3, 0.0) > _leg_tail(p2, 0.0)
    first = open_precision(
        p3,
        np.array([0.0, 9000.0, 1.0, 5.0, 0.9, 0.0]),
        np.array([[900.0, 960.0]]),
        np.array([[True, False]]),
        9000.0,
        T_END,
    )[6]
    assert first == pytest.approx(2 * math.pi * (_leg_sf(p3, 900.0) / _leg_tail(p3, 0.0)) ** 2)


def test_same_history_ignores_cut_manoeuvres() -> None:
    from tma2.timelate.match import same_history, strip_cut

    true = [[0.0, 20.0], [900.0, 960.0], [2380.0, 2400.0]]
    cut = [True, False, True]
    assert same_history(true, [[910.0, 950.0]], 120.0, cut)
    assert not same_history(true, [[910.0, 950.0]], 120.0, None)
    # a found manoeuvre that pairs with a cut one is not counted against the system
    assert same_history(true, [[5.0, 60.0], [905.0, 955.0]], 120.0, cut)
    # ... but only one per cut manoeuvre, and only within the tolerance
    assert not same_history(true, [[5.0, 60.0], [40.0, 90.0], [905.0, 955.0]], 120.0, cut)
    assert not same_history(true, [[400.0, 460.0], [905.0, 955.0]], 120.0, cut)
    assert not same_history(true, [], 120.0, cut)
    assert same_history([[0.0, 20.0]], [], 120.0, [True])
    assert same_history([], [], 120.0, [])
    assert not same_history(true, [[1200.0, 1260.0]], 120.0, cut)
    a, b = strip_cut(true, [[5.0, 60.0], [905.0, 955.0]], 120.0, cut)
    assert a.tolist() == [930.0] and b.tolist() == [930.0]
    with pytest.raises(ValueError):
        same_history(true, [], 120.0, [True])


def test_cut_flags_follow_the_engagements_table() -> None:
    from tma2.timelate.match import cut_flags
    from tma2.timelate.periods import Period

    z = np.zeros((1, 5))
    meta = {
        "manoeuvres": [
            {"kind": "course", "start_index": 90, "end_index": 104},  # began before
            {"kind": "course", "start_index": 200, "end_index": 212},  # whole
            {"kind": "speed", "start_index": 290, "end_index": 299},  # ends on the last row: whole
            {"kind": "course", "start_index": 299, "end_index": 310},  # no row inside: not listed
            {"kind": "course", "start_index": 20, "end_index": 30},  # outside
        ]
    }
    p = Period(0, meta, z, z, z, 100, 200, 5.0)
    assert p.last == 299
    assert cut_flags(p) == [True, False, False]
    q = Period(
        0,
        {"manoeuvres": [{"kind": "both", "start_index": 290, "end_index": 305}]},
        z,
        z,
        z,
        100,
        200,
        5.0,
    )
    assert cut_flags(q) == [True]
