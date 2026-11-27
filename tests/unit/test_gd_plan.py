"""Spec 038: the scoring plans are built from the protocol, and every name a plan's readings
use is one of that plan's own runs or checkpoints (spec 037's first validation launch read
systems that did not exist)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from tma2.headroom.edit import Edit
from tma2.segment.robust import RobustConfirm

ROOT = Path(__file__).resolve().parents[2]


def _mod() -> Any:
    spec = importlib.util.spec_from_file_location("gd_plan", ROOT / "scripts/research/gd_plan.py")
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _proto(**kw: Any) -> dict[str, Any]:
    return {**json.loads((ROOT / "configs/gd/protocol.json").read_text()), **kw}


CHOSEN = {
    "threshold": 2,
    "edit": "wild",
    "own_prior_weight": 1,
    "combined": True,
    "threshold_neighbours": [1.5, 3],
    "own_prior_weight_neighbours": [0.5, 2],
}


@pytest.mark.parametrize("stage", ["dev-a", "dev-b", "test"])
def test_names_are_the_plans_own(stage: str) -> None:
    proto = _proto(chosen=CHOSEN)
    runs, decomp = _mod().runs_for(proto, stage)
    names = [r["name"] for r in runs]
    assert len(names) == len(set(names))
    cks = {c["name"] for c in proto["checkpoints"]}
    assert set(decomp["regressors"]) | set(decomp["unchanged"]) | {decomp["own"]} <= cks
    assert not cks & set(names)
    for key in ("comparator", "own_hybrid", "true", "segments"):
        assert decomp[key] in names
    assert set(decomp["hardened"]) | set(decomp["hybrids"]) <= set(names)
    for r in runs:
        if r["kind"] == "hybrid":
            assert r["prior_from"] in cks
        if "edit" in r:
            Edit(**r["edit"])
        if "robust_confirm" in r:
            assert r["segmentation"] == "c2r"
            RobustConfirm(**r["robust_confirm"])
    if stage == "test":  # the chosen settings only
        assert {r["name"] for r in runs} >= {"c2-thr", "c2-edit", "c2-edit-thr", "own-hyb"}
        assert not any("w0.5" in n or "thr1.5" in n for n in names)


def test_later_stages_need_a_choice() -> None:
    with pytest.raises(SystemExit):
        _mod().runs_for(_proto(chosen=None), "test")


def test_splits_and_seeds() -> None:
    proto = _proto()
    seeds = [s["seed"] for s in proto["stages"].values()]
    assert seeds == [321, 370, 372]
    for st in proto["stages"].values():
        for split in st["splits"]:
            assert (ROOT / proto["splits"][split]["ranges"]).exists()
