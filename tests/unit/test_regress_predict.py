"""Spec 012 T006: the regressor's prediction file is read by the existing scorer."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from tma2.eval.errors import Truth
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment import score as sc

ROOT = Path(__file__).resolve().parents[2]


def test_scorer_reads_regressor_rows(man2_pack: Path, tmp_path: Path) -> None:
    cfg = dict(id="t", layers=1, width=16, heads=2, feedforward=32, batch_scenarios=8,
               total_updates=3, warmup_updates=1, val_count=8, val_every_updates=3,
               precision="float32", ranges=str(ROOT / "configs/man2-ranges.json"))  # fmt: skip
    (tmp_path / "c.json").write_text(json.dumps(cfg))
    py = [sys.executable, "-m"]
    subprocess.run(
        [*py, "tma2.cli.rtrain", "--config", str(tmp_path / "c.json"), "--out", str(tmp_path)],
        check=True, cwd=ROOT, capture_output=True,
    )  # fmt: skip
    pred = tmp_path / "pred.ndjson"
    subprocess.run(
        [*py, "tma2.cli.rpredict", "--weights", str(tmp_path / "checkpoint.safetensors"),
         "--config", str(tmp_path / "c.json"), "--in", str(man2_pack), "--out", str(pred),
         "--count", "6", "--name", "reg-t"],
        check=True, cwd=ROOT, capture_output=True,
    )  # fmt: skip
    rows, data, truths = [], {}, {}
    for j, m, own, tgt, obs in sc.iter_selected(man2_pack, 0, 6):
        d = bearing_data_from_arrays(m, own, obs)
        data[j], truths[j] = d, Truth.from_block(m, own, tgt)
        rows += [sc.Row(j, k, False) for k in sc.g5_rows(m, d.n)]
    assert rows
    e = sc.prediction_errors(rows, data, truths, pred)
    assert e.shape == (len(rows), 3) and np.isfinite(e).all()
    assert (e[:, 0] > 0).all() and (e[:, 2] < 60).all()  # an untrained model: finite, not good
