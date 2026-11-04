"""Detector targets from the stored manoeuvre spans (spec 004 FR-011; research R3).

Spans are ``Batch.spans`` rows (kind, start_index, end_index), padded with −1. A span's
manoeuvre begins at row start − 1 and ends at row end (the first sample after it), so both
``start`` and ``end`` are boundaries: the rows at which the target's motion stops being the
previous leg's and starts being the next one's.

* ``now[k] = 1`` when a span is in progress at k (start ≤ k < end) or began within the last
  ``now_window_s`` (0 ≤ k − start < now_window_s / dt).
* ``boundary[j]`` = max over boundaries r of the triangular kernel max(0, 1 − |j − r| / h),
  h = ``tolerance_s`` / dt (D1: ±60 s), capped at 1. The pairwise target at a scored row k is
  ``w_target[k, j]`` = the same maximum over the boundaries r ≤ k only, for j ≤ k (0 for j > k):
  a boundary that has not happened yet is not a target.
* ``kind[k, j]`` = 1 for a course change, 0 for a speed change: the kind of the nearest boundary
  r ≤ k (ties: course), weighted by ``w_target[k, j]`` (so only rows near a boundary count).
* ``held[k]``: no manoeuvre in progress and none ended within 300 s (``eval.rows.settled_row``,
  Annex C §C.5), so rows before the first manoeuvre are held; ``settled[k]``: held, after at least
  one completed manoeuvre.

All functions are plain NumPy over padded batch arrays (rows beyond ``samples`` are zero).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tma2.eval.rows import G5_SETTLE_S
from tma2.features.batch import is_turn_kind

NOW_WINDOW_S = 60.0
TOLERANCE_S = 60.0


@dataclass
class RowLabels:
    now: np.ndarray  # [B, R] float64 in {0, 1}
    boundary: np.ndarray  # [B, R] float64 in [0, 1], all boundaries
    held: np.ndarray  # [B, R] bool
    settled: np.ndarray  # [B, R] bool
    valid_row: np.ndarray  # [B, R] bool (k < samples)


@dataclass
class PairLabels:
    w_target: np.ndarray  # [B, N, R] in [0, 1]; 0 for j > k
    kind: np.ndarray  # [B, N, R] in {0, 1}
    kind_weight: np.ndarray  # [B, N, R] in [0, 1]


def _boundaries(spans: np.ndarray) -> list[list[tuple[int, int]]]:
    """Per scenario: (row, kind) for every span start and end."""
    out: list[list[tuple[int, int]]] = []
    for sp in spans:
        cur: list[tuple[int, int]] = []
        for kind, start, end in sp:
            if start < 0:
                continue
            cur.append((int(start), int(kind)))
            cur.append((int(end), int(kind)))
        out.append(cur)
    return out


def _tri(rows: np.ndarray, r: int, half: float) -> np.ndarray:
    return np.clip(1.0 - np.abs(rows - r) / half, 0.0, 1.0)


def row_labels(
    spans: np.ndarray,
    samples: np.ndarray,
    dt: np.ndarray,
    rows: int,
    now_window_s: float = NOW_WINDOW_S,
    tolerance_s: float = TOLERANCE_S,
) -> RowLabels:
    """Per-row targets for a batch: spans [B, M, 3], samples [B], dt [B] (s), rows R."""
    b = spans.shape[0]
    idx = np.arange(rows, dtype=np.int64)
    now = np.zeros((b, rows))
    boundary = np.zeros((b, rows))
    held = np.ones((b, rows), dtype=bool)
    after = np.zeros((b, rows), dtype=bool)
    valid_row = idx[None, :] < samples[:, None]
    for i in range(b):
        win = now_window_s / float(dt[i])
        half = tolerance_s / float(dt[i])
        settle = G5_SETTLE_S / float(dt[i])
        for _kind, start, end in spans[i]:
            if start < 0:
                continue
            s, e = int(start), int(end)
            in_span = (idx >= s) & (idx < e)
            recent = (idx >= s) & (idx - s < win)
            now[i, in_span | recent] = 1.0
            boundary[i] = np.maximum(boundary[i], _tri(idx, s, half))
            if e < int(samples[i]):  # a span still in progress at the window's end has no end yet
                boundary[i] = np.maximum(boundary[i], _tri(idx, e, half))
            # settled_row: in progress, or ended less than 300 s before, is not held
            held[i, in_span] = False
            held[i, (idx >= e) & (idx - e < settle)] = False
            after[i, idx >= e] = True
    held &= valid_row
    now *= valid_row
    boundary *= valid_row
    return RowLabels(now, boundary, held, held & after, valid_row)


def pair_labels(
    spans: np.ndarray,
    dt: np.ndarray,
    ks: np.ndarray,
    rows: int,
    tolerance_s: float = TOLERANCE_S,
) -> PairLabels:
    """Pairwise targets at scored rows ks [B, N] (−1 = no row): [B, N, R]."""
    b, n = ks.shape
    idx = np.arange(rows, dtype=np.int64)
    w = np.zeros((b, n, rows))
    kind = np.zeros((b, n, rows))
    dist = np.full((b, n, rows), np.inf)
    for i, bounds in enumerate(_boundaries(spans)):
        half = tolerance_s / float(dt[i])
        for q in range(n):
            k = int(ks[i, q])
            if k < 0:
                continue
            seen = idx <= k
            # course first so that, at equal distance, the course boundary wins the tie
            for r, kd in sorted(bounds, key=lambda x: not is_turn_kind(x[1])):
                if r > k:
                    continue
                tri = _tri(idx, r, half) * seen
                w[i, q] = np.maximum(w[i, q], tri)
                d = np.abs(idx - r).astype(np.float64)
                closer = (d < dist[i, q]) & seen
                dist[i, q][closer] = d[closer]
                # generator 0.6.0's "both" includes a course change: a turn for p_kind
                kind[i, q][closer] = 1.0 if is_turn_kind(kd) else 0.0
    return PairLabels(np.minimum(w, 1.0), kind, np.minimum(w, 1.0))
