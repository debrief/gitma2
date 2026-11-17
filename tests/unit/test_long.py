"""Spec 023: the long-engagement simulator and its windows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.long.sim import generate
from tma2.long.timelate import chain
from tma2.long.windows import bearing_data, in_manoeuvre, thinned, turns_veto, window

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def cfg() -> tuple[dict[str, Any], dict[str, Any]]:
    c = json.loads((ROOT / "configs/long/long.json").read_text())
    r = json.loads((ROOT / c["target_ranges"]).read_text())
    return c, r


@pytest.fixture(scope="module")
def eng(cfg):  # type: ignore[no-untyped-def]
    c, r = cfg
    return generate(int(c["seed"]), 1, 6.0, c, r)


def test_deterministic(cfg, eng) -> None:  # type: ignore[no-untyped-def]
    c, r = cfg
    again = generate(int(c["seed"]), 1, 6.0, c, r)
    for a, b in ((eng.own, again.own), (eng.tgt, again.tgt), (eng.obs, again.obs)):
        assert np.array_equal(a, b)
    other = generate(int(c["seed"]), 2, 6.0, c, r)
    assert not np.array_equal(eng.obs, other.obs)


def test_layout_and_kinematics(eng) -> None:  # type: ignore[no-untyped-def]
    dt = eng.dt
    assert eng.samples == int(6 * 3600 / dt)
    assert np.allclose(np.diff(eng.own[:, 0]), dt)
    # bearings are the true bearing plus noise of the stated sd
    v = eng.obs[:, 2] > 0
    b = np.arctan2(eng.tgt[:, 1] - eng.own[:, 1], eng.tgt[:, 2] - eng.own[:, 2])
    d = (eng.obs[v, 1] - b[v] + np.pi) % (2 * np.pi) - np.pi
    assert abs(d.std() / eng.meta["parameters"]["noise_sigma_rad"] - 1) < 0.05
    # the target moves at its stated speed between samples (trapezoid on a 0.5 s grid)
    step = np.hypot(np.diff(eng.tgt[:, 1]), np.diff(eng.tgt[:, 2])) / dt
    assert np.max(np.abs(step - 0.5 * (eng.tgt[1:, 4] + eng.tgt[:-1, 4]))) < 0.05
    lo = eng.meta["parameters"]["target_manoeuvres"]
    assert len(lo) == len(eng.meta["manoeuvres"]) > 5  # Annex B: about two changes an hour
    assert len(eng.meta["ownship_turns"]) >= 8
    assert eng.meta["min_range_m"] > 0


def test_window(eng) -> None:  # type: ignore[no-untyped-def]
    first, rows = 1000, 1440
    w = window(eng, first, rows, "last")
    assert w.samples == rows and w.own[0, 0] == 0.0
    assert w.own[0, 1] == 0.0 and w.own[0, 2] == 0.0
    ox, oy = w.meta["window_origin_m"]
    assert np.allclose(w.tgt[:, 1] + ox, eng.tgt[first : first + rows, 1])
    for s in w.meta["manoeuvres"]:
        assert 1 <= s["start_index"] < rows
    for a, b in w.meta["ownship_turns"]:
        assert 0 <= a <= b < rows
    z = w.meta["zig_index"]
    assert z <= rows - 1 - 60  # at least five minutes before the end
    d = bearing_data(w)
    assert d.n == rows and d.zig_index == z


def test_thinned(eng) -> None:  # type: ignore[no-untyped-def]
    e = thinned(eng, 2)
    assert e.dt == 2 * eng.dt and e.samples == (eng.samples + 1) // 2
    assert np.array_equal(e.obs, eng.obs[::2])


def test_veto_every_turn(eng) -> None:  # type: ignore[no-untyped-def]
    w = window(eng, 0, 2000)
    ev = turns_veto(bearing_data(w), w.meta["ownship_turns"], 6)
    for _a, z in w.meta["ownship_turns"]:
        assert ev[z] > 0
    assert (ev > 0).sum() <= 13 * len(w.meta["ownship_turns"])


def test_chain_covers(eng) -> None:  # type: ignore[no-untyped-def]
    spans = chain(eng, 7200.0, 1800.0)
    assert spans[0][0] == 0 or in_manoeuvre(eng, 0) is not None
    assert spans[-1][0] + spans[-1][1] == eng.samples
    for (a, n), (b, _m) in zip(spans, spans[1:], strict=False):
        assert b < a + n  # consecutive windows overlap
    for a, _n in spans:
        assert in_manoeuvre(eng, a) is None
