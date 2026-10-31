"""Scenario objects from the kernel (gitma ``generateScenario``'s record assembly).

``generate_scenario`` is the single-scenario, metadata-carrying path used by the file writer and
by tests; ``features/batch.py`` uses the same kernel for training batches.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from tma2.types import Scenario

from . import scenario as sc
from .geometry import f32
from .prng import derive_seed
from .ranges import flatten_ranges, rows_for


@dataclass
class KernelBuffers:
    """Preallocated per-scenario output arrays for ``generate_into``."""

    rmax: int
    own: np.ndarray
    tgt: np.ndarray
    bearing: np.ndarray
    valid: np.ndarray
    P: np.ndarray
    tm: np.ndarray
    TI: np.ndarray
    spans: np.ndarray
    stats: np.ndarray

    @classmethod
    def for_rows(cls, rmax: int) -> KernelBuffers:
        return cls(
            rmax=rmax,
            own=np.zeros((rmax, 4)),
            tgt=np.zeros((rmax, 4)),
            bearing=np.zeros(rmax),
            valid=np.zeros(rmax, dtype=np.bool_),
            P=np.full(sc.P_LEN, np.nan),
            tm=np.zeros((sc.MAX_TM, 4)),
            TI=np.full(sc.TI_LEN, -1, dtype=np.int64),
            spans=np.zeros((sc.MAX_TM, 3), dtype=np.int64),
            stats=np.zeros(3),
        )


@dataclass
class GeneratedScenario:
    scenario: Scenario
    redraws: int


_PARAM_KEYS: tuple[tuple[str, int], ...] = (
    ("window_s", sc.P_WINDOW),
    ("dt_s", sc.P_DT),
    ("ownship_speed_mps", sc.P_OWN_SPEED),
    ("ownship_course0_rad", sc.P_COURSE0),
    ("zig_angle_rad", sc.P_ZIG),
    ("zig_fraction", sc.P_ZIG_FRAC),
    ("target_range0_m", sc.P_RANGE0),
    ("target_bearing0_rad", sc.P_BEARING0),
    ("target_speed_mps", sc.P_TGT_SPEED),
    ("target_course_rad", sc.P_TGT_COURSE),
    ("noise_sigma_rad", sc.P_SIGMA),
    ("dropout_fraction", sc.P_DROPOUT),
    ("ownship_turn_rate_rad_s", sc.P_TURN_RATE),
    ("zig2_delay_s", sc.P_ZIG2_DELAY),
    ("zig2_angle_rad", sc.P_ZIG2_ANGLE),
    ("target_manoeuvre_time_s", sc.P_TM_TIME),
    ("target_manoeuvre_angle_rad", sc.P_TM_ANGLE),
    ("target_turn_rate_rad_s", sc.P_TM_RATE),
)

_KINDS = ("course", "speed")


def kernel_to_record_parts(
    dataset_seed: np.uint64, index: int, buf: KernelBuffers
) -> tuple[dict[str, Any], int, float]:
    """(metadata dict, samples, dt) from filled kernel buffers."""
    P, TI = buf.P, buf.TI
    params: dict[str, Any] = {}
    for key, i in _PARAM_KEYS:
        if not math.isnan(P[i]):
            params[key] = float(P[i])
    n_tm = int(P[sc.P_N_TM])
    if n_tm >= 0:
        params["target_manoeuvres"] = [
            {
                "kind": _KINDS[int(buf.tm[j, sc.TM_KIND])],
                "start_time_s": float(buf.tm[j, sc.TM_START]),
                "change": float(buf.tm[j, sc.TM_CHANGE]),
                "rate": float(buf.tm[j, sc.TM_RATE]),
            }
            for j in range(n_tm)
        ]
    samples = int(TI[sc.TI_SAMPLES])
    metadata: dict[str, Any] = {
        "seed": str(int(derive_seed(dataset_seed, index))),
        "index": index,
        "parameters": params,
        "samples": samples,
        "zig_index": int(TI[sc.TI_ZIG]),
    }
    for key, i in (
        ("turn_start_index", sc.TI_TURN_START),
        ("zig2_index", sc.TI_ZIG2),
        ("turn2_start_index", sc.TI_TURN2_START),
    ):
        if TI[i] != -1:
            metadata[key] = int(TI[i])
    if TI[sc.TI_M_INDEX] != -1:
        m_start = TI[sc.TI_M_START] if TI[sc.TI_M_START] != -1 else TI[sc.TI_M_INDEX]
        metadata["manoeuvre_start_index"] = int(m_start)
        metadata["manoeuvre_index"] = int(TI[sc.TI_M_INDEX])
    if TI[sc.TI_N_SPANS] != -1:
        metadata["manoeuvres"] = [
            {
                "kind": _KINDS[int(buf.spans[j, 0])],
                "start_index": int(buf.spans[j, 1]),
                "end_index": int(buf.spans[j, 2]),
            }
            for j in range(int(TI[sc.TI_N_SPANS]))
        ]
    metadata["zig_time_s"] = float(buf.stats[0])
    metadata["mean_range_m"] = float(buf.stats[1])
    metadata["min_range_m"] = float(buf.stats[2])
    return metadata, samples, float(P[sc.P_DT])


def kernel_to_record(
    dataset_seed: np.uint64, index: int, buf: KernelBuffers, redraws: int
) -> dict[str, Any]:
    """The scenario dict (gitma's record shape) from filled kernel buffers."""
    metadata, samples, dt = kernel_to_record_parts(dataset_seed, index, buf)
    own = buf.own
    tgt = buf.tgt
    ownship = [
        {
            "timestamp_s": float(f32(i * dt)),
            "x_m": float(own[i, 0]),
            "y_m": float(own[i, 1]),
            "course_rad": float(own[i, 2]),
            "speed_mps": float(own[i, 3]),
        }
        for i in range(samples)
    ]
    target = [
        {
            "timestamp_s": float(f32(i * dt)),
            "x_m": float(tgt[i, 0]),
            "y_m": float(tgt[i, 1]),
            "course_rad": float(tgt[i, 2]),
            "speed_mps": float(tgt[i, 3]),
        }
        for i in range(samples)
    ]
    observations = [
        {
            "timestamp_s": float(f32(i * dt)),
            "bearing_rad": float(buf.bearing[i]),
            "valid": bool(buf.valid[i]),
        }
        for i in range(samples)
    ]
    return {
        "record": "scenario",
        "metadata": metadata,
        "ownship": {"id": "ownship", "states": ownship},
        "target": {"id": "target", "states": target},
        "observations": observations,
    }


def kernel_metadata(dataset_seed: np.uint64, index: int, buf: KernelBuffers) -> dict[str, Any]:
    """Only the metadata dict (parameters, indices, spans, stats) from filled kernel buffers."""
    return kernel_to_record_parts(dataset_seed, index, buf)[0]


def kernel_arrays(buf: KernelBuffers) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """own [S,5], tgt [S,5], obs [S,3] float64 arrays (gitma's pack column order) from buffers."""
    n = int(buf.TI[sc.TI_SAMPLES])
    dt = float(buf.P[sc.P_DT])
    t = np.array([f32(i * dt) for i in range(n)])
    own = np.column_stack([t, buf.own[:n, 0], buf.own[:n, 1], buf.own[:n, 2], buf.own[:n, 3]])
    tgt = np.column_stack([t, buf.tgt[:n, 0], buf.tgt[:n, 1], buf.tgt[:n, 2], buf.tgt[:n, 3]])
    obs = np.column_stack([t, buf.bearing[:n], buf.valid[:n].astype(np.float64)])
    return own, tgt, obs


def run_kernel(dataset_seed: np.uint64, index: int, R: np.ndarray, buf: KernelBuffers) -> int:
    """Run the kernel for one index into ``buf``; returns the redraw count."""
    return int(
        sc.generate_into(
            dataset_seed,
            index,
            R,
            buf.rmax,
            buf.own,
            buf.tgt,
            buf.bearing,
            buf.valid,
            buf.P,
            buf.tm,
            buf.TI,
            buf.spans,
            buf.stats,
        )
    )


def generate_record(
    dataset_seed: np.uint64,
    index: int,
    R: np.ndarray,
    buf: KernelBuffers,
) -> tuple[dict[str, Any], int]:
    """Run the kernel for one index into ``buf`` and return (record dict, redraws)."""
    redraws = run_kernel(dataset_seed, index, R, buf)
    return kernel_to_record(dataset_seed, index, buf, redraws), redraws


def generate_scenario(
    dataset_seed: int | np.uint64, index: int, ranges: dict[str, Any]
) -> GeneratedScenario:
    """Generate scenario ``index`` of a dataset as a validated ``Scenario`` model."""
    R = flatten_ranges(ranges)
    buf = KernelBuffers.for_rows(rows_for(ranges))
    record, redraws = generate_record(np.uint64(dataset_seed), index, R, buf)
    return GeneratedScenario(scenario=Scenario.model_validate(record), redraws=redraws)


def warm_up() -> None:
    """Trigger numba compilation (first call costs seconds; the cache is reused afterwards)."""
    from .ranges import DEFAULT_RANGES

    generate_scenario(1, 0, DEFAULT_RANGES)
