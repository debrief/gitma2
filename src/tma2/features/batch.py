"""In-memory batches for training (contract: specs/001 contracts/batch-interface.md).

The same kernel as the file path fills padded arrays for a block of scenario indices, in
parallel over scenarios; the result is a pure function of (seed, indices, ranges).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numba import get_num_threads, njit, prange, set_num_threads, uint64

from tma2.sim import scenario as sc
from tma2.sim.geometry import f32
from tma2.sim.ranges import flatten_ranges, noise_free, rows_for

KIND_NONE = -1
KIND_COURSE = 0
KIND_SPEED = 1


@dataclass
class Batch:
    index: np.ndarray  # (B,) int64
    samples: np.ndarray  # (B,) int32
    zig_index: np.ndarray  # (B,) int32
    sigma: np.ndarray  # (B,) float32
    dropout: np.ndarray  # (B,) float32
    redraws: np.ndarray  # (B,) int32
    t: np.ndarray  # (B, R) float32
    mask: np.ndarray  # (B, R) bool
    own: np.ndarray  # (B, R, 4) float32: x, y, course, speed
    tgt: np.ndarray  # (B, R, 4) float32
    bearing: np.ndarray  # (B, R) float32
    valid: np.ndarray  # (B, R) bool
    manoeuvring: np.ndarray  # (B, R) bool
    last_kind: np.ndarray  # (B, R) int8
    since_zig_s: np.ndarray  # (B, R) float32
    since_manoeuvre_end_s: np.ndarray  # (B, R) float32, −1 before any
    spans: np.ndarray  # (B, 4, 3) int32 padded with −1

    def __len__(self) -> int:
        return int(self.index.shape[0])


@njit(parallel=True, cache=True)
def _fill_batch(
    dataset_seed: uint64,
    indices: np.ndarray,
    R: np.ndarray,
    rmax: int,
    samples: np.ndarray,
    zig_index: np.ndarray,
    sigma: np.ndarray,
    dropout: np.ndarray,
    redraws: np.ndarray,
    t: np.ndarray,
    mask: np.ndarray,
    own: np.ndarray,
    tgt: np.ndarray,
    bearing: np.ndarray,
    valid: np.ndarray,
    manoeuvring: np.ndarray,
    last_kind: np.ndarray,
    since_zig: np.ndarray,
    since_m_end: np.ndarray,
    spans: np.ndarray,
) -> None:
    n = indices.shape[0]
    for b in prange(n):
        own_b = np.zeros((rmax, 4))
        tgt_b = np.zeros((rmax, 4))
        bearing_b = np.zeros(rmax)
        valid_b = np.zeros(rmax, dtype=np.bool_)
        P = np.full(sc.P_LEN, np.nan)
        tm = np.zeros((sc.MAX_TM, 4))
        TI = np.full(sc.TI_LEN, -1, dtype=np.int64)
        sp = np.zeros((sc.MAX_TM, 3), dtype=np.int64)
        stats = np.zeros(3)
        redraws[b] = sc.generate_into(
            dataset_seed,
            indices[b],
            R,
            rmax,
            own_b,
            tgt_b,
            bearing_b,
            valid_b,
            P,
            tm,
            TI,
            sp,
            stats,
        )
        n_s = TI[sc.TI_SAMPLES]
        samples[b] = n_s
        zig_index[b] = TI[sc.TI_ZIG]
        sigma[b] = P[sc.P_SIGMA]
        dropout[b] = P[sc.P_DROPOUT]
        dt = P[sc.P_DT]
        n_spans = TI[sc.TI_N_SPANS]
        for j in range(sc.MAX_TM):
            for c in range(3):
                spans[b, j, c] = sp[j, c] if j < n_spans else -1
        # 0.4.0 single-turn metadata becomes one course span for the labels.
        if n_spans < 0 and TI[sc.TI_M_INDEX] != -1:
            spans[b, 0, 0] = KIND_COURSE
            spans[b, 0, 1] = TI[sc.TI_M_START]
            spans[b, 0, 2] = TI[sc.TI_M_INDEX]
            n_spans = 1
        for i in range(rmax):
            inside = i < n_s
            mask[b, i] = inside
            t[b, i] = f32(i * dt) if inside else 0.0
            for c in range(4):
                own[b, i, c] = own_b[i, c]
                tgt[b, i, c] = tgt_b[i, c]
            bearing[b, i] = bearing_b[i]
            valid[b, i] = valid_b[i]
            since_zig[b, i] = (i - TI[sc.TI_ZIG]) * dt if inside else 0.0
            in_m = False
            kind = KIND_NONE
            last_end = -1
            for j in range(max(n_spans, 0)):
                s0 = spans[b, j, 1]
                e0 = spans[b, j, 2]
                if s0 <= i < e0:
                    in_m = True
                if e0 <= i:
                    kind = spans[b, j, 0]
                    last_end = e0
            manoeuvring[b, i] = in_m and inside
            last_kind[b, i] = kind if inside else KIND_NONE
            since_m_end[b, i] = (i - last_end) * dt if (inside and last_end >= 0) else -1.0


def generate_batch(
    seed: int | np.uint64,
    batch_index: int,
    batch_size: int,
    ranges: dict[str, Any],
    start: int = 0,
    end: int | None = None,
    noise_free_data: bool = False,
    workers: int | None = None,
) -> Batch:
    """Batch ``batch_index`` of size ``batch_size`` over indices ``[start, end)``."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    lo = start + batch_index * batch_size
    if end is not None and lo >= end:
        raise IndexError(f"batch {batch_index} is beyond the index range [{start}, {end})")
    hi = lo + batch_size if end is None else min(lo + batch_size, end)
    indices = np.arange(lo, hi, dtype=np.int64)
    return generate_indices(seed, indices, ranges, noise_free_data, workers)


