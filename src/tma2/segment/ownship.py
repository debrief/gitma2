"""Segmenter O: ownship steady legs from the recorded track (spec 005 FR-010–FR-014, SRD Annex B
FR-001–FR-006, research R5).

O sees only the recorded course and speed, never helm orders.
1. **Coarse pass.** Adjacent non-overlapping moving averages of ``window`` rows (1 min) of the
   unwrapped course are compared at every row; a row is flagged when they differ by more than D
   (``course_change_deg``). The same test on speed uses D_S (``speed_change_kt``). Runs of
   flagged rows are candidate changes.
2. **Fine pass.** From the candidate's steepest row turning in its direction, walk back to the
   turn's start: the first row (walking back) where the smoothed turn rate (3-row central
   difference) no longer has the turn's sign, or the course sits inside the preceding leg's
   ± C band. Walk forward the same way
   for the end, against the following leg's band: the end is declared ``window`` rows later than
   it happened, since the following leg's mean needs them.
3. **Signed-change test.** A course change is accepted only if its net change across the
   transition is at least ``net_fraction`` (90%) of the total absolute change between its ends,
   and the leg means either side differ by at least D: wander of
   ± C with no persistent direction is not a transition, irregular or cyclic.
4. **Legs.** Transitions are widened to T_min and merged; a steady piece is a leg if it is at
   least L_min long and every sample lies within ± C and ± S of its mean, else unknown.
   ``trim_rows`` (30 s) are then moved from each leg end next to a transition into the transition.

On a prefix [0, k] only rows ≤ k are used; a change whose end is not yet declared is an open
transition.
"""

from __future__ import annotations

import math

import numpy as np

from tma2.types.generated.tma import SegmentParameters

from . import STEADY, TRANSITION, UNKNOWN, Interval, from_codes

KT = 1852.0 / 3600.0  # m/s per knot
WINDOW = 6  # 1 min at 10 s
NET_FRACTION = 0.9
TRIM_ROWS = 3  # 30 s


def _ma(x: np.ndarray, w: int) -> tuple[np.ndarray, np.ndarray]:
    """(before, after): before[r] = mean x[r − w + 1 … r], after[r] = mean x[r + 1 … r + w]; NaN
    where the window leaves the array."""
    n = x.shape[0]
    cs = np.concatenate([[0.0], np.cumsum(x)])
    before = np.full(n, np.nan)
    after = np.full(n, np.nan)
    for r in range(w - 1, n):
        before[r] = (cs[r + 1] - cs[r + 1 - w]) / w
    for r in range(0, n - w):
        after[r] = (cs[r + 1 + w] - cs[r + 1]) / w
    return before, after


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    out = []
    r, n = 0, mask.shape[0]
    while r < n:
        if mask[r]:
            a = r
            while r < n and mask[r]:
                r += 1
            out.append((a, r - 1))
        else:
            r += 1
    return out


