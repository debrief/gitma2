"""Gate D checks and rules (spec 004 FR-029–FR-031)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from tma2.detect.matching import ScenarioDetection, score_scenario
from tma2.eval.gd import (
    G5Rows,
    GdCheck,
    Resampler,
    gate_result,
    validation_carries,
    variant_checks,
    variant_result,
)


def _meta(i: int) -> dict[str, Any]:
    return {
        "index": i,
        "samples": 200,
        "zig_index": 20,
        "parameters": {"dt_s": 10.0, "noise_sigma_rad": math.pi / 180},
        "manoeuvres": [{"kind": "course", "start_index": 100, "end_index": 106}],
    }


def _scores(
    delay_rows: int | None, false_rows: tuple[int, ...] = (), n: int = 40
) -> list[ScenarioDetection]:
    out = []
    for i in range(n):
        p = np.zeros(200)
        if delay_rows is not None and (i % 10 != 0 or delay_rows < 5):  # some misses when slow
            p[99 + delay_rows] = 1.0
        for r in false_rows:
            if i % 4 == 0:
                p[r] = 1.0
        out.append(score_scenario(_meta(i), {"p_change": p.tolist()}, "x"))
    return out


def _rows(det_err: float, n: int = 40) -> G5Rows:
    rng = np.random.default_rng(0)
    scen = np.repeat(np.arange(n), 4)
    settled = np.tile([True, True, False, True], n)
    base = {
        m: np.abs(rng.normal(1.0, 0.1, scen.size)) for m in ("range_rel", "course_deg", "speed_kt")
    }
    errs = {
        "least_squares": {m: 2.0 * v for m, v in base.items()},
        "imm": {m: 1.5 * v for m, v in base.items()},
        "oracle": {m: 0.5 * v for m, v in base.items()},
        "det-downstream": {m: det_err * v for m, v in base.items()},
    }
    return G5Rows(scenario=scen, settled=settled, errors=errs)


def test_a_clearly_better_detector_passes() -> None:
    det = _scores(2)
    ctl = {"cusum": _scores(8), "glr": _scores(6)}
    checks = variant_checks(det, ctl, _rows(1.0), "det-downstream", 0.05, 0.975, 200)
    by = {c.name: c for c in checks}
    assert by["D-delay"].result == "pass" and by["D-delay"].detail == "against glr"
    assert by["D-miss"].result == "pass"
    assert by["D-false"].result == "pass" and by["D-false"].value == 0.0
    assert by["D-downstream-all"].result == "pass"
    assert all(
        by[f"D-downstream-settled-{m}"].result == "pass" for m in ("range", "course", "speed")
    )
    assert math.isclose(by["D-gap"].value, (2.0 - 1.0) / (2.0 - 0.5), rel_tol=1e-6)
    assert variant_result(checks) == "pass" and validation_carries(checks)


def test_false_alarms_and_slow_detection_fail() -> None:
    det = _scores(8, false_rows=(50, 80))  # G5 rows 50 and 80 flagged in a quarter of scenarios
    ctl = {"cusum": _scores(2), "glr": _scores(3)}
    checks = variant_checks(det, ctl, _rows(1.8), "det-downstream", 0.05, 0.975, 200)
    by = {c.name: c for c in checks}
    assert by["D-delay"].result == "fail"
    assert by["D-false"].result == "fail"
    assert by["D-downstream-all"].result == "fail"  # 1.8 / 1.5
    assert variant_result(checks) == "fail" and not validation_carries(checks)


def test_gate_and_variant_rules() -> None:
    def chk(name: str, res: str) -> GdCheck:
        return GdCheck(name, res, 0.5, 0.4, 0.6, 1.0, 10)

    gated = ["D-delay", "D-miss", "D-false", "D-downstream-all"] + [
        f"D-downstream-settled-{m}" for m in ("range", "course", "speed")
    ]
    passing = [chk(n, "pass") for n in gated]
    unsure = [*passing[:-1], chk(gated[-1], "inconclusive")]
    failing = [*passing[:-1], chk(gated[-1], "fail")]
    assert variant_result(unsure) == "inconclusive" and variant_result(failing) == "fail"
    assert gate_result({"a": failing, "b": passing}) == "pass"
    assert gate_result({"a": failing, "b": unsure}) == "inconclusive"
    assert gate_result({"a": failing, "b": failing}) == "fail"
    assert validation_carries(unsure) and not validation_carries(failing)


def test_resampler_is_seeded() -> None:
    a = Resampler([1, 2, 3], 5)
    b = Resampler([1, 2, 3], 5)
    assert all(np.array_equal(x, y) for x, y in zip(a.picks, b.picks, strict=True))


def test_records_are_strict_json(tmp_path: Any) -> None:
    import json
    from pathlib import Path

    from tma2.eval.experiment import Check, Experiment

    root = Path(str(tmp_path))
    folder = root / "experiments" / "ci-strict-json"
    try:
        exp = Experiment(id="ci-strict-json", folder=folder, root=root)
        exp.checks.append(Check("D-delay", "fail", "n", value=math.inf, ci_low=math.inf))
        exp.metrics = {"a": math.nan, "b": [1.0, -math.inf]}
        exp.write("GD")
        for name in ("verdict.json", "metrics.json"):
            text = (folder / name).read_text()
            assert "Infinity" not in text and "NaN" not in text
            json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
        rec = json.loads((folder / "verdict.json").read_text())["checks"][0]
        assert "value" not in rec and "value = inf" in rec["detail"]
    finally:
        import shutil

        shutil.rmtree(folder, ignore_errors=True)
