"""Spec 005 T037: Gate S's refusals and its pass / fail / inconclusive logic (FR-071)."""

from __future__ import annotations

import json
from pathlib import Path

from tma2.segment import gate
from tma2.segment.gate import FAIL, INCONCLUSIVE, PASS, Interval

PLAN = {"evidence_network": {"width": 32, "kernel": 5, "dilations": [1, 2, 4, 8]}}
DEC = {"plan_digest": "p" * 64, "validation_digest": "v" * 64}


def test_above_zero() -> None:
    assert gate.above_zero(Interval(0.1, 0.02, 0.2)) == PASS
    assert gate.above_zero(Interval(0.1, -0.01, 0.2)) == INCONCLUSIVE
    assert gate.above_zero(Interval(-0.1, -0.2, 0.0)) == FAIL
    assert gate.above_zero(Interval(0.0, 0.0, 0.0)) == FAIL


def test_within_limit_and_all_of() -> None:
    assert gate.within_limit(Interval(0.0, -0.01, 0.01), 0.01) == PASS
    assert gate.within_limit(Interval(0.0, -0.01, 0.02), 0.01) == INCONCLUSIVE
    assert gate.within_limit(Interval(0.03, 0.02, 0.04), 0.01) == FAIL
    assert gate.all_of([PASS, PASS]) == PASS
    assert gate.all_of([PASS, INCONCLUSIVE]) == INCONCLUSIVE
    assert gate.all_of([INCONCLUSIVE, FAIL]) == FAIL


def test_s4_and_reference() -> None:
    win = Interval(0.02, 0.01, 0.03)
    assert gate.s4_verdict(win, PASS) == PASS
    assert gate.s4_verdict(win, FAIL) == FAIL  # a control that beats C voids the claim
    assert gate.s4_verdict(Interval(0.0, -0.01, 0.01), FAIL) == INCONCLUSIVE
    assert gate.reference(PASS, 0.5, 0.9) == "C"
    assert gate.reference(INCONCLUSIVE, 0.5, 0.9) == "glr_confirm"
    assert gate.reference(FAIL, 0.9, 0.5) == "C"


def _ok(**over: object) -> list[str]:
    params = "a" * 64
    weights = "w" * 64
    headers = {
        "C": {"dataset_digest": "t" * 64, "segmenter_sha256": params, "git_dirty": False},
        "L": {
            "dataset_digest": "t" * 64,
            "segmenter_sha256": gate.expected_l_sha(params, weights, PLAN),
            "git_dirty": False,
        },
    }
    kw: dict[str, object] = {
        "decision": DEC,
        "plan_sha": "p" * 64,
        "split": "test",
        "truth_sha": "t" * 64,
        "test_digest": "t" * 64,
        "headers": headers,
        "params_sha": params,
        "carried": {"weights_sha256": weights},
        "plan": PLAN,
    }
    kw.update(over)
    return gate.check_inputs(**kw)  # type: ignore[arg-type]


def test_refusals() -> None:
    assert _ok() == []
    assert any("plan" in e for e in _ok(plan_sha="x" * 64))
    assert any("test split" in e for e in _ok(truth_sha="x" * 64))
    assert any("seed315" in e for e in _ok(test_digest=None))
    assert any("validation" in e for e in _ok(split="validation"))
    assert any("carried" in e for e in _ok(carried=None))
    assert any("carried weights" in e for e in _ok(carried={"weights_sha256": "z" * 64}))
    assert any("parameters" in e for e in _ok(params_sha="b" * 64))
    h = {"C": {"dataset_digest": "t" * 64, "segmenter_sha256": "a" * 64, "git_dirty": True}}
    errs = _ok(headers=h)
    assert any("no segmentation named L" in e for e in errs)
    assert any("dirty" in e for e in errs)


def test_amendments_list_every_other_file(tmp_path: Path) -> None:
    (tmp_path / "decision.json").write_text("{}")
    (tmp_path / "README.md").write_text("x")
    (tmp_path / "carried.json").write_text(json.dumps({"weights_sha256": "w"}))
    (tmp_path / "seed315-digests.json").write_text("{}")
    am = gate.amendments(tmp_path)
    assert [x["file"] for x in am] == ["carried.json", "seed315-digests.json"]
    assert all(len(x["sha256"]) == 64 for x in am)


def test_no_rows_is_inconclusive() -> None:
    """A criterion with nothing to measure neither passes nor fails (Gate S panel round 1)."""
    nan = float("nan")
    assert gate.within_limit(gate.Interval(nan, nan, nan), 0.05) == gate.INCONCLUSIVE
    assert gate.above_zero(gate.Interval(nan, nan, nan)) == gate.INCONCLUSIVE
