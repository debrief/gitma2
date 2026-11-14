"""Spec 017: detectability bands, the gap split and its verdict."""

from __future__ import annotations

import math

import numpy as np

from tma2.timelate.study5 import detect_table, found_flags, gap_split, verdict


def test_found_flags_pair_each_true_manoeuvre_once() -> None:
    true = [[100.0, 200.0], [1000.0, 1100.0], [2000.0, 2100.0]]
    found = [[130.0, 210.0], [1900.0, 2050.0]]
    assert found_flags(true, found, 120.0) == [True, False, True]
    assert found_flags(true, [], 120.0) == [False, False, False]
    # one found manoeuvre cannot serve two true ones
    assert found_flags([[0.0, 100.0], [100.0, 200.0]], [[60.0, 140.0]], 120.0).count(True) == 1


def test_missed_share_by_detectability_band_ignores_cut_manoeuvres() -> None:
    periods = [
        {
            "true": [[100.0, 200.0], [1000.0, 1100.0], [1800.0, 1900.0]],
            "true_cut": [False, False, True],
            "detectability": [3.0, 150.0, 1.0],
            "histories": {"ctl": {"spans": [[1010.0, 1090.0]]}},
        },
        {
            "true": [[500.0, 600.0]],
            "true_cut": [False],
            "detectability": [30.0],
            "histories": {"ctl": {"spans": []}},
        },
    ]
    t = detect_table(periods, ["ctl"], [10.0, 20.0, 40.0], 120.0)
    assert t["manoeuvres"] == 3  # the cut one is not counted
    assert t["share_below"]["10"]["rate"] == 1 / 3 and t["share_below"]["40"]["rate"] == 2 / 3
    assert t["missed_by_band"]["0-5"]["ctl"]["rate"] == 1.0
    assert t["missed_by_band"]["20-40"]["ctl"]["rate"] == 1.0
    assert t["missed_by_band"]["100+"]["ctl"]["rate"] == 0.0
    assert t["missed_by_band"]["5-10"]["ctl"] is None


def test_the_gap_splits_into_an_attainable_share() -> None:
    n = 40
    full = np.full(n, 0.02)
    med = {"ctl": np.full(n, 0.08), "ref-full": full, "ref-d20": np.full(n, 0.04)}
    s = gap_split(med, "ctl", "ref-full", [20.0])["20"]
    assert math.isclose(s["share"], 0.5, rel_tol=1e-9)  # log 2 of log 4
    med["ref-d20"] = full.copy()  # nothing undetectable: the whole gap is attainable
    assert math.isclose(gap_split(med, "ctl", "ref-full", [20.0])["20"]["share"], 1.0)
    med["ref-d20"] = med["ctl"].copy()  # the control is at the detectable-only reference
    assert math.isclose(
        gap_split(med, "ctl", "ref-full", [20.0])["20"]["share"], 0.0, abs_tol=1e-12
    )
    assert gap_split(med, "ctl", "ref-full", [10.0]) == {}


def test_the_verdict_needs_an_interval_wholly_one_side_of_a_half() -> None:
    assert verdict({"share": 0.2, "lo": 0.1, "hi": 0.4}) == "mostly identifiability"
    assert verdict({"share": 0.8, "lo": 0.6, "hi": 0.9}) == "mostly attainable"
    assert verdict({"share": 0.45, "lo": 0.3, "hi": 0.6}) == "mixed"
    assert verdict(None) == "absent"
