"""Generator 0.6.0, the MAN2 model (spec 006): leg plan, the "both" kind, wander, zig planning,
ranges validation. 0.5.0 byte-identity is guarded by the golden and gitma-conformance suites."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tma2.sim import scenario as sc
from tma2.sim.generate import KernelBuffers, generate_scenario, run_kernel
from tma2.sim.geometry import arc_position, wrap2pi
from tma2.sim.prng import derive_seed
from tma2.sim.ranges import (
    R_LEG_MEAN,
    R_WW_NONE,
    RangesError,
    flatten_ranges,
    rows_for,
)

ROOT = Path(__file__).resolve().parents[2]
MAN2 = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())


def _no_wander(r: dict[str, Any]) -> dict[str, Any]:
    return {**r, "ownship_wander_weights": {"none": 1, "wander": 0, "oscillation": 0, "both": 0}}


def _name(kind: Any) -> str:
    """An enum member's value, whatever the generated type makes of it."""
    return str(getattr(kind, "value", kind))


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def test_validation_and_layout() -> None:
    assert rows_for(MAN2) == 720
    R = flatten_ranges(MAN2)
    assert R[R_LEG_MEAN] == 1500.0
    assert math.isclose(R[R_WW_NONE], 0.4)
    with pytest.raises(RangesError, match="cannot be combined"):
        flatten_ranges({**MAN2, "target_manoeuvre_spacing_s": 180})
    bad = {k: v for k, v in MAN2.items() if k != "target_leg_length_s"}
    with pytest.raises(RangesError, match="needs target_leg_length_s"):
        flatten_ranges(bad)
    with pytest.raises(RangesError, match="needs ownship_wander_weights"):
        flatten_ranges({k: v for k, v in MAN2.items() if k != "ownship_wander_weights"})


