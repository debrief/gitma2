"""tma2-tune criteria (spec 003 R6, spec 004 R7)."""

from __future__ import annotations

import math

from tma2.cli.tune import G5_EKF_GRID, G5_IMM_GRID, _load, _score
from tma2.references.imm import imm_name

FIXTURE = "tests/fixtures/gitma/phase4-seed777/validation.f32pack"


def test_g5_rows_are_zig_plus_5_to_20_min() -> None:
    for meta, _own, _tgt, _obs, ks in _load(FIXTURE, 20, "g5"):
        dt = float(meta["parameters"]["dt_s"])
        offsets = [round((k - int(meta["zig_index"])) * dt) for k in ks]
        assert offsets == [300, 600, 900, 1200][: len(offsets)]
        assert all(k < int(meta["samples"]) for k in ks)


def test_g5_grid_contains_p0_setting_at_its_centre() -> None:
    names = [imm_name(p) for p in G5_IMM_GRID]
    assert len(names) == 243 + 26 and len(set(names)) == len(names)
    assert "imm-cv0.01-ct0.03-w0.01-s0.001-p4-r8" in names
    assert len(G5_EKF_GRID) == 21


def test_g5_score_is_finite() -> None:
    _, _, med = _score(("imm", G5_IMM_GRID[0], FIXTURE, 10, "g5"))
    assert math.isfinite(med) and med > 0
