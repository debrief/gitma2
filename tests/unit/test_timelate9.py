"""Spec 026: the carry across gaps and its readings."""

from __future__ import annotations

import numpy as np

from tma2.timelate.carry import Carried, carried_theta
from tma2.timelate.study9 import study_split9, verdict9


def test_carried_theta_runs_forward_at_constant_velocity() -> None:
    c = Carried(100.0, np.array([10.0, 20.0, 3.0, 4.0]))
    th = carried_theta(c, 300.0)
    assert np.allclose(th, [610.0, 820.0, np.arctan2(3.0, 4.0), 5.0])


def _arr() -> tuple[dict[str, np.ndarray], list[dict[str, object]]]:
    rng = np.random.default_rng(0)
    rows = []
    recs: list[dict[str, object]] = []
    for e in range(12):
        for p in range(2):
            for _ in range(4):
                rows.append((e, p))
        recs.append(
            {
                "ordinal": e,
                "layout": {"periods": [[0, 10], [20, 10]], "period_seconds": [[0, 50], [100, 150]]},
                "gaps": [{"length_s": 600.0, "true": 0, "declared": 0}],
                "own_turns": [1, 0],
                "joint_fell_back": [False, False],
                "alone": [[], []],
                "joint": [],
                "full": [],
                "carry": [{"fell_back": False}, {"fell_back": False}],
                "carry_first_max_diff": 0.0,
            }
        )
    eng = np.array([r[0] for r in rows])
    per = np.array([r[1] for r in rows], dtype=np.int8)
    n = eng.size

    def err(scale: float) -> np.ndarray:
        e = np.abs(rng.normal(scale, scale / 10, (n, 4)))
        return e

    arr = {
        "eng": eng,
        "period": per,
        "bound_span": np.full((n, 3), 0.01),
        "bound_own": np.full((n, 3), 0.01),
        "true_range": np.full(n, 1e4),
        "err_alone": err(0.4),
        "err_joint": err(0.1),
        "err_carry": err(0.2),
        "carry_first": per == 0,
    }
    for s in (
        "full",
        "c2",
        "one-leg",
        "ref-alone",
        "ref-span",
        "ref-alone-fixed",
        "ref-span-fixed",
    ):
        arr[f"err_{s}"] = err(0.1)
    return arr, recs


def test_study9_uses_later_periods_and_decides() -> None:
    arr, recs = _arr()
    r = study_split9(arr, recs)
    c = r["carry"]
    assert c["periods_scored"] == 12  # second periods only
    assert abs(c["ratios"]["carry/joint"]["range"]["value"] - 2.0) < 0.2
    assert abs(c["ratios"]["alone/carry"]["range"]["value"] - 2.0) < 0.2
    v = verdict9(r)
    assert v == {"carry_vs_joint": "joining better", "alone_vs_carry": "carrying helps"}
