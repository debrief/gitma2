"""Reference estimators reproduce gitma's prediction files (spec 002 FR-001/002, SC-001).

Rule: the row count and every ``converged`` flag are identical; on rows where both converged,
range, speed, position and course agree to 1e-4 relative (course as an angle difference).
Iterative estimators stop on a knife-edge (1e-12 relative cost change), so a last-bit libm
difference can shift the stopping iteration and move the optimum by ~1e-7 relative; the worst
observed is 1.6e-5 on one least-squares row. The maximum is printed for the record.
"""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pytest

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.references.classical import bearing_data_from_arrays, classical_predict
from tma2.references.ekf import ekf_predict
from tma2.references.imm import ImmParams, imm_predict

FROZEN_IMM = ImmParams(0.01, 0.03, 0.01, 0.001, 4.0, 8.0)
REL_TOL = 1e-4


def _load(path: Any) -> tuple[str, dict[int, dict[str, Any]]]:
    out: dict[int, dict[str, Any]] = {}
    with open(path, encoding="utf-8") as f:
        header = json.loads(f.readline())
        for line in f:
            p = json.loads(line)
            out[p["scenario_index"]] = p
    return header["estimator"], out


def _predict(est: str, d: Any) -> dict[str, Any]:
    if est == "lsq":
        return classical_predict(d, "per_timestep")
    if est == "ekf":
        return ekf_predict(d, 0.03, 4.0, 8.0)
    return imm_predict(d, FROZEN_IMM)


@pytest.mark.parametrize("name", ["iter4-seed777", "phase4-seed777"])
@pytest.mark.parametrize("split", ["test", "validation"])
@pytest.mark.parametrize("est", ["lsq", "ekf", "imm"])
def test_estimator_matches_gitma(
    name: str, split: str, est: str, capsys: pytest.CaptureFixture[str]
) -> None:
    estimator_name, theirs = _load(fixture_dir(name) / "predictions" / f"{split}-{est}.ndjson")
    worst = 0.0
    rows = 0
    for _, meta, own, _tgt, obs in iter_pack_raw(fixture_dir(name) / f"{split}.f32pack"):
        d = bearing_data_from_arrays(meta, own, obs)
        mine = _predict(est, d)
        assert mine["estimator"] == estimator_name
        ref = theirs[meta["index"]]
        assert len(mine["rows"]) == len(ref["rows"]), f"scenario {meta['index']}: row count"
        for a, b in zip(mine["rows"], ref["rows"], strict=True):
            rows += 1
            assert a["timestamp_s"] == b["timestamp_s"]
            assert a["converged"] == b["converged"], (
                f"scenario {meta['index']} t={a['timestamp_s']}"
            )
            if not a["converged"]:
                continue
            for k in ("range_m", "speed_mps", "x_m", "y_m"):
                r = abs(a[k] - b[k]) / max(abs(b[k]), 1.0)
                worst = max(worst, r)
                assert r <= REL_TOL, (
                    f"scenario {meta['index']} t={a['timestamp_s']} {k}: {a[k]} vs {b[k]}"
                )
            dc = abs(
                math.atan2(
                    math.sin(a["course_rad"] - b["course_rad"]),
                    math.cos(a["course_rad"] - b["course_rad"]),
                )
            )
            worst = max(worst, dc)
            assert dc <= REL_TOL
    with capsys.disabled():
        print(
            f"\nreference {name}/{split}/{est}: rows={rows} worst relative difference={worst:.1e}"
        )


def test_noise_free_recovery() -> None:
    """gitma's G0 check 1: final-mode least squares recovers noise-free truth within 0.1% range."""
    import tempfile
    from pathlib import Path

    from tests.conftest import fixture_ranges
    from tma2.data.dataset import GenerateOptions, generate_dataset
    from tma2.sim.ranges import noise_free

    ranges, heldout = fixture_ranges("iter4-seed777")
    d = Path(tempfile.mkdtemp())
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(42),
            count=100,
            out_dir=d,
            ranges=noise_free(ranges),
            heldout_ranges=noise_free(heldout),
            format="f32pack",
            created_by="t",
            generator_git_commit="t",
            generator_git_dirty=True,
        )
    )
    worst = 0.0
    for _, meta, own, tgt, obs in iter_pack_raw(d / "train.f32pack"):
        bd = bearing_data_from_arrays(meta, own, obs)
        p = classical_predict(bd, "final")
        row = p["rows"][-1]
        i = int(meta["samples"]) - 1
        true_range = math.hypot(tgt[i, 1] - own[i, 1], tgt[i, 2] - own[i, 2])
        assert row["converged"], meta["index"]
        worst = max(worst, abs(row["range_m"] - true_range) / true_range)
    assert worst < 1e-3, worst
