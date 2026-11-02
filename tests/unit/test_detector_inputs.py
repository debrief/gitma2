"""Soft segmentation → physics inputs and knot export (spec 004 FR-014, R4)."""

from __future__ import annotations

import numpy as np
import torch

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.models.detector_inputs import export_knots, knot_arrays, physics_inputs
from tma2.physics.segmentation import oracle_inputs
from tma2.references.classical import bearing_data_from_arrays


def tt(a: np.ndarray) -> torch.Tensor:
    return torch.tensor(a, dtype=torch.float64).unsqueeze(0)


def test_export_knots_local_maxima() -> None:
    w = np.zeros(40)
    w[5:10] = [0.2, 0.6, 0.9, 0.6, 0.2]  # peak at 7
    w[15:18] = [0.7, 0.7, 0.1]  # plateau: once, at 15
    w[25] = 0.4  # below threshold
    w[30:33] = [0.55, 0.8, 0.55]  # beyond k
    pk = np.zeros(40)
    pk[7] = 0.9
    knots = export_knots(w, pk, 29)
    assert [(k.row, k.kind) for k in knots] == [(7, "course"), (15, "speed")]
    assert [k.row for k in export_knots(w, pk, 39, max_knots=2)] == [7, 31]
    assert export_knots(np.zeros(40), pk, 39) == []


def test_truth_segmentation_reproduces_oracle_knots() -> None:
    """A detector that outputs the truth boundaries (w = 1, isolated) and their kinds exports
    exactly the oracle's knots, and its layer inputs carry the speed prior on every course knot."""
    done = 0
    for _, meta, own, _tgt, obs in iter_pack_raw(fixture_dir("phase4-seed777") / "test.f32pack"):
        spans = meta.get("manoeuvres") or []
        if not spans:
            continue
        d = bearing_data_from_arrays(meta, own, obs)
        n = d.n
        k = n - 1
        orc = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, spans, speed_prior=True)
        assert orc is not None
        kind_row = np.zeros(n)
        for s in spans:
            for r in (s["start_index"], s["end_index"]):
                if 0 < r <= k:
                    kind_row[r] = 1.0 if s["kind"] == "course" else 0.0
        knots = export_knots(orc.changepoint, kind_row, k)
        bounds = set(np.flatnonzero(orc.changepoint).tolist())
        # adjacent boundaries (a one-row speed change) are a plateau: one knot, at its first row
        assert [kn.row for kn in knots] == sorted(r for r in bounds if r - 1 not in bounds)
        cp, kind = knot_arrays(knots, n)
        if all(r - 1 not in bounds for r in bounds):
            np.testing.assert_array_equal(cp, orc.changepoint)
        x = physics_inputs(
            tt(cp),
            tt(kind),
            tt(d.z),
            tt(d.valid.astype(np.float64)),
            torch.stack([tt(d.ox), tt(d.oy)], dim=2),
            tt(d.t),
            torch.tensor([d.sigma], dtype=torch.float64),
            torch.tensor([k]),
        )
        np.testing.assert_allclose(x.theta0[0].numpy(), orc.theta0, rtol=1e-9, atol=1e-6)
        # the prior sits on every course knot (start and end), a superset of the oracle's
        if all(r - 1 not in bounds for r in bounds):
            assert np.all(x.speed_weight[0].numpy() >= orc.speed_weight)
        assert x.speed_skip is not None and torch.equal(x.speed_skip, x.speed_weight)
        done += 1
        if done >= 10:
            break
    assert done > 0
