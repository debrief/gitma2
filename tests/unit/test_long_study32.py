"""Spec 032: the scorer's reading rule and its behaviour with nothing to read."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from tma2.long.study32 import _ratio, _read


def test_reading_rule() -> None:
    assert _read({"interval": [1.01, 2.0]}) == "ctl-prior better"
    assert _read({"interval": [0.5, 0.99]}) == "ctl-prior worse"
    assert _read({"interval": [0.9, 1.1]}) == "not separated"
    assert _read({"interval": [math.nan, math.nan]}) == "not separated"


def test_ratio_shares() -> None:
    units = [np.log(np.array([2.0, 0.5, 4.0])), np.log(np.array([1.5]))]
    r = _ratio(units)
    assert r["windows"] == 4 and r["engagements"] == 2
    assert math.isclose(r["share_prior_better"], 0.75)
    assert math.isclose(r["share_twice_prior_better"], 0.5)
    assert math.isclose(r["share_twice_prior_worse"], 0.25)
    assert math.isclose(r["median"], 1.75)


def test_empty_raw_fails_s1(tmp_path: Path) -> None:
    from tma2.long.study32 import score32

    cfg = Path(__file__).resolve().parents[2] / "configs/long/legs-tuning.json"
    res = score32(tmp_path, cfg)
    s1 = res["soundness"]["S1_parts_present"]
    assert not s1["pass"] and s1["missing"] == {"a": 12, "c": 12}
    assert res["counts"]["held_decided"] == 0
