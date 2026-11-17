"""Spec 023: layout, masked span and the paired readings."""

from __future__ import annotations

import numpy as np

from tma2.timelate.layout import Layout, layout, period, span
from tma2.timelate.periods import Period
from tma2.timelate.study8 import gap_reading, paired, period_table, verdict


def _engagement(n: int = 1440) -> Period:
    own = np.zeros((n, 5), dtype=np.float32)
    own[:, 0] = np.arange(n) * 5.0
    tgt = np.zeros((n, 5), dtype=np.float32)
    obs = np.ones((n, 3), dtype=np.float32)
    return Period(7, {"seed": "123", "manoeuvres": []}, own, tgt, obs, 0, n, 5.0)


def test_layout_reproducible_and_inside():
    for seed in range(40):
        a = layout(np.uint64(seed), 1440, 5.0)
        b = layout(np.uint64(seed), 1440, 5.0)
        assert a == b
        assert a is not None
        assert 2 <= len(a.periods) <= 3
        assert a.first >= 0 and a.first + a.rows <= 1440
        for (p, n), (q, _m) in zip(a.periods[:-1], a.periods[1:], strict=True):
            assert 180 <= n <= 360  # 15 to 30 min at 5 s
            assert 60 <= q - (p + n) <= 360  # gaps 5 to 30 min
        assert [g[1] for g in a.gaps()] == [
            q - (p + n) for (p, n), (q, _m) in zip(a.periods[:-1], a.periods[1:], strict=True)
        ]


def test_layout_drops_periods_that_do_not_fit():
    short = [layout(np.uint64(s), 520, 5.0) for s in range(200)]
    assert any(x is None for x in short)
    for x in short:
        if x is not None:
            assert x.first + x.rows <= 520 and len(x.periods) >= 2
    assert layout(np.uint64(1), 300, 5.0) is None


def test_layout_does_not_touch_the_engagement_stream():
    # the layout's stream is its own: a different seed changes it, the same seed never does
    a = [layout(np.uint64(s), 1440, 5.0) for s in range(20)]
    assert len({x for x in a}) > 10


def test_span_masks_exactly_the_gaps_and_copies():
    x = _engagement()
    lay = Layout(100, ((100, 200), (400, 250), (800, 200)))
    m = span(x, lay, masked=True)
    f = span(x, lay, masked=False)
    assert m.first == 100 and m.rows == 900
    assert f.obs is x.obs and m.obs is not x.obs
    assert (x.obs[:, 2] == 1).all()  # the engagement is untouched
    v = m.obs[:, 2] != 0
    gap = np.zeros(1440, dtype=bool)
    gap[300:400] = gap[650:800] = True
    assert (v == ~gap).all()
    p = period(x, 400, 250)
    assert p.first == 400 and p.rows == 250 and p.obs is x.obs


def test_paired_resamples_engagements():
    # two engagements: one with two periods twice as good, one with one period level
    num = np.array([[2.0, 1, 1], [2.0, 1, 1], [1.0, 1, 1]])
    den = np.ones((3, 3))
    r = paired(num, den, np.array([0, 0, 1]))
    assert r["periods"] == 3 and r["engagements"] == 2
    assert abs(r["value"] - 2 ** (2 / 3)) < 1e-12
    assert r["lo"] <= r["value"] <= r["hi"]
    assert r["lo"] >= 1.0 - 1e-12  # resamples are all-level, mixed or all-better, never worse
    assert r["twice_as_good"] == 0.0 and r["better"] == 2 / 3


def test_period_table_uses_common_rows():
    arr = {
        "eng": np.array([1, 1, 1, 2]),
        "period": np.array([0, 0, 1, 0], dtype=np.int8),
        "err_a": np.array([[0.1, 1, 1, 0], [0.3, 1, 1, 0], [0.2, 1, 1, 0], [0.5, 1, 1, 0]]),
        "err_b": np.array([[0.1, 1, 1, 0], [np.nan] * 4, [0.4, 1, 1, 0], [0.5, 1, 1, 0]]),
    }
    t = period_table(arr, np.array([True, True, True, False]), ["a", "b"])
    assert t["eng"].tolist() == [1, 1] and t["period"].tolist() == [0, 1]
    assert t["a"][:, 0].tolist() == [0.1, 0.2]  # the row b lacks is dropped for both
    assert t["dropped_rows_without_state"] == 1


def test_gap_reading_and_verdict():
    recs = [
        {"gaps": [{"true": 1, "declared": 1}, {"true": 0, "declared": 0}]},
        {"gaps": [{"true": 2, "declared": 0}, {"true": 0, "declared": 1}]},
    ]
    g = gap_reading(recs)
    assert (g["found"], g["missed"], g["invented"]) == (1, 1, 1)
    gain = {
        "ratios": {"alone/joint": {q: {"lo": 1.2, "hi": 2.0} for q in ("range", "course", "speed")}}
    }
    assert verdict(gain)["outcome"] == "gain"
    harm = {
        "ratios": {
            "alone/joint": {
                "range": {"lo": 1.2, "hi": 2},
                "course": {"lo": 0.5, "hi": 0.9},
                "speed": {"lo": 1, "hi": 1},
            }
        }
    }
    assert verdict(harm)["outcome"] == "harm"
