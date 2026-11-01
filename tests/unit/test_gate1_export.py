"""Gate 1 model export (spec 003 FR-020, research R2): one ONNX graph whose physics iterations
are a single Loop, equal to torch in onnxruntime (Python) to 1e-5. K is small here; CI exports
K = 100 and runs the browser and Java legs too."""

from __future__ import annotations

import json
from pathlib import Path

import torch

from tma2.models.config import model_config
from tma2.models.export import FIXTURE, TOL, export, seeded_model
from tma2.sim.ranges import rows_for


def test_export_is_one_loop_and_matches_torch(tmp_path: Path) -> None:
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        model = seeded_model(model_config("g1-test", iterations=4), seed=3)
        r_max = rows_for(json.loads((FIXTURE / "ranges.json").read_text()))
        rec = export(model, tmp_path, r_max)
    finally:
        torch.set_default_dtype(default)
    assert rec["loop_nodes"] == 1
    assert "If" not in rec["ops"]
    assert all(v <= TOL for v in rec["max_rel_diff"].values()), rec["max_rel_diff"]
    assert rec["load_s"] < 60
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["model"] == "model.onnx"
    assert (tmp_path / "weights.safetensors").exists()
