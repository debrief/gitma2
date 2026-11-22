"""The fine-tuning mix of bearing-error conditions (spec 037 research R3).

Every scenario index of the stream draws its condition from its own sub-stream of the stream
seed: clean with probability ``clean_share``; otherwise each of the four kinds of spec 010 is
on with probability ``p_on`` and its severities are log-uniform within the mix's ranges. The
draws are made for every index and every kind in one fixed order, whatever is switched on. The
kinds of the overlay's second stream (``white_t_df``, ``sigma_step_factor``) can never be drawn:
they are the held-out family.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numba import njit, uint64

from tma2.sim import mismatch as mm
from tma2.sim.prng import create_rng, derive_seed, uniform01

MIX_STREAM = 1_000_061
"""SplitMix64 output number of the scenario seed that seeds the mix's draws (the kernel uses
small numbers; the overlay 1,000,003 and 1,000,033)."""

DEG = math.pi / 180.0
# rows of the flattened ranges: (column of M, low, high)
_KEYS = (
    ("corr_tau_s", mm.M_CORR_TAU, 0),
    ("corr_share", mm.M_CORR_SHARE, 0),
    ("bias_sd_deg", mm.M_BIAS_SD, 1),
    ("bias_tau_s", mm.M_BIAS_TAU, 1),
    ("sigma_factor_max", mm.M_SIGMA_K, 2),
    ("outlier_rate", mm.M_OUT_RATE, 3),
    ("outlier_spread", mm.M_OUT_SPREAD, 3),
)


@dataclass(frozen=True)
class Mix:
    raw: dict[str, Any]
    clean_share: float
    p_on: float
    lo: np.ndarray  # [7] in M's units
    hi: np.ndarray
    col: np.ndarray  # [7] column of M
    kind: np.ndarray  # [7] which of the four kinds the row belongs to


def load_mix(path: str | Path) -> Mix:
    raw: dict[str, Any] = json.loads(Path(path).read_text())
    if set(raw) - {"description", "clean_share", "p_on", *(k for k, _, _ in _KEYS)}:
        raise ValueError("mix: unknown key (the held-out kinds cannot be in a training mix)")
    lo, hi = np.zeros(len(_KEYS)), np.zeros(len(_KEYS))
    for i, (key, _col, _kind) in enumerate(_KEYS):
        a, b = (float(x) for x in raw[key])
        if not 0 < a <= b:
            raise ValueError(f"mix {key}: need 0 < min <= max")
        scale = DEG if key.endswith("_deg") else 1.0
        lo[i], hi[i] = a * scale, b * scale
    return Mix(
        raw,
        float(raw["clean_share"]),
        float(raw["p_on"]),
        lo,
        hi,
        np.array([c for _, c, _ in _KEYS], dtype=np.int64),
        np.array([k for _, _, k in _KEYS], dtype=np.int64),
    )


@njit(cache=True)
def _draw(
    stream_seed: uint64,
    indices: np.ndarray,
    clean_share: float,
    p_on: float,
    lo: np.ndarray,
    hi: np.ndarray,
    col: np.ndarray,
    kind: np.ndarray,
    M: np.ndarray,
) -> None:
    for b in range(indices.shape[0]):
        s = create_rng(derive_seed(derive_seed(stream_seed, indices[b]), MIX_STREAM))
        clean = uniform01(s) < clean_share
        on = np.zeros(4, dtype=np.bool_)
        for k in range(4):
            on[k] = uniform01(s) < p_on
        for i in range(lo.shape[0]):
            u = uniform01(s)
            if not clean and on[kind[i]]:
                M[b, col[i]] = math.exp(math.log(lo[i]) + u * (math.log(hi[i]) - math.log(lo[i])))


def conditions(stream_seed: int | np.uint64, indices: np.ndarray, mix: Mix) -> np.ndarray:
    """[n, M_LEN] the condition of each scenario index (a row of NaN: clean)."""
    M = np.full((indices.shape[0], mm.M_LEN), np.nan)
    _draw(
        np.uint64(stream_seed),
        np.asarray(indices, dtype=np.int64),
        mix.clean_share,
        mix.p_on,
        mix.lo,
        mix.hi,
        mix.col,
        mix.kind,
        M,
    )
    return M
