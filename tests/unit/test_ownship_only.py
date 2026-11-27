"""Spec 038 FR-010 (research R3): which bearings reach the ownship-only regressor's rows.

It reads no bearing feature, but the first valid bearing sets its frame and the last valid one
at or before the row gives the direction its range is laid along. With those two held, no other
bearing changes anything; the full model, by contrast, moves.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from tma2.references.classical import bearing_data_from_arrays
from tma2.regress.model import Regressor, RegressorConfig
from tma2.regress.predict import predict_scenarios
from tma2.segment import score as sc

ROOT = Path(__file__).resolve().parents[2]
TOY = dict(id="t", layers=1, width=16, heads=2, feedforward=32, batch_scenarios=8,
           total_updates=3, warmup_updates=1, val_count=8, val_every_updates=3,
           precision="float32", ranges=str(ROOT / "configs/man2-ranges.json"))  # fmt: skip
KEYS = ("range_m", "course_rad", "speed_mps", "x_m", "y_m", "sd_log_range", "sd_speed_mps")


def _rows(inputs: str, man2_pack: Path) -> tuple[list[list[float]], list[list[float]]]:
    torch.manual_seed(1)
    model = Regressor(RegressorConfig(**{**TOY, "inputs": inputs})).eval()  # type: ignore[arg-type]
    with torch.no_grad():  # the output head starts at zero: give every weight a value
        for w in model.parameters():
            w.normal_(0.0, 0.2)
    rng = np.random.default_rng(2)
    base: list[list[float]] = []
    moved: list[list[float]] = []
    for _j, m, own, _tgt, obs in sc.iter_selected(man2_pack, 0, 3):
        d = bearing_data_from_arrays(m, own, obs)
        ks = sc.g5_rows(m, d.n)[-1:]
        if not ks:
            continue
        k = ks[0]
        v = np.flatnonzero(d.valid[: k + 1] > 0)
        z = d.z.copy()
        mid = v[1:-1]  # every valid bearing but the first and the last at or before k
        z[mid] = z[mid] + rng.normal(0.0, 0.2, mid.size)
        for dd, out in ((d, base), (replace(d, z=z), moved)):
            (rows,) = predict_scenarios(model, [dd], [ks])
            out.append([float(rows[0][key]) for key in KEYS])
    assert base
    return base, moved


def test_ownship_only_ignores_all_but_two_bearings(man2_pack: Path) -> None:
    base, moved = _rows("ownship_only", man2_pack)
    assert base == moved


def test_full_model_reads_the_bearings(man2_pack: Path) -> None:
    base, moved = _rows("full", man2_pack)
    assert base != moved
