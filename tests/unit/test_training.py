"""Training resumes to the same result (spec 003 FR-015, SC-005)."""

from __future__ import annotations

import json
from pathlib import Path

from safetensors.torch import load_file

from tests.conftest import fixture_dir
from tma2.data.io import file_digest
from tma2.models.config import model_config
from tma2.models.train import train
from tma2.types import dump_record
from tma2.types.generated.tma import DatasetRef, TrainingPlan


def _plan(tmp: Path) -> Path:
    d = fixture_dir("iter4-seed777")
    import json as _j

    hdr = _j.loads((d / "test.ndjson").read_text().split("\n")[0])
    cfg = model_config(
        "t1", iterations=20, batch_scenarios=8, epochs=2, patience=5, threads=2, rows_per_scenario=2
    )
    plan = TrainingPlan(
        id="test-plan",
        ranges=hdr["parameter_ranges"],
        train_seed=99,
        scenarios_per_epoch=16,
        validation=DatasetRef(
            path=str(d / "validation.f32pack"),
            header=hdr,
            digest=file_digest(d / "validation.f32pack"),
        ),
        validation_scenarios=10,
        models=[cfg],
        decision="none",
    )
    p = tmp / "plan.json"
    p.write_text(json.dumps(dump_record(plan)))
    return p


def test_resumed_run_equals_uninterrupted(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    data = fixture_dir("iter4-seed777")
    a, b = tmp_path / "a", tmp_path / "b"
    train(plan, "t1", a, data, epochs=2, log=lambda _: None)
    train(plan, "t1", b, data, epochs=1, log=lambda _: None)  # stops after one epoch
    meta = train(plan, "t1", b, data, epochs=2, log=lambda _: None)  # resumes
    assert meta.epoch == 2 and len(meta.jobs or []) == 2
    wa, wb = load_file(str(a / "weights.safetensors")), load_file(str(b / "weights.safetensors"))
    assert wa.keys() == wb.keys()
    assert all(bool((wa[k] == wb[k]).all()) for k in wa)


def test_predictions_score_with_the_evaluation_tools(tmp_path: Path) -> None:
    """tma2-predict output is gitma's prediction format: it binds to the truth file and every
    scenario has a row at every post-zig timestep."""
    from tma2.eval.predictions import check_bound, iter_predictions_raw
    from tma2.models.predict import load_model, predict_split

    plan = _plan(tmp_path)
    data = fixture_dir("iter4-seed777")
    ck = tmp_path / "ck"
    train(plan, "t1", ck, data, epochs=1, log=lambda _: None)
    model = load_model(plan, "t1", ck)
    out = tmp_path / "pred.ndjson"
    truth = data / "test.f32pack"
    predict_split(model, truth, out, log=lambda _: None)
    check_bound(out, truth)
    from tma2.data.f32pack import iter_pack_raw

    zig = {
        int(m["index"]): (int(m["zig_index"]), int(m["samples"]))
        for _, m, *_ in iter_pack_raw(truth)
    }
    n = 0
    for _, p in iter_predictions_raw(out):
        z, s = zig[int(p["scenario_index"])]
        assert len(p["rows"]) == s - z - 1
        n += 1
    assert n == len(zig)