def _planned_legs(n_scen: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Leg lengths (s), first-change phase fractions and kinds from plan_target_legs in a window
    long enough that the end of the window does not select short legs."""
    R = flatten_ranges(MAN2)
    legs: list[float] = []
    phases: list[float] = []
    kinds: list[int] = []
    for i in range(n_scen):
        P = np.full(sc.P_LEN, np.nan)
        P[sc.P_DT] = 10.0
        P[sc.P_WINDOW] = 6.0e5  # 1,000 rows of 10 min each: never reached before MAX_TM
        P[sc.P_TGT_SPEED] = 5.0
        tm = np.zeros((sc.MAX_TM, sc.TM_COLS))
        seed = np.uint64(derive_seed(np.uint64(314), i))
        n = sc.plan_target_legs(seed, 0, R, P, tm)
        assert n == sc.MAX_TM
        ends = []
        for j in range(n):
            kind = int(tm[j, sc.TM_KIND])
            kinds.append(kind)
            if kind == 1:
                dur = abs(tm[j, sc.TM_CHANGE]) / tm[j, sc.TM_RATE]
            else:
                dur = abs(tm[j, sc.TM_CHANGE]) / tm[j, sc.TM_RATE]
                if kind == 2:
                    dur = max(dur, abs(tm[j, sc.TM_CHANGE2]) / tm[j, sc.TM_RATE2])
            ends.append(tm[j, sc.TM_START] + dur)
        for j in range(1, n):
            legs.append(tm[j, sc.TM_START] - ends[j - 1])
        phases.append(tm[0, sc.TM_START])
    return np.asarray(legs), np.asarray(phases), np.asarray(kinds)


def test_leg_plan_matches_the_owners_model() -> None:
    legs, _phases, kinds = _planned_legs(600)
    mean, sd, lo = 1500.0, 546.0, 300.0
    # whole-row start times shift each leg by at most one row (10 s)
    x = np.sort(legs)
    n = x.size
    # the clip puts the mass below `lo` at `lo` itself: F(v) = Φ(z) for v ≥ lo
    model = np.array([_norm_cdf((v - mean) / sd) if v >= lo else 0.0 for v in x])
    ecdf = np.arange(1, n + 1) / n
    d = float(np.max(np.abs(ecdf - model)))
    assert d < 1.63 / math.sqrt(n) + 10.0 / sd  # KS at 1%, plus the one-row rounding allowance
    share10 = float(np.mean(legs <= 600.0 + 10.0))
    assert 0.04 <= share10 <= 0.06, share10
    assert 0.92 * 1500 < float(np.median(legs)) < 1.08 * 1500
    shares = np.bincount(kinds, minlength=3) / kinds.size
    assert abs(shares[0] - 0.8) < 0.02 and abs(shares[1] - 0.1) < 0.02
    assert abs(shares[2] - 0.1) < 0.02


def test_plan_is_deterministic_and_attempt_dependent() -> None:
    R = flatten_ranges(MAN2)

    def plan(attempt: int) -> np.ndarray:
        P = np.full(sc.P_LEN, np.nan)
        P[sc.P_DT] = 10.0
        P[sc.P_WINDOW] = 7200.0
        P[sc.P_TGT_SPEED] = 5.0
        tm = np.zeros((sc.MAX_TM, sc.TM_COLS))
        sc.plan_target_legs(np.uint64(derive_seed(np.uint64(7), 3)), attempt, R, P, tm)
        return tm

    assert np.array_equal(plan(0), plan(0))
    assert not np.array_equal(plan(0), plan(1))


def test_both_kind_reduces_to_the_arc_and_ends_exactly() -> None:
    omega, dur = math.radians(0.5), 120.0
    for tau in (0.0, 13.0, 60.0, 120.0):
        x, y, c, v = sc.both_state(100.0, -50.0, 0.3, 4.0, omega, dur, 0.0, 0.02, 0.0, tau)
        ax, ay, ac = arc_position(100.0, -50.0, 0.3, 4.0, omega, tau)
        assert abs(x - ax) < 1e-2 and abs(y - ay) < 1e-2  # 1 s midpoint rule: ~1 mm per 2 min
        assert abs(c - ac) < 1e-12 and v == 4.0
    _x, _y, c, v = sc.both_state(0.0, 0.0, 1.0, 4.0, -omega, dur, -1.5, 0.025, 60.0, 200.0)
    assert math.isclose(c, wrap2pi(1.0 - omega * dur), abs_tol=1e-12)
    assert math.isclose(v, 2.5, abs_tol=1e-12)


def test_generated_spans_and_both_kind_are_recorded() -> None:
    kinds: set[str] = set()
    for i in range(80):
        m = generate_scenario(314, i, MAN2).scenario.metadata
        for sp in m.manoeuvres or []:
            kinds.add(_name(sp.kind))
            assert 1 <= sp.start_index <= sp.end_index <= m.samples
        for t in m.parameters.target_manoeuvres or []:
            if _name(t.kind) == "both":
                assert t.change2 is not None and t.rate2 is not None
    assert {"course", "speed", "both"} <= kinds


def test_wander_stays_in_band_and_is_separable() -> None:
    worst = 0.0
    seen = set()
    for i in range(120):
        a = generate_scenario(314, i, MAN2).scenario
        b = generate_scenario(314, i, _no_wander(MAN2)).scenario
        ca = np.array([s.course_rad for s in a.ownship.states])
        cb = np.array([s.course_rad for s in b.ownship.states])
        worst = max(worst, float(np.max(np.abs(np.angle(np.exp(1j * (ca - cb)))))))
        assert [s.model_dump() for s in a.target.states] == [
            s.model_dump() for s in b.target.states
        ]
        assert a.metadata.manoeuvres == b.metadata.manoeuvres
        assert a.metadata.ownship_wander is not None
        seen.add(_name(a.metadata.ownship_wander.kind))
        if _name(a.metadata.ownship_wander.kind) == "none":
            assert np.array_equal(ca, cb)
    assert worst <= math.radians(5.0)
    assert {"none", "wander", "oscillation"} <= seen


def test_zig_planned_on_the_simulated_target_and_flagged() -> None:
    R = flatten_ranges(_no_wander(MAN2))
    buf = KernelBuffers.for_rows(720)
    flagged = 0
    for i in range(60):
        run_kernel(np.uint64(314), i, R, buf)
        P, TI = buf.P, buf.TI
        # the target position used for the zig plan is the generated target track's
        k = TI[sc.TI_ZIG]
        tx, ty = sc.target_position(P, buf.tm, int(k), 720)
        assert abs(tx - buf.tgt[k, 0]) < 0.5 and abs(ty - buf.tgt[k, 1]) < 0.5  # float32 storage
        # rows shared by the ownship's turn [turn start, zig) and a span [start, end)
        turn = set(range(TI[sc.TI_TURN_START], TI[sc.TI_ZIG]))
        inside = any(
            turn & set(range(buf.spans[j, 1], buf.spans[j, 2])) for j in range(TI[sc.TI_N_SPANS])
        )
        assert (P[sc.P_ZIG_ON_MAN] > 0) == inside
        flagged += inside
    assert flagged < 60


def test_spans_are_padded_beyond_the_plan() -> None:
    R = flatten_ranges(MAN2)
    buf = KernelBuffers.for_rows(720)
    run_kernel(np.uint64(314), 0, R, buf)
    n = int(buf.TI[sc.TI_N_SPANS])
    assert 0 < n < sc.MAX_TM
    from tma2.features.batch import generate_indices

    b = generate_indices(314, np.arange(3), MAN2)
    assert b.spans.shape[1] == sc.MAX_TM and b.tm.shape[1:] == (sc.MAX_TM, sc.TM_COLS)
    for i in range(3):
        k = int(b.n_tm[i])
        assert np.all(b.spans[i, k:] == -1)


def test_wander_positions_are_the_integral_of_the_recorded_course() -> None:
    checked = 0
    for i in range(60):
        a = generate_scenario(314, i, MAN2).scenario
        b = generate_scenario(314, i, _no_wander(MAN2)).scenario
        w = a.metadata.ownship_wander
        assert w is not None
        if _name(w.kind) == "none":
            continue
        v = float(a.metadata.parameters.ownship_speed_mps)
        dt = float(a.metadata.parameters.dt_s)
        ca = [s.course_rad for s in a.ownship.states]
        cb = [s.course_rad for s in b.ownship.states]
        for j in range(1, len(ca)):
            if cb[j] != cb[j - 1] or (j + 1 < len(cb) and cb[j + 1] != cb[j]):
                continue  # turn rows, and the row before one, keep the planned arc
            if cb[j - 1] != cb[j]:
                continue
            p0, p1 = a.ownship.states[j - 1], a.ownship.states[j]
            ex = p0.x_m + 0.5 * v * dt * (math.sin(ca[j - 1]) + math.sin(ca[j]))
            ey = p0.y_m + 0.5 * v * dt * (math.cos(ca[j - 1]) + math.cos(ca[j]))
            # stored positions and courses are float32: a few mm at ranges of tens of km
            assert abs(p1.x_m - ex) < 0.05 and abs(p1.y_m - ey) < 0.05
            checked += 1
    assert checked > 1000


def test_ranges_cli_describes_and_samples(capsys: pytest.CaptureFixture[str]) -> None:
    from tma2.cli.ranges import main

    assert main(["--describe", str(ROOT / "configs" / "man2-ranges.json"), "--sample", "60"]) == 0
    out = capsys.readouterr().out
    assert "generator 0.6.0 leg model" in out and "720 rows" in out
    assert "P5/P50/P95 10.0 / 25.0 / 40.0 min" in out and "P(leg ≤ 10 min) 0.050" in out
    assert "cut off by the window's end, left out" in out
    assert "ownship zig overlapping" in out
    phase4 = ROOT / "tests" / "fixtures" / "gitma" / "phase4-seed777" / "ranges.json"
    assert main(["--describe", str(phase4), "--sample", "20"]) == 0
    out = capsys.readouterr().out
    assert "0.5.0 manoeuvre count model" in out and "ownship zig overlapping" not in out


def test_wander_weight_validation() -> None:
    no_osc = {k: v for k, v in MAN2.items() if k != "ownship_oscillation"}
    with pytest.raises(RangesError, match="needs ownship_oscillation"):
        flatten_ranges(no_osc)
    zero = {**MAN2, "ownship_wander_weights": {"none": 0, "wander": 0, "oscillation": 0, "both": 0}}
    with pytest.raises(RangesError, match="positive sum"):
        flatten_ranges(zero)
    neg = {**MAN2, "target_change_kind_weights": {"course": 1, "speed": -0.1, "both": 0.1}}
    with pytest.raises(RangesError, match="non-negative"):
        flatten_ranges(neg)


def test_both_kind_counts_as_a_turn_and_a_speed_change() -> None:
    from tma2.detect.matching import _is_turn
    from tma2.eval.slices import manoeuvre_band

    plan = {"parameters": {"target_manoeuvres": [{"kind": "speed"}, {"kind": "both"}]}}
    assert manoeuvre_band(plan) == "1turn+speed"
    only = {"parameters": {"target_manoeuvres": [{"kind": "both"}]}}
    assert manoeuvre_band(only) == "1turn+speed"
    assert _is_turn("both") and _is_turn("course") and not _is_turn("speed")


def test_fast_bound_refuses_a_narrow_table_with_both() -> None:
    from tma2.references.crb import crb_known_manoeuvres_fast

    n = 50
    t = np.arange(n) * 10.0
    z = np.zeros(n)
    tm = np.array([[2.0, 100.0, 0.5, 0.01]])
    with pytest.raises(ValueError, match="six-column"):
        crb_known_manoeuvres_fast(t, z, z, z + 5000, z + 5000, z + 1, z, np.ones(n), tm, [40], 0.02)
