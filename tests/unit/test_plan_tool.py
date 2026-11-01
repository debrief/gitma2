"""``tma2-plan`` (spec 003 T017): plan resolution by branch and the completeness check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tma2.cli.plan_tool import find_plan, main


def test_resolves_the_plan_named_by_the_branch(tmp_path: Path) -> None:
    for name, pid in (("a", "g1-a"), ("b", "g1-b")):
        (tmp_path / "configs" / name).mkdir(parents=True)
        (tmp_path / "configs" / name / "plan.json").write_text(json.dumps({"id": pid}))
    assert find_plan("train/g1-b", tmp_path) == Path("configs/b/plan.json")
    with pytest.raises(ValueError):
        find_plan("train/g1-missing", tmp_path)


def test_committed_smoke_plan_resolves() -> None:
    assert find_plan("train/g1-smoke", Path.cwd()) == Path("configs/gate1-smoke/plan.json")


def test_complete_reads_the_checkpoint_meta(tmp_path: Path) -> None:
    assert main(["complete", "--checkpoint", str(tmp_path)]) == 1
    meta = {
        "model_id": "m",
        "plan_id": "p",
        "plan_digest": "d",
        "epoch": 1,
        "best_epoch": 1,
        "best_val_loss": 1.0,
        "complete": False,
    }
    (tmp_path / "meta.json").write_text(json.dumps(meta))
    assert main(["complete", "--checkpoint", str(tmp_path)]) == 1
    (tmp_path / "meta.json").write_text(json.dumps({**meta, "complete": True}))
    assert main(["complete", "--checkpoint", str(tmp_path)]) == 0
    (tmp_path / "meta.json").write_text(json.dumps({"complete": True}))  # not a CheckpointMeta
    assert main(["complete", "--checkpoint", str(tmp_path)]) == 2
