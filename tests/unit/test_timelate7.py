"""Spec 019: the ladder of priors and the concentration of a gain."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.run7 import ORDER, PARTS, ladder, with_parts
from tma2.timelate.study7 import concentration

ROOT = Path(__file__).resolve().parents[2]


def _prior(name: str) -> ManoeuvrePrior:
    return ManoeuvrePrior.from_ranges(
        json.loads((ROOT / f"configs/timelate/{name}.json").read_text()), 3
    )


def test_the_ladder_runs_from_the_broadened_prior_to_the_true_one() -> None:
    base, true = _prior("tl-broad"), _prior("tl-shift-ranges")
    rungs = ladder(base, true)
    assert sorted(rungs) == [
        "lad-0", "lad-1", "lad-2", "lad-3", "lad-4", "lad-5",
        "one-angle", "one-kinds", "one-rate", "one-speed",
    ]  # fmt: skip
    assert rungs["lad-0"] == base
    assert rungs["lad-5"] == true  # every part taken: nothing else differs between them
    assert rungs["lad-1"].leg_mean == true.leg_mean and rungs["lad-1"].angle == base.angle
    assert rungs["lad-2"].angle == true.angle and rungs["lad-2"].turn_rate == base.turn_rate
    one = rungs["one-speed"]
    assert one.dv == true.dv and one.acc == true.acc
    assert one.leg_mean == base.leg_mean and one.angle == base.angle and one.w_both == base.w_both
    # every field of the prior that differs between the two belongs to exactly one part
    named = [f for p in ORDER for f in PARTS[p]]
    assert len(named) == len(set(named))
    differs = {f for f in vars(base) if getattr(base, f) != getattr(true, f)}
    assert differs <= set(named)
    assert with_parts(base, true, ()) == base


def test_concentration_of_a_gain_in_its_best_periods() -> None:
    a = np.full(40, 0.04)
    b = np.full(40, 0.04)
    b[:5] = 0.01  # the whole gain is in five periods
    c = concentration(a, b, top=10)
    assert math.isclose(c["share_in_top"], 1.0) and math.isclose(c["ratio_without_top"], 1.0)
    b = np.full(40, 0.02)  # an even gain: a quarter of it in a quarter of the periods
    c = concentration(a, b, top=10)
    assert math.isclose(c["share_in_top"], 0.25) and math.isclose(c["ratio_without_top"], 2.0)
