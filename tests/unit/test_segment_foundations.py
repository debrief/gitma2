"""Spec 005 foundations: the interval validator (T005), truth labels (T007, research R4), metrics
(T008) and the hand-over to the physics layer (T009)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.data.f32pack import iter_pack_raw
from tma2.physics.segmentation import oracle_inputs
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment import (
    STEADY,
    TRANSITION,
    UNKNOWN,
    Interval,
    SegmentationError,
    default_parameters,
    from_codes,
    to_codes,
    validate,
)
from tma2.segment import metrics as mx
from tma2.segment.inputs import segmentation_inputs
from tma2.segment.truth import change_rows, truth_codes, widen

S, T, U = STEADY, TRANSITION, UNKNOWN

# --- validator ---------------------------------------------------------------------------


def test_validate_accepts_a_tiling() -> None:
    validate([Interval(S, 0, 29), Interval(T, 30, 35), Interval(S, 36, 99)], 99, 30, 6)
    validate([Interval(U, 0, 9), Interval(S, 10, 39), Interval(T, 40, 41, True)], 41, 30, 6)


@pytest.mark.parametrize(
    "ivs,k",
    [
        ([Interval(S, 0, 29), Interval(T, 31, 36)], 36),  # hole
        ([Interval(S, 0, 29), Interval(T, 29, 36)], 36),  # overlap
        ([Interval(S, 0, 28), Interval(T, 29, 36)], 36),  # leg < L_min
        ([Interval(S, 0, 29), Interval(T, 30, 34), Interval(S, 35, 64)], 64),  # transition < T_min
        ([Interval(T, 0, 1, True), Interval(S, 2, 31)], 31),  # open not last
        ([Interval(S, 0, 29)], 30),  # does not reach k
    ],
)
def test_validate_rejects(ivs: list[Interval], k: int) -> None:
    with pytest.raises(SegmentationError):
        validate(ivs, k, 30, 6)


def test_codes_round_trip() -> None:
    ivs = [Interval(U, 0, 4), Interval(S, 5, 40), Interval(T, 41, 47), Interval(S, 48, 90)]
    assert from_codes(to_codes(ivs, 91)) == ivs


def test_default_parameters_follow_annex_b() -> None:
    p = default_parameters()
    assert (p.course_tol_deg, p.l_min_rows, p.t_min_rows) == (5.0, 30, 6)


# --- truth labels ------------------------------------------------------------------------


def _meta(spans: list[tuple[int, int]], n: int = 300, zig: int = 60) -> dict[str, Any]:
    return {
        "samples": n,
        "turn_start_index": zig - 10,
        "zig_index": zig,
        "manoeuvres": [{"start_index": a, "end_index": b, "kind": "course"} for a, b in spans],
    }


def test_widen_and_merge() -> None:
    assert widen([(100, 101)], 6, 300) == [(98, 103)]
    assert widen([(100, 100)], 6, 300) == [(98, 103)]  # odd shortfall: extra row after
    assert widen([(100, 110)], 6, 300) == [(100, 110)]
    assert widen([(100, 101), (104, 105)], 6, 300) == [(98, 107)]  # touching → merged
    assert widen([(0, 1)], 6, 300) == [(0, 3)]  # clipped


def test_truth_codes_target() -> None:
    m = _meta([(120, 131), (200, 203)])
    c = truth_codes(m, "target", l_min=30, t_min=6)
    assert (c[:61] == U).all()  # prior up to the zig's end
    assert (c[61:120] == S).all()
    assert (c[120:132] == T).all()
    assert (c[132:199] == S).all()
    assert (c[199:205] == T).all()  # 200..203 widened to 199..204
    assert (c[205:] == S).all()
    # a piece shorter than L_min is unknown
    c2 = truth_codes(_meta([(120, 131), (150, 160)]), "target", 30, 6)
    assert (c2[132:150] == U).all()
    c3 = truth_codes(m, "target", 30, 6, prior_unknown=False)
    assert (c3[:120] == S).all()


def test_truth_codes_ownship_two_turns() -> None:
    m = _meta([], zig=60)
    m["turn2_start_index"], m["zig2_index"] = 200, 215
    c = truth_codes(m, "ownship", 30, 6)
    assert (c[50:61] == T).all() and (c[200:216] == T).all()
    assert (c[:50] == S).all() and (c[61:200] == S).all() and (c[216:] == S).all()


def test_truth_matches_true_track_changes(man2_pack: Path) -> None:
    """R4 on MAN2: the target's true course or speed changes exactly on its span rows, and every
    ownship steady row lies within ± C (5°) of its leg's circular mean (wander and oscillation)."""
    c_tol = math.radians(5.0)
    for _, m, own, tgt, _obs in iter_pack_raw(man2_pack):
        n = int(m["samples"])
        ch = np.zeros(n, dtype=bool)
        ch[1:] = (tgt[1:, 3] != tgt[:-1, 3]) | (tgt[1:, 4] != tgt[:-1, 4])
        tr = np.zeros(n, dtype=bool)
        for a, b in change_rows(m, "target"):
            tr[a : b + 1] = True
        assert (ch == tr).all(), m["index"]
        oc = truth_codes(m, "ownship", 30, 6)
        for iv in from_codes(oc):
            if iv.kind != S:
                continue
            crs = own[iv.start : iv.end + 1, 3].astype(np.float64)
            mean = math.atan2(np.sin(crs).mean(), np.cos(crs).mean())
            dev = np.abs((crs - mean + math.pi) % (2 * math.pi) - math.pi)
            assert dev.max() <= c_tol, (m["index"], iv, float(np.degrees(dev.max())))