def generate_indices(
    seed: int | np.uint64,
    indices: np.ndarray,
    ranges: dict[str, Any],
    noise_free_data: bool = False,
    workers: int | None = None,
) -> Batch:
    """Arrays for an explicit set of scenario indices."""
    r = noise_free(ranges) if noise_free_data else ranges
    R = flatten_ranges(r)
    rmax = rows_for(r)
    n = int(indices.shape[0])
    b = Batch(
        index=np.asarray(indices, dtype=np.int64),
        samples=np.zeros(n, dtype=np.int32),
        zig_index=np.zeros(n, dtype=np.int32),
        sigma=np.zeros(n, dtype=np.float32),
        dropout=np.zeros(n, dtype=np.float32),
        redraws=np.zeros(n, dtype=np.int32),
        t=np.zeros((n, rmax), dtype=np.float32),
        mask=np.zeros((n, rmax), dtype=np.bool_),
        own=np.zeros((n, rmax, 4), dtype=np.float32),
        tgt=np.zeros((n, rmax, 4), dtype=np.float32),
        bearing=np.zeros((n, rmax), dtype=np.float32),
        valid=np.zeros((n, rmax), dtype=np.bool_),
        manoeuvring=np.zeros((n, rmax), dtype=np.bool_),
        last_kind=np.full((n, rmax), KIND_NONE, dtype=np.int8),
        since_zig_s=np.zeros((n, rmax), dtype=np.float32),
        since_manoeuvre_end_s=np.full((n, rmax), -1.0, dtype=np.float32),
        spans=np.full((n, sc.MAX_TM, 3), -1, dtype=np.int32),
    )
    previous = get_num_threads()
    if workers is not None:
        set_num_threads(max(1, workers))
    try:
        _fill_batch(
            np.uint64(seed),
            b.index,
            R,
            rmax,
            b.samples,
            b.zig_index,
            b.sigma,
            b.dropout,
            b.redraws,
            b.t,
            b.mask,
            b.own,
            b.tgt,
            b.bearing,
            b.valid,
            b.manoeuvring,
            b.last_kind,
            b.since_zig_s,
            b.since_manoeuvre_end_s,
            b.spans,
        )
    finally:
        if workers is not None:
            set_num_threads(previous)
    bad = np.flatnonzero(b.redraws < 0)
    if bad.size:
        raise ValueError(
            f"scenario {int(b.index[bad[0]])}: no valid geometry after {sc.MAX_REDRAWS} redraws"
        )
    return b
