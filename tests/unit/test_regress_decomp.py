"""Spec 038: the decomposition's readings (regress.decomp)."""

from __future__ import annotations

import math

import numpy as np

from tma2.regress import decomp as dc


def _errs(n: int = 200, rows: int = 3) -> tuple[dict[str, np.ndarray], np.ndarray]:
    rng = np.random.default_rng(3)
    ordinal = np.repeat(np.arange(n), rows)
    base = np.exp(rng.normal(0.0, 0.3, (n * rows, 3)))
    errs = {
        "c": base * 2.0,
        "h": base * math.sqrt(2.0),  # closes half the log gap to ft
        "ft1": base * np.exp(rng.normal(0.0, 0.05, base.shape)),
        "ft2": base * np.exp(rng.normal(0.0, 0.05, base.shape)),
        "own": base * 4.0,
    }
    return errs, ordinal


def test_share_recovers_half() -> None:
    errs, ordinal = _errs()
    names = {"comparator": "c", "regressors": ["ft1", "ft2"], "hardened": ["h"], "own": "own"}
    out = dc.comparisons(errs, names, ordinal, resamples=300)
    g = out["gap_closed"]["range"]["h"]
    assert g["defined"] and abs(g["share"] - 0.5) < 0.03 and g["lo"] < 0.5 < g["hi"]
    assert abs(out["ratios"]["range"]["fine_tuned"]["ratio"] - 2.0) < 0.05
    p = out["prior_share"]["range"]["own"]
    assert abs(p["share"] + 1.0) < 0.06 and p["outcome"] == "little"
    assert abs(out["versus"]["range"]["h"]["ratio"] - math.sqrt(2.0)) < 0.05


def test_share_undefined_without_a_gain() -> None:
    num = {i: 0.1 for i in range(50)}
    den = {i: (-1.0) ** i * 0.5 for i in range(50)}
    assert dc.share(num, den, 200)["defined"] is False
    assert dc.share({}, {}, 10) == {"scenarios": 0, "defined": False}


def test_since_last_change_and_bands() -> None:
    ms = [{"start_index": 10, "end_index": 20}, {"start_index": 50, "end_index": 60}]
    assert dc.since_last_change(ms, 5, 10.0) == math.inf
    assert dc.since_last_change(ms, 15, 10.0) == 0.0
    assert dc.since_last_change(ms, 45, 10.0) == 250.0
    assert dc.since_last_change(ms, 70, 10.0) == 100.0
    assert [dc.since_band(s) for s in (0.0, 299.0, 300.0, 899.0, 900.0, math.inf)] == [
        0,
        0,
        1,
        1,
        2,
        2,
    ]


def test_structure_right() -> None:
    ms = [{"start_index": 100, "end_index": 110}, {"start_index": 195, "end_index": 205}]
    # at k = 200 the second change began 50 s ago: not required, but a declaration of it is fine
    assert dc.structure_right([(98, 112)], ms, 200, 10.0)
    assert dc.structure_right([(98, 112), (196, 200)], ms, 200, 10.0)
    assert not dc.structure_right([], ms, 200, 10.0)  # a miss
    assert not dc.structure_right([(98, 112), (40, 50)], ms, 200, 10.0)  # a false transition
    assert dc.structure_right([(118, 121)], ms, 200, 10.0)  # within 120 s
    assert not dc.structure_right([(130, 140)], ms, 200, 10.0)


def test_common_rows() -> None:
    errs, _ = _errs(4, 2)
    errs["h"][3, 1] = np.inf
    rows = dc.common_rows(errs, ["c", "h"])
    assert rows.sum() == 7 and not rows[3]
