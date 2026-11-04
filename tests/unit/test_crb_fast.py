"""The numba known-manoeuvres bound equals the Python one (spec 004 R5)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from tests.conftest import fixture_dir
from tma2.features.batch import generate_indices
from tma2.models.train import batch_from_pack
from tma2.references.crb import crb_known_manoeuvres, crb_known_manoeuvres_fast

PACK = fixture_dir("phase4-seed777") / "validation.f32pack"


def test_fast_bound_matches_python() -> None:
    b = batch_from_pack(Path(PACK), 25)
    assert b.tm is not None and b.n_tm is not None
    from tma2.data.f32pack import iter_pack_raw

    metas = [m for _, m, *_ in iter_pack_raw(PACK)][:25]
    compared = 0
    for i, m in enumerate(metas):
        n = int(b.samples[i])
        tms = m["parameters"]["target_manoeuvres"]
        if not tms:
            continue
        t = b.t[i, :n].astype(np.float64)
        ox, oy = b.own[i, :n, 0].astype(np.float64), b.own[i, :n, 1].astype(np.float64)
        tx, ty = b.tgt[i, :n, 0].astype(np.float64), b.tgt[i, :n, 1].astype(np.float64)
        c, v = b.tgt[i, :n, 2].astype(np.float64), b.tgt[i, :n, 3].astype(np.float64)
        tvx, tvy = v * np.sin(c), v * np.cos(c)
        valid = b.valid[i, :n].astype(np.float64)
        rows = [int(b.zig_index[i]) + 30, n - 1]
        rows = [k for k in rows if k < n]
        slow = crb_known_manoeuvres(
            t, ox, oy, tx, ty, tvx, tvy, valid, tms, rows, float(b.sigma[i])
        )
        fast = crb_known_manoeuvres_fast(
            t, ox, oy, tx, ty, tvx, tvy, valid, b.tm[i, : b.n_tm[i]], rows, float(b.sigma[i])
        )
        for a, f in zip(slow, fast, strict=True):
            assert a.singular == f.singular
            if a.singular:
                continue
            for k in ("sd_range_rel", "sd_course_deg", "sd_speed_kt"):
                assert math.isclose(getattr(a, k), getattr(f, k), rel_tol=1e-9), k
            assert a.state_cov is not None and f.state_cov is not None
            np.testing.assert_allclose(f.state_cov, a.state_cov, rtol=1e-8, atol=1e-12)
            compared += 1
    assert compared > 5


def test_generated_batch_carries_manoeuvre_table() -> None:
    import json

    ranges = json.loads((fixture_dir("phase4-seed777") / "ranges.json").read_text())
    b = generate_indices(777, np.arange(10), ranges)
    assert b.tm is not None and b.n_tm is not None
    assert (b.n_tm >= 0).all() and (b.n_tm <= 4).all()
    for i in range(10):
        spans = int((b.spans[i, :, 1] >= 0).sum())
        assert spans == int(b.n_tm[i])


def test_fast_bound_matches_python_on_man2_with_both_kind() -> None:
    """Generator 0.6.0's "both" manoeuvre (turn and speed change together) in both bounds."""
    import json

    from tma2.sim.generate import generate_scenario

    ranges = json.loads(
        (Path(__file__).resolve().parents[2] / "configs" / "man2-ranges.json").read_text()
    )
    compared = 0
    with_both = 0
    for idx in range(40):
        sc_ = generate_scenario(314, idx, ranges).scenario
        m = sc_.metadata
        tms = [
            t.model_dump(mode="json", exclude_none=True)
            for t in m.parameters.target_manoeuvres or []
        ]
        if not any(t["kind"] == "both" for t in tms):
            continue
        with_both += 1
        own, tgt = sc_.ownship.states, sc_.target.states
        t = np.array([s.timestamp_s for s in own], dtype=np.float64)
        ox = np.array([s.x_m for s in own])
        oy = np.array([s.y_m for s in own])
        tx = np.array([s.x_m for s in tgt])
        ty = np.array([s.y_m for s in tgt])
        tvx = np.array([s.speed_mps * math.sin(s.course_rad) for s in tgt])
        tvy = np.array([s.speed_mps * math.cos(s.course_rad) for s in tgt])
        valid = np.array([1.0 if o.valid else 0.0 for o in sc_.observations])
        codes = {"course": 0.0, "speed": 1.0, "both": 2.0}
        table = np.array(
            [
                [
                    codes[x["kind"]],
                    x["start_time_s"],
                    x["change"],
                    x["rate"],
                    x.get("change2", 0.0),
                    x.get("rate2", 0.0),
                ]
                for x in tms
            ]
        )
        n = len(own)
        rows = [k for k in (int(m.zig_index) + 30, n - 1) if k < n]
        sigma = float(m.parameters.noise_sigma_rad)
        slow = crb_known_manoeuvres(t, ox, oy, tx, ty, tvx, tvy, valid, tms, rows, sigma)
        fast = crb_known_manoeuvres_fast(t, ox, oy, tx, ty, tvx, tvy, valid, table, rows, sigma)
        for a, f in zip(slow, fast, strict=True):
            assert a.singular == f.singular
            if a.singular:
                continue
            for k in ("sd_range_rel", "sd_course_deg", "sd_speed_kt"):
                assert math.isclose(getattr(a, k), getattr(f, k), rel_tol=1e-8), k
            compared += 1
        if with_both >= 4:
            break
    assert with_both >= 2 and compared >= 2
