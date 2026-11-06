"""tma2-g2 end to end on three fixture scenarios (spec 007 T023): untrained E-w scored beside C
on the same segmentation recovers the same gap (E − C = 0); validation mode writes the rule;
the gate refuses inputs that are not the decision's."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import torch

from tests.unit.test_gate2_predict import ENCODER, _params
from tma2.cli.g2 import criteria
from tma2.cli.g2 import main as g2_main
from tma2.gate2.model import EWeights
from tma2.gate2.predict import e_rows
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment import STEADY, TRANSITION, Interval
from tma2.segment.codeid import code_digest
from tma2.segment.gate import sha256_file
from tma2.segment.score import g5_rows, iter_selected
from tma2.types.generated.tma import Gate2Decision, PhysicsModelConfig, SegmentParameters

IMM = "imm-cv0.03-ct1-w0.01-s0.0003-p4-r2"
N = 3


def _decision(plan_sha: str, val_sha: str, p: SegmentParameters, psha: str) -> dict[str, Any]:
    return Gate2Decision(
        plan_id="t",
        plan_digest=plan_sha,
        validation_seed=316,
        validation_digest=val_sha,
        train_seed=318,
        test_seed=319,
        test_count=10,
        c_parameters=p,
        c_parameters_sha256=psha,
        c_code_sha256=code_digest(),
        knots=12,
        imm=IMM,
        ekf="-",
        glr_confirm="-",
        g2a_limit=1.0,
        g2b_limit=1.1,
        g2c_limit=0.5,
        bootstrap_level=0.975,
        bootstrap_resamples=2000,
        carried_rule="median",
        shuffled_rule="not wholly above zero",
        validation_rule="every point",
        rescore="not taken",
        criterion="SRD §5",
        follow_on="-",
        forecast="-",
    ).model_dump(mode="json", exclude_none=True)


@pytest.fixture(scope="module")
def files(man2_pack: Path, tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    tmp = tmp_path_factory.mktemp("g2")
    p = _params()
    truth_sha = sha256_file(man2_pack)
    data, rows, segs, recs = [], [], [], []
    for j, m, own, _tgt, obs in iter_selected(man2_pack, 0, N):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        z = int(m["zig_index"])
        sg = {}
        for q, k in enumerate(ks):
            ivs = (
                [Interval(STEADY, 0, z - 1), Interval(TRANSITION, z, k, True)]
                if q == 1 and k - z < 30
                else [Interval(STEADY, 0, k)]
            )
            sg[k] = ivs
            recs.append(
                {
                    "ordinal": j,
                    "prefix_row": k,
                    "intervals": [
                        {
                            "kind": ("steady", "transition", "unknown")[iv.kind],
                            "start_index": iv.start,
                            "end_index": iv.end,
                            "open": iv.open,
                        }
                        for iv in ivs
                    ],
                }
            )
        data.append((j, m, d))
        rows.append(ks)
        segs.append(sg)
    psha = "c" * 64
    plan = {
        "c": {"parameters_sha256": psha, "code_sha256": code_digest(), "mode": p.mode},
        "models": {"ew-s1": {"kind": "ew", "seed": 1}},
    }
    (tmp / "plan.json").write_text(json.dumps(plan))
    plan_sha = sha256_file(tmp / "plan.json")
    head = {
        "record": "header",
        "schema_version": "0.25.0",
        "segmenter": "C",
        "segmenter_sha256": psha,
        "dataset_digest": truth_sha,
        "parameters": json.loads(p.model_dump_json(exclude_none=True)),
        "git_commit": "x",
        "git_dirty": False,
        "code_sha256": code_digest(),
    }
    with open(tmp / "c.ndjson", "w") as f:
        f.write(json.dumps(head) + "\n")
        for r in recs:
            f.write(json.dumps(r) + "\n")
    model = EWeights(PhysicsModelConfig.model_validate(ENCODER)).double()
    out = e_rows(model, [d for _, _, d in data], rows, segs, p.mode, p.open_handover)
    ph = {
        "record": "header",
        "model": "ew-s1",
        "weights_sha256": "w" * 64,
        "plan_sha256": plan_sha,
        "dataset_digest": truth_sha,
        "parameters_sha256": psha,
        "code_sha256": code_digest(),
        "git_commit": "x",
        "git_dirty": False,
    }
    with open(tmp / "e.ndjson", "w") as f:
        f.write(json.dumps(ph) + "\n")
        for (j, m, _), rs in zip(data, out, strict=True):
            f.write(json.dumps({"ordinal": j, "scenario_index": m["index"], "rows": rs}) + "\n")
    (tmp / "dec").mkdir()
    (tmp / "dec" / "decision.json").write_text(json.dumps(_decision(plan_sha, truth_sha, p, psha)))
    return {"tmp": tmp, "truth": str(man2_pack)}


def _args(f: dict[str, Any], exp: str) -> list[str]:
    t = f["tmp"]
    return [
        "--truth",
        f["truth"],
        "--start",
        "0",
        "--count",
        str(N),
        "--c",
        str(t / "c.ndjson"),
        "--e",
        f"ew-s1={t / 'e.ndjson'}",
        "--imm",
        IMM,
        "--experiment",
        str(t / exp),
    ]


def test_scoring_untrained_e_is_c(files: dict[str, Any]) -> None:
    assert g2_main(_args(files, "s")) == 0
    m = json.loads((files["tmp"] / "s" / "metrics.json").read_text())
    assert m["knots"] == 12
    e = m["segmenters"]["ew-s1"]
    assert e["all"]["range_median"] == pytest.approx(
        m["segmenters"]["C"]["all"]["range_median"], rel=1e-9
    )
    d = e["gap_minus"]["C"]["range"]
    assert abs(d["value"]) < 1e-9 and abs(d["lo"]) < 1e-9  # hi: 3 scenarios, may be undefined
    dec = Gate2Decision.model_validate_json((files["tmp"] / "dec" / "decision.json").read_text())
    c = criteria(e, dec, "pass")
    assert c["g2d"] != "pass" and not c["validation_rule"]


def test_validation_mode_and_refusals(files: dict[str, Any]) -> None:
    t = files["tmp"]
    gate = ["--decision", str(t / "dec" / "decision.json"), "--plan", str(t / "plan.json")]
    assert g2_main([*_args(files, "v"), *gate, "--split", "validation"]) == 0
    v = json.loads((t / "v" / "validation.json").read_text())
    assert v["estimators"]["ew-s1"]["validation_rule"] is False
    (t / "other.json").write_text("{}")
    bad = ["--decision", str(t / "dec" / "decision.json"), "--plan", str(t / "other.json")]
    assert g2_main([*_args(files, "r"), *bad, "--split", "validation"]) == 2
    assert g2_main([*_args(files, "r2"), *gate, "--split", "test", "--model", "ew-s1"]) == 2
    assert not (t / "r").exists() and not (t / "r2").exists()
