"""Spec 018: the rate posterior, the mixture's spread and the study's readings."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tma2.timelate.adapt import log_sum, rate_grid, rate_posterior
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.study6 import (
    any_false,
    control_misses,
    coverage,
    kinds_of_period,
    medians3,
    one_called_quiet,
    pair3,
)

ROOT = Path(__file__).resolve().parents[2]


def test_rate_grid_changes_only_the_leg_length() -> None:
    base = ManoeuvrePrior.from_ranges(
        json.loads((ROOT / "configs/timelate/tl-broad.json").read_text()), 3
    )
    grid = rate_grid(base, [600.0, 2400.0], 0.5)
    assert sorted(grid) == ["rate2400", "rate600"]
    assert grid["rate600"].leg_mean == 600.0 and grid["rate600"].leg_sd == 300.0
    assert grid["rate2400"].angle == base.angle and grid["rate2400"].leg_min == base.leg_min
    assert grid["rate2400"].version == 3


def test_rate_posterior_weighs_evidence_and_prior_weight() -> None:
    ev = {"a": np.array([0.0, -50.0]), "b": np.array([math.log(3.0)])}
    post = rate_posterior(ev, {"a": 0.0, "b": 0.0})
    assert math.isclose(post["b"], 0.75, rel_tol=1e-9) and math.isclose(sum(post.values()), 1.0)
    post = rate_posterior(ev, {"a": math.log(3.0), "b": 0.0})  # a weight of 3 evens it
    assert math.isclose(post["a"], 0.5, rel_tol=1e-9)
    # a rate whose search found nothing has no probability; nothing found anywhere: even
    assert rate_posterior({"a": np.array([1.0]), "b": np.array([])}, {"a": 0.0, "b": 0.0})["b"] == 0
    assert rate_posterior({"a": np.array([]), "b": np.array([-np.inf])}, {"a": 0.0, "b": 0.0}) == {
        "a": 0.5,
        "b": 0.5,
    }
    assert log_sum(np.array([])) == -math.inf


def _arrays(n: int = 12, rows: int = 4) -> dict[str, np.ndarray]:
    period = np.repeat(np.arange(n), rows)
    bound = np.column_stack([np.repeat(np.linspace(0.01, 0.12, n), rows)] * 3)

    def err(level: float) -> np.ndarray:
        return np.full((n * rows, 4), level, dtype=np.float32)

    good = err(0.02)
    good[period >= 6] = 0.08  # the adaptive control wins only in the first six periods
    return {
        "period": period,
        "bound": bound.astype(np.float32),
        "true_range": np.full(n * rows, 10_000.0, dtype=np.float32),
        "err_ctl": err(0.08),
        "err_ada": good,
        "err_true": err(0.02),
    }


def test_paired_ratios_in_three_quantities_carry_their_period_counts() -> None:
    arr = _arrays()
    ids, med, bound = medians3(arr)
    assert ids.size == 12 and med["ctl"].shape == (12, 3) and bound[0] < bound[-1]
    c = pair3(med, "ctl", "ada")
    assert c is not None and set(c) == {"range", "course", "speed"}
    assert c["range"]["periods"] == 12
    assert math.isclose(c["range"]["geometric_mean"], 2.0, rel_tol=1e-6)  # sqrt(4 × 1)
    assert math.isclose(c["range"]["median_ratio"], 2.0, rel_tol=1e-6)
    keep = ids < 6
    assert math.isclose(
        pair3(med, "ctl", "ada", keep)["range"]["geometric_mean"], 4.0, rel_tol=1e-6
    )  # type: ignore[index]
    assert pair3(med, "ctl", "absent") is None
    assert pair3(med, "ctl", "ada", ids < 3) is None  # too few periods to quote


def _period(
    ordinal: int, true: list[list[float]], det: list[float], spans: list[list[float]]
) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "true": true,
        "true_cut": [False] * len(true),
        "detectability": det,
        "histories": {"ctl": {"spans": spans}},
    }


def test_kind_of_period_reads_detectable_misses_only() -> None:
    periods = [
        _period(0, [[100.0, 200.0]], [5.0], []),  # missed, but the bearings barely show it
        _period(1, [[100.0, 200.0]], [50.0], []),  # missed and detectable
        _period(2, [[100.0, 200.0]], [50.0], [[120.0, 190.0]]),  # found
        _period(3, [], [], [[500.0, 600.0]]),  # quiet target, a false manoeuvre
    ]
    miss = control_misses(periods, "ctl", 20.0, 120.0)
    assert miss == {0: False, 1: True, 2: False, 3: False}
    ids = np.arange(5)
    kinds = kinds_of_period(ids, np.array([0.01, 0.02, 0.03, 0.2, np.nan]), miss)
    assert kinds["control_misses"].tolist() == [False, True, False, False, False]
    assert kinds["control_finds_all"].tolist() == [True, False, True, True, False]  # 4: unknown
    assert (
        int(kinds["bound_tight"].sum() + kinds["bound_middle"].sum() + kinds["bound_loose"].sum())
        == 4
    )
    assert one_called_quiet(periods, "ctl")["rate"] == 2 / 3  # type: ignore[index]
    assert any_false(periods, "ctl", 120.0)["rate"] == 0.25  # type: ignore[index]


def test_coverage_counts_rows_within_the_stated_spread() -> None:
    arr = _arrays(n=4, rows=5)
    n = arr["period"].size
    arr["hrange_h"] = np.full(n, 10_000.0, dtype=np.float32)
    arr["hrange_h"][:5] = 10_300.0  # period 0: off by 300 m
    arr["hrange_h"][5:10] = 10_150.0  # period 1: off by 150 m
    arr["spread_h"] = np.full(n, 100.0, dtype=np.float32)
    arr["spread_h"][15:] = 0.0  # period 3 states no spread: left out
    periods = [{"ordinal": i, "true": [], "true_cut": []} for i in range(4)]
    periods[1]["true"], periods[1]["true_cut"] = [[1.0, 2.0]], [False]
    c = coverage(arr, periods, "h", [1.0, 2.0])
    assert c["rows_with_a_spread"] == 15 and c["rows_determined"] == 20
    assert math.isclose(c["all"]["within_1sd"], 1 / 3) and math.isclose(
        c["all"]["within_2sd"], 2 / 3
    )
    assert c["1"]["rows"] == 5 and c["1"]["within_2sd"] == 1.0 and c["1"]["within_1sd"] == 0.0
    assert c["0"]["periods"] == 2 and c["2+"]["rows"] == 0
    assert coverage(arr, periods, "absent", [1.0]) == {}
