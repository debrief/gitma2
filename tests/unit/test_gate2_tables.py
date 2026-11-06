"""E-s's decision tables (spec 007 T012): at zero evidence the tables reproduce C. For a decision
C accepted, "with" is C's own error; for one it rejected, "without" is; and the relaxed loss at
zero evidence and a vanishing temperature is C's own error summed over the decision rows."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from tma2.data.f32pack import iter_pack_raw
from tma2.gate2.tables import (
    _accepted_transition,
    _with,
    _without,
    c_confirmation,
    in_band,
    relaxed_loss,
    scenario_table,
    truth_and_bounds,
)
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment import TRANSITION
from tma2.segment.segmenter import intervals_at
from tma2.types.generated.tma import SegmentParameters

ROOT = Path(__file__).resolve().parents[2]


def _cut(d: BearingData, k: int) -> BearingData:
    """The scenario truncated to rows 0 … k (as ``test_segment_c``)."""
    return BearingData(
        t=d.t[: k + 1].copy(),
        ox=d.ox[: k + 1].copy(),
        oy=d.oy[: k + 1].copy(),
        z=d.z[: k + 1].copy(),
        valid=d.valid[: k + 1].copy(),
        zig_index=d.zig_index,
        sigma=d.sigma,
        index=d.index,
    )


@pytest.fixture(scope="module")
def case(man2_pack: Path):  # type: ignore[no-untyped-def]
    """Scenario 2 of the fixture under the Gate S parameters: C accepts an open transition at
    row 573 (``test_segment_c``), so the table has accepted and rejected decisions."""
    torch.set_default_dtype(torch.float64)
    plan = ROOT / "configs" / "segment" / "gs-plan.json"
    p = SegmentParameters(**json.loads(plan.read_text())["segmenter"]["parameters"])
    _, m, own, tgt, obs = next(x for q, x in enumerate(iter_pack_raw(man2_pack)) if q == 2)
    d = _cut(bearing_data_from_arrays(m, own, obs), 610)  # C on rows 0 … 610 only: test time
    anchor = int(m["zig_index"])
    ks, truth, bound = truth_and_bounds(m, own, tgt, obs, [anchor, 574, 600])
    layer = PhysicsLayer()
    conf = c_confirmation(layer, d, anchor, p)
    tab = scenario_table(layer, d, conf, ks, truth, bound, p, p.mode, None)
    return conf, d, p, tab


def test_decisions_match_c(case) -> None:  # type: ignore[no-untyped-def]
    conf, _d, p, tab = case
    acc = [x for x in tab.decisions if x.accepted]
    assert acc and any(not x.accepted for x in tab.decisions)
    assert len(acc) == len(conf.transitions)
    for x in tab.decisions:  # accepted exactly when the drop beats the threshold
        assert x.accepted == (x.drop - x.threshold > 0.0)
    for x in acc:
        tr = _accepted_transition(conf, x)
        assert tr is not None
        k = max(x.row, 600)
        assert len(intervals_at(_without(conf, tr), k, p)) <= len(intervals_at(conf, k, p))
    assert any(in_band(x, p.tau) for x in tab.decisions)
    assert {r.decision for r in tab.rows} <= {
        q for q, x in enumerate(tab.decisions) if in_band(x, p.tau)
    }
    for x in (y for y in tab.decisions if not y.accepted):
        k = max(x.row, x.start + x.length - 1)
        ivs = intervals_at(_with(conf, x, p.margin), k, p)
        assert any(iv.kind == TRANSITION and iv.start <= x.start <= iv.end for iv in ivs)


def test_with_and_without_are_c(case) -> None:  # type: ignore[no-untyped-def]
    _conf, _d, _p, tab = case
    assert tab.rows
    for r in tab.rows:
        dd = tab.decisions[r.decision]
        c = tab.c_error[r.k]
        assert (r.e_with if dd.accepted else r.e_without) == c
        assert np.isfinite(r.e_with) and np.isfinite(r.e_without)


def test_relaxed_loss_at_zero_evidence_is_c(case) -> None:  # type: ignore[no-untyped-def]
    _conf, d, _p, tab = case
    zero = torch.zeros(d.n, requires_grad=True)
    got = relaxed_loss(tab, zero, temperature=1e-6)
    want = sum(tab.c_error[r.k] for r in tab.rows)
    assert float(got.detach()) == pytest.approx(want, rel=1e-9, abs=1e-9)
    warm = relaxed_loss(tab, zero, temperature=1.0)
    warm.backward()  # type: ignore[no-untyped-call]
    assert zero.grad is not None and torch.isfinite(zero.grad).all()
