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


def _arc_case() -> tuple[np.ndarray, ...]:
    from tma2.timelate.arc import arc_states

    t = np.arange(0.0, 3600.0, 5.0)
    # ownship: north at 4 m/s, then east from t = 1500
    ovx = np.where(t < 1500, 0.0, 4.0)
    ovy = np.where(t < 1500, 4.0, 0.0)
    ox = np.concatenate([[0.0], np.cumsum(ovx[:-1] * 5.0)])
    oy = np.concatenate([[0.0], np.cumsum(ovy[:-1] * 5.0)])
    spans = np.array([[900.0, 1000.0], [2400.0, 2500.0]])
    theta = np.array([6000.0, 3000.0, 4.0, 5.0, 1.2, 0.0, 0.0, 2.0])
    st = arc_states(theta, t, spans)
    z = np.arctan2(st[:, 0] - ox, st[:, 1] - oy)
    return t, ox, oy, z, spans, theta, st


def test_arc_states_hold_course_and_speed_between_manoeuvres() -> None:
    t, _ox, _oy, _z, _spans, theta, st = _arc_case()
    course = np.arctan2(st[:, 2], st[:, 3])
    speed = np.hypot(st[:, 2], st[:, 3])
    leg = (t > 1000) & (t < 2400)
    assert np.allclose(np.cos(course[leg] - theta[2] - theta[4]), 1.0)
    assert np.allclose(speed[leg], theta[3])
    assert np.allclose(speed[t >= 2500], theta[3] + theta[7])
    # position is the integral of velocity (midpoint steps): check a leg by its endpoints
    i, j = int(np.argmax(t > 1000)), int(np.argmax(t >= 2400))
    assert np.allclose(st[j, :2] - st[i, :2], st[i, 2:] * (t[j] - t[i]), atol=1e-6)


def test_arc_fit_recovers_noise_free_truth_and_the_kind() -> None:
    from tma2.timelate.arc import solve_arc

    t, ox, oy, z, spans, theta, st = _arc_case()
    start = st.copy()
    start[:, :2] = np.stack([ox, oy], axis=1) + 1.3 * (st[:, :2] - np.stack([ox, oy], axis=1))
    start[:, 2:] *= 1.3
    fit, free, _n = solve_arc(t, ox, oy, z, np.ones(t.size, dtype=bool), 0.01, spans, start)
    assert np.allclose(fit.states[:, :2], st[:, :2], atol=1.0)
    assert free.tolist() == [[True, False], [False, True]]


def test_arc_fit_keeps_turns_bounded() -> None:
    from tma2.timelate.arc import MAX_TURN, fit_arc

    t, ox, oy, z, spans, theta, _st = _arc_case()
    th = theta.copy()
    th[4] = 10.0  # a start wound round more than once
    fit = fit_arc(t, ox, oy, z, np.ones(t.size, dtype=bool), 0.01, spans, th)
    assert float(np.abs(fit.theta[4::2]).max()) < MAX_TURN


def test_soft_uniform_is_a_density() -> None:
    from tma2.timelate.prior import log_soft_uniform

    x = np.linspace(-5.0, 9.0, 20001)
    d = np.exp([log_soft_uniform(float(v), 1.0, 3.0) for v in x])
    assert abs(float(np.sum(d) * (x[1] - x[0])) - 1.0) < 1e-3
    assert log_soft_uniform(2.0, 1.0, 3.0) > log_soft_uniform(3.5, 1.0, 3.0)


def test_evidence_prefers_the_history_with_a_clear_manoeuvre() -> None:
    import json
    from pathlib import Path

    from tma2.timelate.prior import ManoeuvrePrior
    from tma2.timelate.retest import joint_fit, log_evidence

    prior = ManoeuvrePrior.from_ranges(
        json.loads(Path("configs/timelate/tl-ranges.json").read_text())
    )
    t, ox, oy, z, spans, theta, _st = _arc_case()
    rng = np.random.default_rng(5)
    sigma = 0.0175
    pb = (t, ox, oy, z + sigma * rng.standard_normal(t.size), np.ones(t.size, dtype=bool), sigma)
    kinds = np.array([[True, False], [False, True]])
    full = joint_fit(pb, theta, spans, free_changes=kinds, prior=prior)
    one = joint_fit(pb, theta[:6], spans[:1], free_changes=kinds[:1], prior=prior)
    assert (
        log_evidence(pb, full, kinds, prior)["total"]
        > log_evidence(pb, one, kinds[:1], prior)["total"]
    )


def test_evidence_search_finds_a_clear_manoeuvre_from_nothing() -> None:
    import json
    from pathlib import Path

    from tma2.timelate.prior import ManoeuvrePrior
    from tma2.timelate.search import candidate_set, evidence_search

    prior = ManoeuvrePrior.from_ranges(
        json.loads(Path("configs/timelate/tl-ranges.json").read_text())
    )
    t, ox, oy, z, spans, theta, st = _arc_case()
    rng = np.random.default_rng(7)
    sigma = 0.0175
    pb = (t, ox, oy, z + sigma * rng.standard_normal(t.size), np.ones(t.size, dtype=bool), sigma)
    best, seen = evidence_search(pb, theta[:4], np.zeros((0, 2)), prior, steps=4)
    assert best.fit.spans.shape[0] >= 1
    assert float(np.abs(best.fit.spans[:, 0] - spans[0, 0]).min()) < 180.0
    cands = candidate_set(seen)
    assert abs(sum(p for _h, p in cands) - 1.0) < 1e-9
    assert cands[0][0].evidence == max(h.evidence for h in seen if np.isfinite(h.evidence))