# --- metrics -----------------------------------------------------------------------------


def test_metrics_oracle_and_one_leg() -> None:
    truth = np.array([U] * 10 + [S] * 40 + [T] * 8 + [S] * 42, dtype=np.int8)
    assert mx.contamination(truth, truth) == 0.0
    assert mx.coverage(truth, truth) == 1.0
    one = np.full(100, S, dtype=np.int8)
    assert mx.contamination(one, truth) == pytest.approx(8 / 90)
    assert mx.coverage(one, truth) == 1.0
    assert mx.gap_recovered(10.0, 10.0, 4.0) == 0.0
    assert mx.gap_recovered(10.0, 4.0, 4.0) == 1.0
    assert math.isnan(mx.gap_recovered(4.0, 4.0, 4.0))
    assert mx.leg_count(truth) == 2


def test_false_split_and_boundaries() -> None:
    assert mx.false_split([], 0) is False
    assert mx.false_split([(10, 15)], 0) is True
    assert mx.false_split([(10, 15)], 1) is None
    truth = [(100, 110), (300, 305)]
    pred = [(103, 112), (500, 506)]
    assert mx.match_transitions(pred, truth) == [0, None]
    assert mx.boundary_hits(pred, truth, 6) == [True, False]
    assert mx.boundary_hits(pred, truth, 2) == [False, False]


def test_live_metrics() -> None:
    truth = [(100, 110)]
    seq = [
        (95, []),
        (105, [(101, 105)]),  # found at k = 105: delay 5
        (120, [(102, 112)]),
        (130, [(102, 112), (60, 66)]),  # a false one
        (140, [(102, 112), (61, 67)]),  # the same false one, not counted again
    ]
    assert mx.detection_delays(seq, truth, 6) == [5]
    assert mx.false_transitions(seq, truth, 6) == 1
    moves, tracked = mx.boundary_moves(seq, 6)
    assert tracked == 3 and moves == 0
    moves, _ = mx.boundary_moves([(115, [(100, 110)]), (130, [(105, 125)])], 6)
    assert moves == 1


# --- hand-over to the physics layer --------------------------------------------------------


def test_truth_transitions_equal_oracle_inputs(man2_pack: Path) -> None:
    for i, (_, m, own, _tgt, obs) in enumerate(iter_pack_raw(man2_pack)):
        if i >= 12:
            break
        d = bearing_data_from_arrays(m, own, obs)
        k = d.n - 1
        spans = m.get("manoeuvres") or []
        trs = [(int(s["start_index"]), int(s["end_index"])) for s in spans]
        kinds = [s["kind"] == "course" for s in spans]
        for mode, mask in (("chord", False), ("gap", True)):
            got = segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, trs, mode, True, kinds)
            want = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, spans, True, mask)
            assert got is not None and want is not None
            for f in ("changepoint", "speed_weight", "log_weight", "theta0", "speed_skip"):
                np.testing.assert_array_equal(getattr(got, f), getattr(want, f), err_msg=f)
