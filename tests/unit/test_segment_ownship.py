"""Spec 005 T022–T023: segmenter O (ownship legs) on constructed tracks (FR-014) and on MAN2
data (US4)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from tma2.data.f32pack import iter_pack_raw
from tma2.segment import STEADY, TRANSITION, default_parameters, to_codes
from tma2.segment import metrics as mx
from tma2.segment.ownship import changes, segment_ownship
from tma2.segment.truth import change_rows, truth_codes

P = default_parameters()
N = 360
SPEED = np.full(N, 6.0)


def _turn(
    course0: float, size_deg: float, at: int, rate_deg_s: float, dt: float = 10.0
) -> np.ndarray:
    """Course with a rate-limited turn of ``size_deg`` starting at row ``at``."""
    c = np.full(N, course0)
    step = math.radians(rate_deg_s) * dt * math.copysign(1.0, size_deg)
    rows = math.ceil(abs(size_deg) / (rate_deg_s * dt))
    for r in range(at, N):
        c[r] = course0 + (
            step * min(r - at + 1, rows) if r - at + 1 < rows else math.radians(size_deg)
        )
    return np.mod(c, 2 * math.pi)


def _wander(
    seed: int, sd_deg: float = 1.5, tau_s: float = 60.0, clip_deg: float = 4.0
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    a = math.exp(-10.0 / tau_s)
    x = np.zeros(N)
    for r in range(1, N):
        x[r] = a * x[r - 1] + math.sqrt(1 - a * a) * rng.normal() * math.radians(sd_deg)
    return np.clip(x, -math.radians(clip_deg), math.radians(clip_deg))


@pytest.mark.parametrize("seed", range(5))
def test_wander_and_oscillation_are_not_transitions(seed: int) -> None:
    c0 = math.radians(40.0)
    wander = c0 + _wander(seed)
    t = np.arange(N) * 10.0
    rng = np.random.default_rng(100 + seed)
    amp = math.radians(rng.uniform(1.0, 3.0))
    per = rng.uniform(120.0, 360.0)
    osc = c0 + amp * np.sin(2 * math.pi * t / per + rng.uniform(0, 2 * math.pi))
    for c in (wander, osc):
        assert changes(c, SPEED, P) == []
        assert segment_ownship(c, SPEED, N - 1, P)[0].kind == STEADY


@pytest.mark.parametrize(
    "size,rate", [(12.0, 0.5), (-15.0, 3.0), (30.0, 1.0), (-30.0, 0.5), (90.0, 2.0)]
)
def test_turns_found(size: float, rate: float) -> None:
    c = _turn(math.radians(100.0), size, 150, rate) + _wander(7) * 0.5
    ch = changes(c, SPEED, P)
    assert len(ch) == 1, ch
    a, b, is_open = ch[0]
    rows = math.ceil(abs(size) / (rate * 10.0))
    assert not is_open
    assert abs(a - 150) <= 3 and abs(b - (150 + rows - 1)) <= 3, (a, b, rows)
    ivs = segment_ownship(c, SPEED, N - 1, P)
    assert [iv.kind for iv in ivs] == [STEADY, TRANSITION, STEADY]


def test_wrap_across_north() -> None:
    c = np.mod(math.radians(359.0) + _wander(3), 2 * math.pi)
    assert changes(c, SPEED, P) == []
    turned = _turn(math.radians(355.0), 20.0, 150, 1.0)  # 355° → 15°
    assert len(changes(turned, SPEED, P)) == 1


def test_open_turn_at_prefix_end() -> None:
    c = _turn(math.radians(100.0), 40.0, 150, 0.5)
    ivs = segment_ownship(c, SPEED, 156, P)
    assert ivs[-1].kind == TRANSITION and ivs[-1].open


def test_man2_ownship(man2_pack: Path) -> None:
    """On MAN2 ownship tracks (wander, oscillation, one or two turns), every turn is found within
    ± 3 rows (30 s) of truth before trimming, nothing else is called, and contamination of O's
    legs against the truth labels is 0."""
    worst = 0.0
    for _, m, own, _tgt, _obs in iter_pack_raw(man2_pack):
        n = int(m["samples"])
        ch = changes(own[:, 3], own[:, 4], P)
        truth = change_rows(m, "ownship")
        pred = [(a, b) for a, b, _ in ch]
        assert len(pred) == len(truth), (m["index"], truth, pred)
        assert all(mx.boundary_hits(pred, truth, 3)), (m["index"], truth, pred)
        ivs = segment_ownship(own[:, 3], own[:, 4], n - 1, P)
        tc = truth_codes(m, "ownship", P.l_min_rows, P.t_min_rows)
        worst = max(worst, mx.contamination(to_codes(ivs, n), tc))
    assert worst == 0.0
