"""Steady-leg segmentation (spec 005, SRD Annex B): segmenters O (ownship), C (classical target)
and L (learned), their truth labels, metrics and the hand-over to the physics layer.

A segmentation of a prefix [0, k] is a list of intervals (steady, transition, unknown) that tiles
the prefix. Rows are inclusive sample indices. Internally intervals are ``(kind, start, end,
open)`` tuples and per-row labels are ``int8`` codes ``STEADY``, ``TRANSITION``, ``UNKNOWN``.
"""

from __future__ import annotations

import math
from typing import NamedTuple

import numpy as np

from tma2.types.generated.tma import SegmentKind, SegmentMode, SegmentParameters

STEADY = 0
TRANSITION = 1
UNKNOWN = 2

KIND_CODE = {
    SegmentKind.steady: STEADY,
    SegmentKind.transition: TRANSITION,
    SegmentKind.unknown: UNKNOWN,
}
CODE_KIND = {v: k for k, v in KIND_CODE.items()}


class Interval(NamedTuple):
    kind: int
    start: int
    end: int  # inclusive
    open: bool = False


def default_parameters(**overrides: object) -> SegmentParameters:
    """Annex B's defaults and the MAN2 re-plan's (data-model.md). ``search_penalty``, ``margin``,
    ``mode`` and ``glr_threshold`` (∞: no GLR nominations) are placeholders until validation
    measurements and the decision record fix them."""
    base: dict[str, object] = {
        "course_tol_deg": 5.0,
        "speed_tol_kt": 0.5,
        "course_change_deg": 10.0,
        "speed_change_kt": 1.0,
        "l_min_rows": 30,
        "t_min_rows": 6,
        "t_lengths_rows": [6, 9, 12, 18, 24, 36],
        "search_penalty": 0.0,
        "nominator_far": 0.2,
        "retest_rows": 6,
        "tau": 13.8,
        "margin": 0.0,
        "mode": SegmentMode.chord,
        "glr_threshold": math.inf,
        "glr_window": 30,
        "window_rows": 36,
        "candidate_step_rows": 3,
        "search_every_rows": 30,
        "search_step_rows": 6,
        "search_horizon_rows": 18,
        "polish_rows": 3,
    }
    base.update(overrides)
    return SegmentParameters.model_validate(base)


class SegmentationError(ValueError):
    """A segmentation that does not tile its prefix or breaks a length rule."""


def validate(intervals: list[Interval], k: int, l_min: int, t_min: int) -> None:
    """Check that ``intervals`` tile [0, k] in order without overlap; that steady intervals are at
    least ``l_min`` rows and transitions at least ``t_min`` rows unless open; and that only the
    last interval may be open (and only a transition)."""
    if not intervals:
        raise SegmentationError("no intervals")
    nxt = 0
    for i, iv in enumerate(intervals):
        if iv.kind not in (STEADY, TRANSITION, UNKNOWN):
            raise SegmentationError(f"interval {i}: unknown kind {iv.kind}")
        if iv.start != nxt:
            raise SegmentationError(f"interval {i} starts at {iv.start}, expected {nxt}")
        if iv.end < iv.start:
            raise SegmentationError(f"interval {i} ends before it starts ({iv.start}, {iv.end})")
        length = iv.end - iv.start + 1
        last = i == len(intervals) - 1
        if iv.open and (not last or iv.kind != TRANSITION):
            raise SegmentationError(f"interval {i}: only a last transition may be open")
        if iv.kind == STEADY and length < l_min:
            raise SegmentationError(f"interval {i}: steady leg of {length} rows < L_min {l_min}")
        if iv.kind == TRANSITION and not iv.open and length < t_min:
            raise SegmentationError(f"interval {i}: transition of {length} rows < T_min {t_min}")
        nxt = iv.end + 1
    if nxt != k + 1:
        raise SegmentationError(f"intervals end at row {nxt - 1}, prefix is [0, {k}]")


def to_codes(intervals: list[Interval], n: int) -> np.ndarray:
    """Per-row codes for rows 0 … n − 1 (rows past the last interval are UNKNOWN)."""
    out = np.full(n, UNKNOWN, dtype=np.int8)
    for iv in intervals:
        out[iv.start : min(iv.end, n - 1) + 1] = iv.kind
    return out


def from_codes(codes: np.ndarray) -> list[Interval]:
    """Runs of equal codes as intervals (none open)."""
    out: list[Interval] = []
    n = int(codes.shape[0])
    s = 0
    for r in range(1, n + 1):
        if r == n or codes[r] != codes[s]:
            out.append(Interval(int(codes[s]), s, r - 1))
            s = r
    return out


def transitions(intervals: list[Interval]) -> list[tuple[int, int]]:
    """(start, end) of each transition interval, inclusive."""
    return [(iv.start, iv.end) for iv in intervals if iv.kind == TRANSITION]
