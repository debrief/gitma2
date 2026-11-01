"""The P0 physics-equals-least-squares check can fail (spec 003 FR-002, P0 panel round 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tma2.cli import p0
from tma2.eval.experiment import ROOT, Experiment
from tma2.physics.layer import PhysicsLayer

SMALL = (("phase4-seed777", "test"),)


def _run(layer: PhysicsLayer) -> str:
    exp = Experiment(id="t", folder=ROOT / "experiments" / "_test-p0-check")
    p0.check_physics_equals_ls(exp, layer=layer, sources=SMALL)
    return exp.checks[0].result


def test_passes_with_the_production_layer() -> None:
    assert _run(PhysicsLayer()) == "pass"


def test_fails_with_a_crippled_layer() -> None:
    # Five iterations from the grid start stop short on many rows: the cost test must catch it.
    assert _run(PhysicsLayer(iterations=5)) == "fail"


def test_experiment_folder_must_be_under_experiments(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        Experiment(id="x", folder=tmp_path / "x")
    with pytest.raises(ValueError):
        Experiment(id="x", folder=ROOT)
