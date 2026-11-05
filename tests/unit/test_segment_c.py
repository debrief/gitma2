"""Spec 005 T012–T014: segmenter C's nominations, confirmation and per-prefix segmentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from tma2.data.f32pack import iter_pack_raw
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment import STEADY, TRANSITION, UNKNOWN, Interval, default_parameters, to_codes
from tma2.segment import metrics as mx
from tma2.segment.confirm import (
    Confirmed,
    NearMiss,
    Transition,
    glr_nominations,
    search_nominations,
)
from tma2.segment.segmenter import intervals_at, segment
from tma2.segment.truth import change_rows

S, T, U = STEADY, TRANSITION, UNKNOWN
P = default_parameters(search_penalty=20.0)


def test_glr_nominations_retest_while_raised() -> None:
    stat = np.zeros(100)
    stat[40:55] = 10.0
    stat[80] = 10.0
    noms = glr_nominations(stat, 5.0, P)
    assert [x.row for x in noms] == [40, 46, 52, 80]
    assert noms[0].lo == 40 - P.window_rows + 1 and noms[0].hi == 40


def test_search_nominations_horizon_and_dedupe() -> None:
    by = [
        (100, [(60, 70, False)]),  # 70 + 18 = 88 ≤ 100: nominated at 100
        (130, [(61, 71, False), (110, 125, False)]),  # same start (dedupe); 125 + 18 > 130
        (160, [(110, 125, False), (150, 160, True)]),  # nominated at 160; open: not
    ]
    noms = search_nominations(by, P)
    assert [(x.row, x.source) for x in noms] == [(100, "search"), (160, "search")]
    assert noms[0].lo == 60 - P.window_rows // 2


def test_intervals_at() -> None:
    conf = Confirmed(
        transitions=[
            Transition(100, 111, 130, 130, 40.0, 20.0, "glr"),
            Transition(200, None, 210, 210, 30.0, 10.0, "glr"),  # open until closed
        ],
    )
    p = P
    ivs = intervals_at(conf, 120, p)  # nothing accepted yet at 120
    assert ivs == [Interval(S, 0, 120)]
    ivs = intervals_at(conf, 180, p)
    assert ivs == [Interval(S, 0, 99), Interval(T, 100, 111), Interval(S, 112, 180)]
    ivs = intervals_at(conf, 215, p)
    assert ivs[-1] == Interval(T, 200, 215, True)
    # a near miss (recorded only when its score is within the margin) is unknown from its row on
    conf.near_misses.append(NearMiss(150, 160, 170, -0.5))
    codes = to_codes(intervals_at(conf, 200, p), 201)
    assert (codes[150:161] == U).all() and (codes[112:150] == S).all() and (codes[161:] == S).all()
    assert (to_codes(intervals_at(conf, 169, p), 170)[112:] == S).all()
    # closing an open transition polishes its start with later bearings: prefixes before the
    # close keep the start as accepted (FR-002; Gate S panel round 1)
    conf3 = Confirmed(transitions=[Transition(197, 228, 210, 245, 30.0, 10.0, "glr", 200)])
    assert intervals_at(conf3, 230, p)[-1] == Interval(T, 200, 230, True)
    assert intervals_at(conf3, 250, p)[1] == Interval(T, 197, 228)
    # a steady piece shorter than L_min is unknown
    conf2 = Confirmed(transitions=[Transition(50, 60, 70, 70, 40.0, 20.0, "glr")])
    assert intervals_at(conf2, 75, P)[-1] == Interval(U, 61, 75)
    assert intervals_at(conf2, 75, P)[0] == Interval(S, 0, 49)


def _short(
    pack: Path, n_max: int = 420, count: int = 2
) -> list[tuple[dict[str, Any], BearingData]]:
    out = []
    for _, m, own, _tgt, obs in iter_pack_raw(pack):
        if int(m["samples"]) <= n_max and m.get("manoeuvres"):
            out.append((m, bearing_data_from_arrays(m, own, obs)))
        if len(out) == count:
            break
    return out


@pytest.fixture(scope="module")
def layer() -> PhysicsLayer:
    torch.set_default_dtype(torch.float64)
    return PhysicsLayer()


def test_noise_free_after_zig(man2_noise_free_pack: Path, layer: PhysicsLayer) -> None:
    """On noise-free engagements (search nominations only), every target change after the zig
    with a full leg on both sides is a transition within 8 rows at the last scored row."""
    items = _short(man2_noise_free_pack)
    data = [d for _, d in items]
    metas = [m for m, _ in items]
    rows = [[d.n - 1 - ((d.n - 1 - int(m["zig_index"])) % 6)] for m, d in items]
    segs = segment(layer, data, metas, rows, P)
    checked = 0
    for (m, _d), sg in zip(items, segs, strict=True):
        k = sg[0].k
        pred = [(iv.start, iv.end) for iv in sg[0].intervals if iv.kind == T]
        truth = [
            (a, b)
            for a, b in change_rows(m, "target")
            if a > int(m["zig_index"]) and a >= P.l_min_rows and b <= k - P.l_min_rows
        ]
        assert all(mx.boundary_hits(pred, truth, 8)), (m["index"], truth, pred)
        checked += len(truth)
    assert checked >= 1


def test_prefix_invariance(man2_noise_free_pack: Path, layer: PhysicsLayer) -> None:
    """C's segmentation at row k does not change when the bearings after k are removed."""
    m, d = _short(man2_noise_free_pack, count=1)[0]
    k = int(m["zig_index"]) + 60
    rows = [k, k + 30] if k + 30 < d.n else [k]
    full = segment(layer, [d], [m], [rows], P)[0][0]
    cut = BearingData(**{**d.__dict__})
    cut.valid = d.valid.copy()
    cut.valid[k + 1 :] = 0
    cut.z = d.z.copy()
    cut.z[k + 1 :] = 0.0
    alone = segment(layer, [cut], [m], [[k]], P)[0][0]
    assert full.intervals == alone.intervals
    assert full.cost == pytest.approx(alone.cost, rel=1e-12)


def test_prefix_invariance_open_transition(man2_pack: Path, layer: PhysicsLayer) -> None:
    """At a prefix inside an open transition whose start is later polished, C's segmentation does
    not change when the bearings after k are removed (Gate S panel round 1: the close rewrote the
    start for earlier prefixes). Scenario 2 of the seed-316 fixture under the Gate S parameters:
    accepted at row 573 with start 541, closed at 576 with start 538."""
    from tma2.types.generated.tma import SegmentParameters

    plan = Path(__file__).resolve().parents[2] / "configs" / "segment" / "gs-plan.json"
    pg = SegmentParameters(**json.loads(plan.read_text())["segmenter"]["parameters"])
    for q, (_, m, own, _tgt, obs) in enumerate(iter_pack_raw(man2_pack)):
        if q == 2:
            d = bearing_data_from_arrays(m, own, obs)
            break
    k = 574
    rows = [int(m["zig_index"]), k]  # the search grid is anchored on the first scored row
    full = segment(layer, [d], [m], [rows], pg)[0][1]
    cut = BearingData(**{**d.__dict__})
    cut.valid = d.valid.copy()
    cut.valid[k + 1 :] = 0
    cut.z = d.z.copy()
    cut.z[k + 1 :] = 0.0
    alone = segment(layer, [cut], [m], [rows], pg)[0][1]
    assert full.intervals[-1].open and full.intervals[-1].start == 541
    assert full.intervals == alone.intervals
