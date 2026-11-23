"""Spec 037 research R2: the overlay's second stream (Student-t white error, a level step)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tma2.sim import mismatch as mm
from tma2.sim import scenario as sc
from tma2.sim.generate import KernelBuffers, run_kernel
from tma2.sim.ranges import flatten_ranges, rows_for

ROOT = Path(__file__).resolve().parents[2]
RANGES = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())
R = flatten_ranges(RANGES)


def _run(cond: mm.Condition, n: int, seed: int = 320) -> list[dict[str, np.ndarray]]:
    buf = KernelBuffers.for_rows(rows_for(RANGES))
    out = []
    for i in range(n):
        run_kernel(np.uint64(seed), i, R, buf, cond)
        s = int(buf.TI[sc.TI_SAMPLES])
        out.append(
            {
                "bearing": buf.bearing[:s].copy(),
                "comp": buf.comp[:s].copy(),
                "eng": buf.eng.copy(),
                "sigma": np.array(buf.P[sc.P_SIGMA]),
            }
        )
    return out


def test_existing_conditions_are_byte_identical_to_0_7_0() -> None:
    """Digests made with the code before the second stream existed (bearing, components and
    engagement truth of the first 40 scenarios of seed 320, every Gate H condition)."""
    want = json.loads((ROOT / "tests/fixtures/mismatch/overlay-0.7.0-digests.json").read_text())
    conds = json.loads((ROOT / "configs/gateh/conditions.json").read_text())["conditions"]
    assert len(conds) == 16
    for c in conds:
        cond = mm.flatten_condition(c)
        assert cond.version == "0.7.0"
        h = hashlib.sha256()
        for r in _run(cond, 40):
            h.update(r["bearing"].tobytes())
            h.update(r["comp"].tobytes())
            h.update(r["eng"].tobytes())
        assert h.hexdigest() == want[c["id"]], c["id"]


def test_student_t_white_has_the_same_sd_and_heavier_tails() -> None:
    cond = mm.flatten_condition({"id": "t", "white_t_df": 3})
    assert cond.version == "0.8.0" and not cond.off
    z = np.concatenate([r["comp"][:, 0] / float(r["sigma"]) for r in _run(cond, 150)])
    assert abs(np.median(np.abs(z)) / 0.6745 - np.sqrt(1 / 3) * 1.134) < 0.05  # t3's MAD, scaled
    assert np.mean(np.abs(z) > 4.0) > 20 * 6.3e-5  # a Gaussian's share beyond 4 sd
    assert 0.7 < z.std() < 1.4


def test_level_step_scales_from_one_sample_on() -> None:
    cond = mm.flatten_condition({"id": "s", "sigma_step_factor": 2.0})
    base = mm.flatten_condition({"id": "c", "corr_tau_s": 60.0, "corr_share": 0.5})
    both = mm.flatten_condition(
        {"id": "cs", "corr_tau_s": 60.0, "corr_share": 0.5, "sigma_step_factor": 2.0}
    )
    ups = downs = 0
    for a, b in zip(_run(base, 30), _run(both, 30), strict=True):
        ratio = b["comp"][:, 1] / a["comp"][:, 1]  # the correlated part, same draws
        change = np.flatnonzero(~np.isclose(ratio, 1.0))
        if change.size == 0:
            continue
        first = int(change[0])
        assert np.allclose(ratio[:first], 1.0)
        f = float(ratio[first])
        assert np.allclose(ratio[first:], f) and (np.isclose(f, 2.0) or np.isclose(f, 0.5))
        ups += f > 1
        downs += f < 1
        assert np.allclose(b["comp"][:, 2], a["comp"][:, 2])  # bias untouched
    assert ups > 3 and downs > 3
    assert not np.array_equal(
        _run(cond, 1)[0]["bearing"], _run(mm.flatten_condition({"id": "off"}), 1)[0]["bearing"]
    )


def test_bad_fields_are_refused() -> None:
    for bad in ({"white_t_df": 2}, {"white_t_df": 3.5}, {"sigma_step_factor": 0.5}):
        with pytest.raises(ValueError):
            mm.flatten_condition({"id": "x", **bad})


def test_heldout_conditions_use_only_the_second_stream() -> None:
    doc = json.loads((ROOT / "configs/rmis/heldout-conditions.json").read_text())
    for c in doc["conditions"]:
        if c["id"] == "off":
            continue
        m = mm.flatten_condition(c).M
        assert np.all(np.isnan(m[: mm.M_T_DF])) and not np.all(np.isnan(m[mm.M_T_DF :]))
