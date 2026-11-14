"""Spec 017: detectability bands, the gap split and its verdict."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from tma2.timelate.study5 import detect_table, found_flags, gap_split, verdict


def test_found_flags_pair_each_true_manoeuvre_once() -> None:
    true = [[100.0, 200.0], [1000.0, 1100.0], [2000.0, 2100.0]]
    found = [[130.0, 210.0], [1900.0, 2050.0]]
    assert found_flags(true, found, 120.0) == [True, False, True]
    assert found_flags(true, [], 120.0) == [False, False, False]
    # one found manoeuvre cannot serve two true ones
    assert found_flags([[0.0, 100.0], [100.0, 200.0]], [[60.0, 140.0]], 120.0).count(True) == 1


def test_missed_share_by_detectability_band_ignores_cut_manoeuvres() -> None:
    periods = [
        {
            "true": [[100.0, 200.0], [1000.0, 1100.0], [1800.0, 1900.0]],
            "true_cut": [False, False, True],
            "detectability": [3.0, 150.0, 1.0],
            "histories": {"ctl": {"spans": [[1010.0, 1090.0]]}},
        },
        {
            "true": [[500.0, 600.0]],
            "true_cut": [False],
            "detectability": [30.0],
            "histories": {"ctl": {"spans": []}},
        },
    ]
    t = detect_table(periods, ["ctl"], [10.0, 20.0, 40.0], 120.0)
    assert t["manoeuvres"] == 3  # the cut one is not counted
    assert t["share_below"]["10"]["rate"] == 1 / 3 and t["share_below"]["40"]["rate"] == 2 / 3
    assert t["missed_by_band"]["0-5"]["ctl"]["rate"] == 1.0
    assert t["missed_by_band"]["20-40"]["ctl"]["rate"] == 1.0
    assert t["missed_by_band"]["100+"]["ctl"]["rate"] == 0.0
    assert t["missed_by_band"]["5-10"]["ctl"] is None


def test_the_gap_splits_into_an_attainable_share() -> None:
    n = 40
    full = np.full(n, 0.02)
    med = {"ctl": np.full(n, 0.08), "ref-full": full, "ref-d20": np.full(n, 0.04)}
    s = gap_split(med, "ctl", "ref-full", [20.0])["20"]
    assert math.isclose(s["share"], 0.5, rel_tol=1e-9)  # log 2 of log 4
    med["ref-d20"] = full.copy()  # nothing undetectable: the whole gap is attainable
    assert math.isclose(gap_split(med, "ctl", "ref-full", [20.0])["20"]["share"], 1.0)
    med["ref-d20"] = med["ctl"].copy()  # the control is at the detectable-only reference
    assert math.isclose(
        gap_split(med, "ctl", "ref-full", [20.0])["20"]["share"], 0.0, abs_tol=1e-12
    )
    assert gap_split(med, "ctl", "ref-full", [10.0]) == {}


def test_the_verdict_needs_an_interval_wholly_one_side_of_a_half() -> None:
    assert verdict({"share": 0.2, "lo": 0.1, "hi": 0.4}) == "mostly identifiability"
    assert verdict({"share": 0.8, "lo": 0.6, "hi": 0.9}) == "mostly attainable"
    assert verdict({"share": 0.45, "lo": 0.3, "hi": 0.6}) == "mixed"
    assert verdict(None) == "absent"


def _synthetic_split(
    n_periods: int = 12, rows: int = 20
) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    """Arrays and period records shaped as ``run_shard4`` writes them: the control at half
    the search's error, the reference at a quarter, C″ at twice."""
    rng = np.random.default_rng(5)
    period = np.repeat(np.arange(n_periods), rows)
    bound = np.full((period.size, 3), 0.03, dtype=np.float32)
    bound[::7, 0] = 0.9  # some rows undetermined: not scored
    base = rng.uniform(0.02, 0.2, size=n_periods)[period]

    def err(scale: float) -> np.ndarray:
        e = np.stack([base * scale, base * 40, base * 10, base * 2e4], axis=1)
        return e.astype(np.float32)

    arr: dict[str, np.ndarray] = {
        "period": period,
        "bound": bound,
        "stratum": np.zeros(period.size, dtype=np.int8),
        "true_range": np.full(period.size, 1.5e4, dtype=np.float32),
        "err_search3": err(1.0),
        "err_ctl": err(0.5),
        "err_c2": err(2.0),
        "err_history-best": err(0.25),
        "err_history-fixed": err(0.25),
    }
    periods: list[dict[str, Any]] = []
    for i in range(n_periods):
        true = [] if i % 3 == 0 else [[600.0, 700.0]]
        periods.append(
            {
                "ordinal": i,
                "true": true,
                "true_cut": [False] * len(true),
                "reference_flagged": i == 1,
                "history_converged": True,
                "corr_estimate": [0.0, 0.0],
                "ctl_corr_estimate": [0.0, 0.0, False],
                "edited": 0,
                "seconds": {"plain/v3": 10.0},
                "histories": {
                    "search3": {"spans": [[610.0, 690.0]]},  # a manoeuvre everywhere
                    "ctl": {"spans": true, "log_bayes_broad": -1.0},
                    "c2": {"spans": []},
                },
            }
        )
    return arr, periods


