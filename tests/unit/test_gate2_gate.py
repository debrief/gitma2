"""Gate 2's verdicts (spec 007 T022): G2-a…G2-d, the shuffled rule and the validation rule."""

from __future__ import annotations

import math

from tma2.gate2.gate import (
    FAIL,
    INCONCLUSIVE,
    PASS,
    above,
    below,
    g2a,
    g2b,
    g2c,
    g2d,
    shuffled_rule,
    validation_rule,
)
from tma2.segment.gate import Interval

NAN = Interval(math.nan, math.nan, math.nan)


def iv(v: float, lo: float, hi: float) -> Interval:
    return Interval(v, lo, hi)


def test_below_and_above() -> None:
    assert below(iv(0.8, 0.7, 0.9), 1.0) == PASS
    assert below(iv(0.9, 0.8, 1.0), 1.0) == INCONCLUSIVE  # the bound touches: not wholly below
    assert below(iv(1.2, 1.0, 1.4), 1.0) == FAIL
    assert above(iv(0.7, 0.6, 0.8), 0.5) == PASS
    assert above(iv(0.6, 0.5, 0.7), 0.5) == INCONCLUSIVE
    assert above(iv(0.4, 0.3, 0.5), 0.5) == FAIL
    assert below(NAN, 1.0) == INCONCLUSIVE and above(NAN, 0.0) == INCONCLUSIVE  # no rows


def test_g2a_g2b_g2c() -> None:
    good, edge, bad = iv(0.8, 0.7, 0.9), iv(0.95, 0.9, 1.05), iv(1.1, 1.05, 1.2)
    assert g2a({"range": good, "course_deg": good}, 1.0) == PASS
    assert g2a({"range": good, "course_deg": edge}, 1.0) == INCONCLUSIVE
    assert g2a({"range": bad, "course_deg": good}, 1.0) == FAIL
    s = {"range": good, "course_deg": good, "speed_kt": iv(1.05, 1.0, 1.09)}
    assert g2b(s, 1.1) == PASS
    assert g2b(s | {"speed_kt": iv(1.2, 1.12, 1.3)}, 1.1) == FAIL
    assert g2b(s | {"speed_kt": NAN}, 1.1) == INCONCLUSIVE
    assert g2c(iv(0.9, 0.85, 0.93), 0.5) == PASS and g2c(iv(0.4, 0.3, 0.45), 0.5) == FAIL


def test_g2d_and_shuffled_rule() -> None:
    win = iv(0.02, 0.005, 0.035)
    assert shuffled_rule(iv(0.001, -0.004, 0.006)) == PASS
    assert shuffled_rule(iv(0.01, 0.002, 0.02)) == FAIL  # the control beats C
    assert g2d(win, PASS) == PASS
    assert g2d(win, FAIL) == FAIL  # void: recorded as not passed
    assert g2d(iv(0.001, -0.003, 0.005), PASS) == INCONCLUSIVE
    assert g2d(iv(-0.01, -0.02, -0.001), PASS) == FAIL
    assert g2d(NAN, PASS) == INCONCLUSIVE


def test_validation_rule() -> None:
    limits = {"g2a_range": ("below", 1.0), "g2c": ("above", 0.5), "g2d": ("above", 0.0)}
    assert validation_rule({"g2a_range": 0.9, "g2c": 0.8, "g2d": 0.01}, limits)
    assert not validation_rule({"g2a_range": 0.9, "g2c": 0.8, "g2d": 0.0}, limits)
    assert not validation_rule({"g2a_range": math.nan, "g2c": 0.8, "g2d": 0.01}, limits)
