"""tma2-gd end to end on fixture data (spec 004 FR-029–FR-031), bindings mocked."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import fixture_dir
from tests.unit.test_detector_train import _plan, _train_in_process
from tma2.types import dump_record, parse_record
from tma2.types.generated.tma import CheckpointMeta, GateDDecision

D = fixture_dir("phase4-seed777")
TRUTH = D / "test.f32pack"
LSQ = D / "predictions" / "test-lsq.ndjson"
IMM = D / "predictions" / "test-imm.ndjson"


def decision(**over: Any) -> GateDDecision:
    base: dict[str, Any] = {
        "plan_id": "det-plan",
        "plan_digest": "0" * 64,
        "carried_variants": ["det-test"],
        "control_models": ["gd-cls"],
        "carried_rule": "median seed",
        "threshold": 0.5,
        "tolerance_s": 60.0,
        "knot_threshold": 0.5,
        "bootstrap_level": 0.975,
        "bootstrap_resamples": 100,
        "false_alarm_limit_rule": "5% or the IMM's",
        "false_alarm_limit": 0.05,
        "validation_seed": 304,
        "test_seed": 305,
        "test_count": 100000,
        "held_leg_weight": 3.0,
        "controls_rule": "matched",
        "imm": "imm",
        "ekf": "ekf",
        "criterion": "Annex A §A.5",
        "validation_rule": "Annex A §A.5",
        "follow_on": "Annex A §A.6",
        "forecast": "f",
        "architecture_check": "a",
    }
    return GateDDecision(**{**base, **over})


def test_tma2_gd_scores_fixture_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import tma2.cli.gd as gd
    from tma2.cli.controls import main as controls
    from tma2.cli.detect import downstream_main
    from tma2.cli.detect import main as detect
    from tma2.cli.oracle import predict_split as oracle_predict

    plan = _plan(tmp_path)
    ck = tmp_path / "ck"
    _train_in_process(plan, ck, 1)
    det = tmp_path / "det.ndjson"
    args = ["--plan", str(plan), "--model", "det-test", "--checkpoint", str(ck)]
    assert detect([*args, "--truth", str(TRUTH), "--out", str(det)]) == 0
    down = tmp_path / "down.ndjson"
    assert downstream_main(["--detector", str(det), "--truth", str(TRUTH), "--out", str(down)]) == 0
    ctl = []
    amend: dict[str, Any] = {"controls": []}
    for kind in ("cusum", "glr"):
        st = tmp_path / f"{kind}.json"
        assert (
            controls(
                ["tune", "--kind", kind, "--validation", str(TRUTH), "--least-squares", str(LSQ)]
                + ["--target-far", "0.05", "--out", str(st)]
            )
            == 0
        )
        amend["controls"].append(json.loads(st.read_text()))
        out = tmp_path / f"{kind}.ndjson"
        run = ["run", "--settings", str(st), "--truth", str(TRUTH), "--least-squares", str(LSQ)]
        assert controls([*run, "--out", str(out)]) == 0
        ctl.append(f"{kind}={out}")
    (tmp_path / "amendment.json").write_text(json.dumps(amend))
    oracle = tmp_path / "oracle.ndjson"
    oracle_predict(str(TRUTH), str(oracle), True, False, 100, 8)
    meta = parse_record(CheckpointMeta, json.loads((ck / "meta.json").read_text()), "m", 1)
    monkeypatch.setattr(gd, "check_inputs", lambda a: (decision(), {"det-test": meta}))
    folder = Path("experiments/ci-gd-e2e")
    try:
        dec = tmp_path / "decision.json"
        dec.write_text(json.dumps(dump_record(decision())))
        cmd = ["--decision", str(dec), "--plan", str(plan), "--split", "test"]
        cmd += ["--truth", str(TRUTH), "--variant", f"det-test={ck / 'meta.json'},{det},{down}"]
        for c in ctl:
            cmd += ["--control", c]
        cmd += ["--least-squares", str(LSQ), "--imm", str(IMM), "--oracle", str(oracle)]
        cmd += ["--amendment", str(tmp_path / "amendment.json"), "--experiment", str(folder)]
        rc = gd.main(cmd)
        assert rc in (0, 3)
        verdict = json.loads((folder / "verdict.json").read_text())
        names = {c["name"] for c in verdict["checks"]}
        assert {f"det-test:{n}" for n in gd.GATED} <= names
        assert verdict["gate"] == "GD" and verdict["result"] in ("pass", "fail", "inconclusive")
        metrics = json.loads((folder / "metrics.json").read_text())
        assert set(metrics["reported"]["controls"]) == {"cusum", "glr"}
        assert "det-test-downstream" in metrics["reported"]["downstream_medians"]
        assert (folder / "detections-det-test.ndjson").exists()
        manifest = json.loads((folder / "manifest.json").read_text())
        assert manifest["amendments"][0]["digest"]
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def test_tma2_gd_refuses_a_plan_other_than_the_decisions(tmp_path: Path) -> None:
    from tma2.cli.gd import main

    dec = tmp_path / "decision.json"
    dec.write_text(json.dumps(dump_record(decision())))
    plan = _plan(tmp_path)
    args = ["--decision", str(dec), "--plan", str(plan), "--split", "test", "--truth", str(TRUTH)]
    args += ["--variant", "det-test=a,b,c", "--control", "cusum=x", "--control", "glr=y"]
    args += ["--least-squares", str(LSQ), "--imm", str(IMM), "--oracle", str(LSQ)]
    assert main([*args, "--experiment", "experiments/ci-gd-refusal"]) == 2
