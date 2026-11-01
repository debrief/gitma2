"""The export does not depend on the caller's default dtype (P0 round 2 crashed when the physics
checks had set it to double before the float32 export)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from tests.conftest import fixture_dir
from tma2.export.onnx_export import export


def test_export_is_independent_of_default_dtype(tmp_path: Path) -> None:
    pack = fixture_dir("phase4-seed777") / "test.f32pack"
    export(tmp_path / "a", pack, dtype="float32")
    before = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        export(tmp_path / "b", pack, dtype="float32")
    finally:
        torch.set_default_dtype(before)
    digest = [hashlib.sha256((tmp_path / d / "toy.onnx").read_bytes()).hexdigest() for d in "ab"]
    assert digest[0] == digest[1]


def test_double_export_loads_and_matches(tmp_path: Path) -> None:
    """The conformance artefact (double) loads in onnxruntime and matches torch (CI failure on
    the scripted Loop's scalar constants, spec 003)."""
    diffs = export(tmp_path / "f64", fixture_dir("phase4-seed777") / "test.f32pack")
    assert all(v <= 1e-5 for v in diffs.values()), diffs
