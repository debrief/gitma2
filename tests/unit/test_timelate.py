"""Spec 013 phase 1: periods, normal points, the track read-out and the whole-period bound."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from tma2.cli.oracle import run_layer
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import oracle_inputs
from tma2.references.crb import crb_rows
from tma2.timelate.bound import period_bound
from tma2.timelate.periods import cut, iter_periods
from tma2.timelate.points import fixed_points
from tma2.timelate.track import track


def test_cut_is_seeded_and_inside() -> None:
    a = cut(np.uint64(12345), 900, 5.0)
    assert a == cut(np.uint64(12345), 900, 5.0)
    first, rows = a
    assert rows >= 240 and first >= 0 and first + rows <= 900
    assert cut(np.uint64(1), 100, 5.0) == (0, 100)  # shorter than the minimum: taken whole
    assert len({cut(np.uint64(s), 900, 5.0) for s in range(20)}) > 10


def test_period_spans_are_reindexed(man2_pack: Path) -> None:
    for p in iter_periods(str(man2_pack), 0, 6, min_seconds=600.0):
        assert 0 <= p.first and p.last < p.own.shape[0]
        for s in p.spans():
            assert 0 <= s["start_index"] <= s["end_index"] < p.rows
        for a, b in p.ownship_turns():
            assert 0 <= a <= b < p.rows


def test_whole_period_bound_equals_the_prefix_bound_at_the_last_row(man2_pack: Path) -> None:
    p = next(iter_periods(str(man2_pack), 0, 1, whole=True))
    m = p.meta
    b = period_bound(p)
    c = crb_rows(
        p.own, p.tgt, p.obs, float(m["parameters"]["noise_sigma_rad"]), int(m["zig_index"]),
        m.get("manoeuvres"), [p.rows - 1], model="known_manoeuvres",
        target_manoeuvres=m["parameters"].get("target_manoeuvres"), fast=True,
    )[0]  # fmt: skip
    assert np.allclose(b[-1], (c.sd_range_rel, c.sd_course_deg, c.sd_speed_kt), rtol=1e-9)
    # with every bearing in hand, no interior row is known worse than under its own prefix
    k = p.rows // 2
    mid = crb_rows(
        p.own, p.tgt, p.obs, float(m["parameters"]["noise_sigma_rad"]), int(m["zig_index"]),
        m.get("manoeuvres"), [k], model="known_manoeuvres",
        target_manoeuvres=m["parameters"].get("target_manoeuvres"), fast=True,
    )[0]  # fmt: skip
    if not mid.singular and np.isfinite(b[k, 0]):
        assert b[k, 0] <= mid.sd_range_rel * (1 + 1e-9)


def test_track_at_the_last_point_is_the_layers_state(man2_pack: Path) -> None:
    torch.set_default_dtype(torch.float64)
    p = next(iter_periods(str(man2_pack), 0, 1, whole=True))
    pt = fixed_points(p, 2)
    d = pt.data
    sp = [
        {**s, "start_index": s["start_index"] // 2, "end_index": s["end_index"] // 2}
        for s in p.spans()
    ]
    inp = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, d.n - 1, sp, True)
    assert inp is not None
    res = run_layer(PhysicsLayer(knots=12), [(d, d.n - 1, inp)], d.n)
    st = track(
        res.theta[0].numpy(), d.t[res.knots[0].numpy()], res.knot_weights[0].numpy(), d.t[-1:]
    )[0]
    assert np.allclose(st, res.state[0].numpy(), rtol=1e-9, atol=1e-6)


def test_pair_points() -> None:
    from tma2.timelate.periods import Period

    n = 40
    own = np.zeros((n, 5))
    own[:, 0] = 5.0 * np.arange(n)
    own[:, 1] = 3.0 * np.arange(n)
    obs = np.zeros((n, 3))
    obs[:, 1] = 0.5
    obs[:, 2] = 1.0
    obs[3, 2] = 0.0
    meta = {"index": 0, "parameters": {"noise_sigma_rad": 0.02, "dt_s": 5.0}, "manoeuvres": []}
    pt = fixed_points(Period(0, meta, own, np.zeros((n, 5)), obs, 10, 20, 5.0), 2)
    assert pt.data.n == 10 and np.allclose(pt.data.t[:2], [2.5, 12.5])
    assert np.allclose(pt.data.z, 0.5) and np.isclose(pt.data.sigma, 0.02 / np.sqrt(2))
    assert np.allclose(pt.data.ox[:2], [31.5, 37.5])
