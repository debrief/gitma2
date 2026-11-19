"""Spec 024: the incremental C, the realism stream, and the carried time-late start."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from tma2.long.incremental import crop
from tma2.long.sim import generate
from tma2.segment import STEADY, TRANSITION, UNKNOWN, Interval

ROOT = Path(__file__).resolve().parents[2]


def _cfg(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    c = json.loads((ROOT / f"configs/long/{name}.json").read_text())
    return c, json.loads((ROOT / c["target_ranges"]).read_text())


def test_crop_keeps_what_is_inside() -> None:
    ivs = [
        Interval(STEADY, 0, 99),
        Interval(TRANSITION, 100, 129),
        Interval(STEADY, 130, 399),
        Interval(UNKNOWN, 400, 449),
        Interval(TRANSITION, 450, 499, True),
    ]
    got = crop(ivs, 499, 110)
    assert got[0] == Interval(TRANSITION, 0, 19)  # a transition cut by the window keeps its part
    assert got[1] == Interval(STEADY, 20, 289)
    assert got[-1] == Interval(TRANSITION, 340, 389, True)  # the open flag survives
    assert crop(ivs, 499, 0)[:4] == ivs[:4]


def test_realism_keeps_the_base_stream() -> None:
    """The realism stream changes the ownship and what is reported, never the first target or
    the base bearing noise, so the comparison with spec 023 is paired."""
    base, r = _cfg("long")
    real, _ = _cfg("realistic")
    e = generate(int(base["seed"]), 0, 6.0, base, r)
    x = generate(int(real["seed"]), 0, 6.0, real, r)
    assert np.array_equal(e.tgt, x.tgt)
    assert not np.array_equal(e.own, x.own)  # it steers on what it believes
    assert x.meta["valid_share"] < e.obs[:, 2].mean()  # gaps and detection lose bearings
    assert x.other is not None and x.other.meta["contact"] == 2
    assert np.array_equal(x.other.own, x.own)
    assert not np.array_equal(x.other.tgt, x.tgt)
    again = generate(int(real["seed"]), 0, 6.0, real, r)
    assert np.array_equal(again.obs, x.obs) and np.array_equal(again.other.obs, x.other.obs)  # type: ignore[union-attr]
    for a, b in x.meta["realism"]["gaps_s"]:
        rows = (x.obs[:, 0] >= a) & (x.obs[:, 0] < b)
        assert not x.obs[rows, 2].any()


def test_carry_start_uses_the_previous_window() -> None:
    from tma2.long.carry import Carried, _carry_start
    from tma2.long.timelate import chain, period_of

    base, r = _cfg("long")
    e = generate(int(base["seed"]), 0, 6.0, base, r)
    ch = chain(e, 7200.0, 1800.0)
    (a0, n0), (a1, n1) = ch[0], ch[1]
    p = period_of(e, a1, n1, 1)
    t = p.own[:, 0] - p.own[0, 0]
    rows = a0 + np.arange(0, n0, 6)
    truth = np.stack([e.tgt[rows, 1], e.tgt[rows, 2], np.zeros(rows.size), np.zeros(rows.size)], 1)
    spans = np.array([[(a1 + 10) * e.dt, (a1 + 30) * e.dt], [(a0 + 5) * e.dt, (a0 + 9) * e.dt]])
    c2 = np.full((p.rows, 4), 7.0)
    track, sp = _carry_start(p, Carried(rows, truth, spans), c2, np.array([[6000.0, 6100.0]]), t)
    ox, oy = p.meta["window_origin_m"]
    inside = rows[(rows >= a1) & (rows < a0 + n0)]
    assert np.allclose(track[inside - a1, 0] + ox, e.tgt[inside, 1])  # the carried track
    assert np.all(track[(a0 + n0 - a1) + 7 :, 0] == 7.0)  # C″'s after the overlap
    assert sp.tolist() == [[50.0, 150.0], [6000.0, 6100.0]]  # carried span inside; C″'s after


def test_incremental_equals_per_window_for_blocks_of_one() -> None:
    from tma2.long.incremental import Incremental

    base, r = _cfg("long")
    e = generate(int(base["seed"]), 0, 6.0, base, r)
    m = Incremental()
    a = m.run(e, limit=2)
    b = m.run_incremental(e, limit=2, block_s=600.0)
    for s in a["states"]:
        assert np.allclose(a["states"][s], b["states"][s], equal_nan=True, rtol=0, atol=1e-6), s
