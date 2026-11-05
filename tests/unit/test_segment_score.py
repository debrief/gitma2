"""Spec 005 T017–T018: scoring helpers (gap recovered, prefix metrics, clustered bootstrap)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from tma2.detect.confirm import Accepted
from tma2.eval.bootstrap import bootstrap_clustered_statistic
from tma2.segment import default_parameters
from tma2.segment.score import gap_recovered_cols, glr_confirm_intervals, prefix_metrics


def _meta(spans: list[tuple[int, int]], zig: int = 60, n: int = 400) -> dict[str, Any]:
    return {
        "samples": n,
        "turn_start_index": zig - 10,
        "zig_index": zig,
        "manoeuvres": [{"start_index": a, "end_index": b, "kind": "course"} for a, b in spans],
    }


def test_gap_recovered_cols() -> None:
    one = np.array([[10.0, 1, 1]] * 5)
    ora = np.array([[2.0, 1, 1]] * 5)
    seg = np.array([[6.0, 1, 1]] * 5)
    cols = {"one_leg": one, "oracle": ora, "C": seg}
    assert gap_recovered_cols(cols, "C", 0) == pytest.approx(0.5)
    assert gap_recovered_cols({**cols, "C": ora}, "C", 0) == pytest.approx(1.0)


def test_prefix_metrics() -> None:
    p = default_parameters()
    m = _meta([(150, 165)])
    perfect = prefix_metrics([(150, 165)], m, 300, p)
    assert perfect.contamination == 0.0 and perfect.coverage == 1.0
    assert perfect.hits60 == [True] and perfect.leg_count_ok and perfect.false_split is None
    missed = prefix_metrics([], m, 300, p)
    assert missed.contamination > 0 and missed.hits60 == [False] and missed.leg_count_ok is False
    nochange = prefix_metrics([(200, 210)], _meta([]), 300, p)
    assert nochange.false_split is True
    # a change after k is not counted
    early = prefix_metrics([], m, 140, p)
    assert early.changes == 0 and early.false_split is False


def test_glr_confirm_intervals() -> None:
    acc = [
        Accepted(100, 105, 95, 30.0),
        Accepted(200, 210, 190, 25.0, 205),
        Accepted(300, 300, 290, 20.0),
    ]
    assert glr_confirm_intervals(acc, 250, 6) == [(95, 100), (190, 205)]


def test_bootstrap_clustered_statistic_deterministic() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=60)
    cl = np.repeat(np.arange(20), 3)
    a = bootstrap_clustered_statistic({"x": x}, cl, lambda c: float(np.median(c["x"])), 0.95, 500)
    b = bootstrap_clustered_statistic({"x": x}, cl, lambda c: float(np.median(c["x"])), 0.95, 500)
    assert (a.lo, a.hi) == (b.lo, b.hi) and a.lo <= a.value <= a.hi and a.clusters == 20


# --- reporting beside the gate (Gate S panel rounds 1 and 2) ---------------------------------


def test_efficiency_of() -> None:
    """median(|e| / σ) / 0.6745 with the lower median; rows without a bound are ignored and a
    failed row (+inf) counts above any finite value."""
    from tma2.segment.score import efficiency_of

    sd = np.array([1.0, 2.0, np.nan, 1.0])
    e = np.array([0.6744897501960817, 2 * 0.6744897501960817, 5.0, np.inf])
    assert efficiency_of(e, sd) == pytest.approx(1.0)
    assert np.isnan(efficiency_of(e, np.full(4, np.nan)))


def test_quantile_convention() -> None:
    """``tma2-gs``'s quantile: lower middle value, failures as +inf, empty as NaN."""
    from tma2.cli.gs import _q

    assert _q(np.array([1.0, 2.0, 3.0, 4.0]), 0.5) == 2.0
    assert _q(np.array([1.0, np.inf, np.nan]), 0.5) == np.inf
    assert _q(np.array([np.inf, np.inf]), 0.5) == np.inf  # panel round 2: crashed before
    assert np.isnan(_q(np.array([]), 0.5))


def test_strata() -> None:
    from tma2.segment.score import strata

    m = _meta([(100, 112), (200, 230)])
    m["manoeuvres"][1]["kind"] = "speed"
    own = np.zeros((400, 5))
    tgt = np.zeros((400, 5))
    tgt[:, 1] = 3000.0  # 3 km east of ownship
    s = strata(m, own, tgt, 150)
    assert s["range_band"] == "2-5km" and s["changes"] == "1-5"
    assert s["latest_kind"] == "course" and s["latest_duration"] == "10-20 rows"
    s = strata(m, own, tgt, 250)
    assert s["latest_kind"] == "speed" and s["speed_only"] == "yes"
    assert s["latest_duration"] == ">20 rows"
    assert strata(m, own, tgt, 50)["changes"] == "0"


def test_bounds_and_naive(man2_pack: Any) -> None:
    """Known-manoeuvres bounds are finite and positive on G5 rows of the MAN2 fixture, and the
    naive baseline answers every row."""
    from tma2.eval.errors import Truth
    from tma2.references.naive import fit_naive
    from tma2.segment import score as sc

    metas, owns, tgts, obss, truths = {}, {}, {}, {}, {}
    for j, (_, m, o, t, ob) in enumerate(iter_raw(man2_pack)):
        if j == 4:
            break
        metas[j], owns[j], tgts[j], obss[j] = m, o, t, ob
        truths[j] = Truth.from_block(m, o, t)
    rows = [
        sc.Row(j, k, False) for j in metas for k in sc.g5_rows(metas[j], int(metas[j]["samples"]))
    ]
    assert rows
    sd = sc.bounds(rows, metas, owns, tgts, obss)
    ok = np.isfinite(sd).all(axis=1)
    assert ok.mean() > 0.9 and (sd[ok] > 0).all()
    model = fit_naive(((j, metas[j], owns[j], tgts[j], obss[j]) for j in metas), "test")
    e = sc.naive_errors(rows, owns, obss, truths, model)
    assert np.isfinite(e).all()


def iter_raw(path: Any) -> Any:
    from tma2.data.f32pack import iter_pack_raw

    return iter_pack_raw(path)
