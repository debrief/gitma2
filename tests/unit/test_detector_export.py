"""The detector exports alone and onnxruntime reproduces it (spec 004 FR-033)."""

from __future__ import annotations

from pathlib import Path

import torch

from tests.unit.test_detector import config
from tma2.models.detector_export import TOL, export, seeded_detector
from tma2.types.generated.tma import DetectorVariant


def test_export_python_leg(tmp_path: Path) -> None:
    default = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        for v in (DetectorVariant.causal, DetectorVariant.time_late):
            model = seeded_detector(config(v), 3)
            rec = export(model, tmp_path / v.value, 360)
            assert all(d <= TOL for d in rec["max_rel_diff"].values()), rec["max_rel_diff"]
            assert "Loop" not in rec["ops"] and "If" not in rec["ops"]
    finally:
        torch.set_default_dtype(default)
