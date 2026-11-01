"""Gate 1 scoring (spec 003 FR-020): rows, checks and their rules, on gitma's fixture rows."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.eval.errors import Truth
from tma2.eval.g1 import gate_rows, score
from tma2.eval.oracle_check import load_rows
from tma2.references.crb import crb_rows


def _setup() -> tuple[list[Truth], Any, Any, Any]:
    d = fixture_dir("iter4-seed777")
    blocks = list(iter_pack_raw(d / "test.f32pack"))
    truths = [Truth.from_block(m, own, tgt) for _, m, own, tgt, _ in blocks]
    bounds = {}
    for _, m, own, tgt, obs in blocks:
        t = Truth.from_block(m, own, tgt)
        ks = sorted({g.k for metric in ("range_rel", "speed_kt") for g in gate_rows([t], metric)})
        if ks:
            for k, b in zip(
                ks,
                crb_rows(
                    own,
                    tgt,
                    obs,
                    float(m["parameters"]["noise_sigma_rad"]),
                    int(m["zig_index"]),
                    None,
                    ks,
                    "full_window",
                ),
                strict=True,
            ):
                bounds[(t.index, k)] = b
    lsq = load_rows(str(d / "predictions" / "test-lsq.ndjson"))
    ekf = load_rows(str(d / "predictions" / "test-ekf.ndjson"))
    return truths, lsq, ekf, bounds


def test_gate_rows_are_sigma_1_at_the_gate_times() -> None:
    truths, *_ = _setup()
    rows = gate_rows(truths, "range_rel")
    by = {t.index: t for t in truths}
    assert rows
    for g in rows:
        t = by[g.index]
        assert abs(float(t.meta["parameters"]["noise_sigma_rad"]) - math.radians(1)) < 1e-6
        assert g.k == t.zig_index + 30
    assert len(gate_rows(truths, "speed_kt")) <= len(rows)


def test_least_squares_against_itself_passes_ratios_and_gross() -> None:
    truths, lsq, ekf, bounds = _setup()
    res = score(truths, lsq, lsq, bounds, {"ekf": ekf}, resamples=200)
    by = {c.name: c for c in res.checks}
    for name in ("ratio-range", "ratio-course", "ratio-speed", "gross"):
        assert by[name].result == "pass", by[name]
    assert by["ratio-range"].value == 1.0
    assert "ekf" in res.reported and "least_squares" in res.reported


def test_a_model_that_never_converges_fails() -> None:
    truths, lsq, _, bounds = _setup()
    res = score(truths, {}, lsq, bounds, {}, resamples=200)
    by = {c.name: c for c in res.checks}
    assert by["ratio-range"].result == "fail"
    assert res.result == "fail"
    assert np.isinf(by["ratio-range"].value)


def _decision(path: Any, plan_digest: str) -> None:
    import json

    from tma2.types import dump_record
    from tma2.types.generated.tma import Gate1Decision

    rec = Gate1Decision(
        plan_id="g1-smoke",
        plan_digest=plan_digest,
        carried_models=["smoke-physics"],
        control_models=["smoke-direct"],
        carried_rule="r",
        test_seed=303,
        test_count=100000,
        gate_rows="g",
        criterion="c",
        bootstrap_level=0.95,
        bootstrap_resamples=2000,
        imm="{}",
        ekf="{}",
        forecast="f",
        if_failed="i",
        validation_rule="v",
    )
    path.write_text(json.dumps(dump_record(rec)))


def test_g1_refuses_a_plan_other_than_the_decisions(tmp_path: Any) -> None:
    from tma2.cli.g1 import main

    dec = tmp_path / "decision.json"
    _decision(dec, "0" * 64)
    d = fixture_dir("iter4-seed777")
    args = [
        "--decision",
        str(dec),
        "--plan",
        "configs/gate1-smoke/plan.json",
        "--carried",
        "smoke-physics",
        "--model-meta",
        str(tmp_path / "meta.json"),
        "--test",
        str(d / "test.f32pack"),
        "--model",
        str(d / "predictions" / "test-lsq.ndjson"),
        "--least-squares",
        str(d / "predictions" / "test-lsq.ndjson"),
        "--experiment",
        "experiments/ci-g1-refusal",
    ]
    assert main(args) == 2
