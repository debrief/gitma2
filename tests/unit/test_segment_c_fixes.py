"""Segmenter C's fixes before Gate 2 (Gate S panel rounds 1 and 2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.f32pack import iter_pack_raw
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment.confirm import Transition, _free
from tma2.segment.inputs import segmentation_inputs
from tma2.segment.search import anchored_grid, segment_costs
from tma2.types.generated.tma import GateSDecision, SegmentParameters

ROOT = Path(__file__).resolve().parents[2]


def _params() -> SegmentParameters:
    plan = json.loads((ROOT / "configs/segment/gs-plan.json").read_text())
    return SegmentParameters(**plan["segmenter"]["parameters"])


def test_cost_table_is_monotone(man2_pack: Path) -> None:
    """A longer leg from the same start never costs less than a shorter one (R4)."""
    p = _params()
    checked = 0
    for q, (_, m, own, _tgt, obs) in enumerate(iter_pack_raw(man2_pack)):
        if q == 3:
            break
        d = bearing_data_from_arrays(m, own, obs)
        grid = anchored_grid(d.n - 1, int(m["zig_index"]), p.search_step_rows)
        c = segment_costs(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, grid, p.l_min_rows)
        a, b = c[:, :-1], c[:, 1:]
        ok = np.isfinite(a) & np.isfinite(b)
        assert not (a[ok] > b[ok] + 1e-9).any()
        checked += int(ok.sum())
    assert checked > 100


def test_open_transition_reserves_its_longest_span() -> None:
    """An open transition blocks [start, start + l_max − 1], not [start, start + 1] (N3)."""
    acc = [Transition(100, None, 110, 110, 30.0, 10.0, "glr")]
    assert not _free(120, 125, acc, 6, 36)  # inside the open span's reach
    assert _free(150, 160, acc, 6, 36)  # beyond start + l_max − 1 + gap
    closed = [Transition(100, 111, 120, 120, 30.0, 10.0, "glr")]
    assert _free(125, 130, closed, 6, 36)


def _inputs(handover: str) -> Any:
    n = 60
    t = np.arange(n) * 10.0
    z = np.linspace(0.1, 0.4, n)
    v = np.ones(n, dtype=np.uint8)
    return segmentation_inputs(
        t,
        t * 0.0,
        t * 0.0 + 1.0,
        z,
        v,
        50,
        [(10, 20), (40, 50)],
        "gap",
        True,
        None,
        True,
        handover,
    )


def test_open_handover_conventions() -> None:
    """A transition open at k: knots at s and k (default), or a start knot with the bearings
    masked or kept; closed transitions are handed over as before."""
    k_at = _inputs("knot_at_k")
    assert k_at.changepoint[40] == 1 and k_at.changepoint[50] == 1 and k_at.speed_weight[50] == 1
    masked = _inputs("start_masked")
    assert masked.changepoint[40] == 1 and masked.changepoint[50] == 0
    assert (masked.log_weight[40:51] < -1).all() and masked.speed_weight[50] == 0
    chord = _inputs("start_chord")
    assert chord.changepoint[40] == 1 and chord.changepoint[50] == 0
    assert (chord.log_weight[40:51] == 0).all()
    for x in (k_at, masked, chord):  # the closed transition is unchanged
        assert (
            x.changepoint[10] == 1 and x.changepoint[20] == 1 and (x.log_weight[10:20] < -1).all()
        )


def test_parameter_digest_unchanged_for_gate_s() -> None:
    """Optional parameters left at their default do not change the digest Gate S bound."""
    from tma2.cli.segment import params_digest

    d = GateSDecision.model_validate(
        json.loads((ROOT / "experiments/20261104-gs-decision/decision.json").read_text())
    )
    assert params_digest(d.parameters) == (
        "60e6ee635d9390e2c959b408997e39e8c30859febcb2d86f199142ea66aa425f"
    )


def test_code_digest_tracks_the_sources(tmp_path: Path) -> None:
    import shutil

    from tma2.segment.codeid import SOURCES, code_digest

    src = ROOT / "src/tma2"
    for rel in SOURCES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src / rel, tmp_path / rel)
    assert code_digest(tmp_path) == code_digest()
    (tmp_path / "segment/search.py").write_text((src / "segment/search.py").read_text() + "\n# x\n")
    assert code_digest(tmp_path) != code_digest()