def test_the_control_s_readings_on_a_synthetic_split() -> None:
    from tma2.timelate.study4 import soundness4, study_split4

    arr, periods = _synthetic_split()
    plan = {
        "reference": {"sound": "history-fixed", "tight_bound": 0.05},
        "study": {
            "soundness_band": [0.8, 1.3],
            "convergence_min": 0.9,
            "reference_flagged_max": 0.25,
        },
    }
    r = study_split4(arr, periods, plan)
    assert r["periods"] == 12 and r["periods_scored"] == 12
    c = r["comparisons"]["search3_over_ctl"]
    assert math.isclose(c["geometric_mean"], 2.0, rel_tol=1e-5) and c["lo"] <= 2.0 <= c["hi"]
    assert math.isclose(
        r["comparisons"]["ctl_over_history-best"]["geometric_mean"], 2.0, rel_tol=1e-5
    )
    assert math.isclose(r["gap_closed"]["ctl"]["share"], 0.5, rel_tol=1e-5)  # log 2 of log 4
    # the search invents a manoeuvre on every quiet period, the control on none
    assert r["declares"]["search3"]["0"]["called_quiet"]["rate"] == 0.0
    assert r["declares"]["ctl"]["0"]["called_quiet"]["rate"] == 1.0
    assert r["declares"]["c2"]["1"]["called_quiet"]["rate"] == 1.0
    assert r["counts"]["ctl"]["120"]["missed"] == 0 and r["counts"]["c2"]["120"]["missed"] == 8
    assert math.isclose(r["reference_flagged_share"], 1 / 12)
    s = soundness4({"man2": r}, plan)
    assert s["reference_flagged_share"] <= 0.25 and s["history_converged_share"] == 1.0


def test_a_learned_track_needs_the_controls_validation_record(tmp_path: Path) -> None:
    import json

    import pytest

    from tma2.cli.tlscore import _require_controls_record

    with pytest.raises(SystemExit, match="required"):
        _require_controls_record(None, "abc")
    with pytest.raises(SystemExit, match="no controls"):
        _require_controls_record(str(tmp_path), "abc")
    rec: dict[str, Any] = {
        "plan_sha256": "other",
        "soundness": {"pass": True},
        "learned_scored": False,
    }
    (tmp_path / "summary.json").write_text(json.dumps(rec))
    with pytest.raises(SystemExit, match="another plan"):
        _require_controls_record(str(tmp_path), "abc")
    rec.update(plan_sha256="abc", soundness={"pass": False})
    (tmp_path / "summary.json").write_text(json.dumps(rec))
    with pytest.raises(SystemExit, match="soundness"):
        _require_controls_record(str(tmp_path), "abc")
    rec.update(soundness={"pass": True}, learned_scored=True)
    (tmp_path / "summary.json").write_text(json.dumps(rec))
    with pytest.raises(SystemExit, match="learned track was scored"):
        _require_controls_record(str(tmp_path), "abc")
    rec.update(learned_scored=False)
    (tmp_path / "summary.json").write_text(json.dumps(rec))
    with pytest.raises(SystemExit, match="not committed"):  # an untracked folder
        _require_controls_record(str(tmp_path), "abc")


def test_a_record_s_tables_are_what_the_script_prints_for_its_summary() -> None:
    import importlib.util
    import json

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "tl5_tables", root / "scripts/research/tl5_tables.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for t in sorted((root / "experiments").glob("*-tl5*/tables.md")):
        summary = json.loads((t.parent / "summary.json").read_text())
        assert t.read_text() == mod.tables(summary), t
