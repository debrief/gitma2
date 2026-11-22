"""Spec 037 research R6: the paired readings."""

import math

import numpy as np

from tma2.regress import mread


def _errs(
    ratio: float, n: int = 300, rows: int = 4, seed: int = 1
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    rng = np.random.default_rng(seed)
    ordinal = np.repeat(np.arange(n), rows)
    base = np.exp(rng.normal(-2.5, 0.8, (n * rows, 3)))
    sys = base * np.exp(rng.normal(0.0, 0.5, base.shape))
    ctl = base * ratio * np.exp(rng.normal(0.0, 0.5, base.shape))
    return {"ctl": ctl, "sys": sys}, ordinal


def test_a_planted_ratio_is_recovered() -> None:
    errs, ordinal = _errs(1.5)
    r = mread.paired(errs, "ctl", ["sys"], ordinal, resamples=500)["range"]["sys"]
    assert r["outcome"] == "better" and r["lo"] < 1.5 < r["hi"]
    assert r["share_better"] > 0.6 and r["scenarios"] == 300


def test_a_true_ratio_of_one_is_not_separated() -> None:
    errs, ordinal = _errs(1.0, seed=3)
    r = mread.paired(errs, "ctl", ["sys"], ordinal, resamples=500)["range"]["sys"]
    assert r["outcome"] == "not separated"


def test_unanswered_rows_and_scenarios_are_left_out_and_counted() -> None:
    errs, ordinal = _errs(1.2, n=50)
    errs["sys"][ordinal == 0] = np.inf  # the system answers nothing on scenario 0
    errs["ctl"][1] = np.inf  # one row lost elsewhere
    ids, _lr, left = mread.scenario_log_ratio(errs["ctl"][:, 0], errs["sys"][:, 0], ordinal)
    assert left == 1 and 0 not in ids.tolist() and ids.size == 49
    s = mread.system_summary(errs["sys"], ordinal, None)
    assert abs(s["answered"] - 49 / 50) < 1e-12


def test_pooled_systems_average_the_log_ratios() -> None:
    errs, ordinal = _errs(2.0, n=80)
    errs["sys2"] = errs["sys"] * 4.0  # control ÷ sys2 = 0.5
    r = mread.paired(errs, "ctl", ["sys", "sys2"], ordinal, resamples=200)["range"]
    assert (
        abs(
            math.log(r["pooled"]["ratio"])
            - 0.5 * (math.log(r["sys"]["ratio"]) + math.log(r["sys2"]["ratio"]))
        )
        < 1e-9
    )


def test_coverage_of_an_honest_statement() -> None:
    rng = np.random.default_rng(5)
    n, rows = 400, 4
    ordinal = np.repeat(np.arange(n), rows)
    sd = 0.2
    d = np.abs(rng.normal(0.0, sd, n * rows))
    hit = (d <= mread.Z95 * sd).astype(float)
    hit[:10] = np.nan  # rows that state nothing
    c = mread.coverage(hit, d / sd, ordinal, resamples=500)
    assert c["lo"] < 0.95 < c["hi"] and abs(c["normalised_error_median"] - 1.0) < 0.08
    assert c["rows"] == n * rows - 10


def test_interval_rows_reads_the_stated_fields() -> None:
    ordinal, ks = np.array([0, 0]), np.array([10, 20])
    e = np.array([[0.1, 10.0, 2.0], [0.1, 10.0, 2.0]])
    true_range = np.array([10_000.0, 10_000.0])
    stated = {
        (0, 10): {
            "range_m": 11_000.0,
            "range_ratio_q95": 0.2,
            "course_arc_rad": 0.1,
            "speed_q95_mps": 2.0,
        },
        (0, 20): {"range_m": 11_000.0, "range_ratio_q95": 0.05, "speed_q95_mps": 0.5},
    }
    hz = mread.interval_rows(stated, ordinal, ks, e, true_range)
    assert hz["range"][0].tolist() == [1.0, 0.0]
    assert hz["course_deg"][0][0] == 0.0 and math.isnan(hz["course_deg"][0][1])  # 10° > 0.1 rad
    assert hz["speed_kt"][0].tolist() == [1.0, 0.0]  # 2 kt = 1.03 m/s