def changes(
    course: np.ndarray,
    speed: np.ndarray,
    p: SegmentParameters,
    window: int = WINDOW,
    net_fraction: float = NET_FRACTION,
) -> list[tuple[int, int, bool]]:
    """Accepted changes as (start, end, open) rows, before widening and trimming. ``open``: the
    end is not yet declared (it lies within ``window`` rows of the last row)."""
    n = course.shape[0]
    u = np.unwrap(course.astype(np.float64))
    d_c = math.radians(p.course_change_deg)
    band_c = math.radians(p.course_tol_deg)
    bc, ac = _ma(u, window)
    bs, as_ = _ma(speed.astype(np.float64), window)
    with np.errstate(invalid="ignore"):
        flag_c = np.abs(ac - bc) > d_c
        flag_s = np.abs(as_ - bs) > p.speed_change_kt * KT
    rate = np.zeros(n)
    rate[1:-1] = (u[2:] - u[:-2]) / 2.0
    out: list[tuple[int, int, bool]] = []
    for f0, f1 in _runs(flag_c):
        peak = f0 + int(np.argmax(np.abs(ac[f0 : f1 + 1] - bc[f0 : f1 + 1])))
        sgn = 1.0 if ac[peak] - bc[peak] > 0 else -1.0
        # the walk starts at the steepest row turning that way, near the coarse peak
        lo_s, hi_s = max(1, f0 - window), min(n - 2, f1 + window)
        mid = lo_s + int(np.argmax(rate[lo_s : hi_s + 1] * sgn))
        lo = max(0, f0 - window + 1)
        m_before = float(np.mean(u[max(0, lo - window) : lo])) if lo > 0 else float(u[0])
        a = mid
        while a > 0 and rate[a] * sgn > 0 and abs(u[a] - m_before) > band_c:
            a -= 1
        a += 1 if a < mid else 0
        hi = f1 + window
        is_open = hi + window > n
        m_after = float(np.mean(u[hi : hi + window])) if not is_open else float(u[-1])
        b = mid
        while b < n - 1 and rate[b] * sgn > 0 and abs(u[b] - m_after) > band_c:
            b += 1
        b -= 1 if b > mid else 0
        if is_open:
            b = n - 1
        # net and total change between the legs either side (the rows just outside it)
        r0, r1 = max(a - 1, 0), min(b + 1, n - 1)
        net = u[r1] - u[r0]
        total = float(np.sum(np.abs(np.diff(u[r0 : r1 + 1]))))
        # D applies to the change of leg means (the coarse test's quantity); the signed test
        # to the rows across the transition
        if abs(m_after - m_before) < d_c or (total > 0 and abs(net) < net_fraction * total):
            continue
        out.append((a, b, is_open))
    for f0, f1 in _runs(flag_s):
        a = max(0, (f0 + f1) // 2 - window // 2)
        b = min(n - 1, a + window - 1)
        is_open = f1 + 2 * window > n
        out.append((a, n - 1 if is_open else b, is_open))
    out.sort()
    merged: list[tuple[int, int, bool]] = []
    for a, b, o in out:
        if merged and a <= merged[-1][1] + 1:
            pa, pb, po = merged[-1]
            merged[-1] = (pa, max(pb, b), po or o)
        else:
            merged.append((a, b, o))
    return merged


def segment_ownship(
    course: np.ndarray,
    speed: np.ndarray,
    k: int,
    p: SegmentParameters,
    trim_rows: int = TRIM_ROWS,
) -> list[Interval]:
    """O on the prefix [0, k]."""
    c = course[: k + 1]
    s = speed[: k + 1]
    n = k + 1
    codes = np.full(n, STEADY, dtype=np.int8)
    open_last = False
    for a, b, o in changes(c, s, p):
        short = p.t_min_rows - (b - a + 1)
        if short > 0 and not o:
            a -= short // 2
            b += short - short // 2
        a, b = max(a, 0), min(b, n - 1)
        codes[a : b + 1] = TRANSITION
        open_last = open_last or (o and b == n - 1)
    # trim each leg end next to a transition
    for iv in from_codes(codes):
        if iv.kind != STEADY:
            continue
        a, b = iv.start, iv.end
        if a > 0 and codes[a - 1] == TRANSITION:
            codes[a : min(a + trim_rows, b + 1)] = TRANSITION
        if b < n - 1 and codes[b + 1] == TRANSITION:
            codes[max(b - trim_rows + 1, a) : b + 1] = TRANSITION
    u = np.unwrap(c.astype(np.float64))
    band_c = math.radians(p.course_tol_deg)
    band_s = p.speed_tol_kt * KT
    for iv in from_codes(codes):
        if iv.kind != STEADY:
            continue
        seg_u = u[iv.start : iv.end + 1]
        seg_s = s[iv.start : iv.end + 1]
        bad = (
            iv.end - iv.start + 1 < p.l_min_rows
            or np.max(np.abs(seg_u - seg_u.mean())) > band_c
            or np.max(np.abs(seg_s - seg_s.mean())) > band_s
        )
        if bad:
            codes[iv.start : iv.end + 1] = UNKNOWN
    ivs = from_codes(codes)
    if open_last and ivs[-1].kind == TRANSITION:
        ivs[-1] = Interval(TRANSITION, ivs[-1].start, ivs[-1].end, True)
    return ivs
