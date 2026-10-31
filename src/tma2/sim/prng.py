"""Seeded PRNG, ported line for line from gitma ``packages/sim/src/prng.ts`` (commit d0aec60).

SplitMix64 derives per-scenario seeds and the xoshiro128** state; xoshiro128** is the stream.
State is an explicit ``uint32[4]`` array passed to every call (no hidden state, constitution III),
and every function is a numba ``njit`` so the scenario kernel can call it.
"""

from __future__ import annotations

import numpy as np
from numba import njit, uint32, uint64

MASK64 = np.uint64(0xFFFFFFFFFFFFFFFF)
GAMMA = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
TWO_POW_53 = 9007199254740992.0


@njit(cache=True)
def mix64(z: uint64) -> uint64:
    """SplitMix64 mix function (Steele, Lea, Flood 2014); arithmetic wraps mod 2^64."""
    z = (z ^ (z >> uint64(30))) * _M1
    z = (z ^ (z >> uint64(27))) * _M2
    return z ^ (z >> uint64(31))


@njit(cache=True)
def splitmix64_at(seed: uint64, n: int) -> uint64:
    """The n-th output (0-based) of SplitMix64 seeded with ``seed``."""
    return mix64(seed + uint64(n + 1) * GAMMA)


@njit(cache=True)
def derive_seed(dataset_seed: uint64, index: int) -> uint64:
    """Seed for scenario ``index`` of a dataset: SplitMix64 output number ``index``."""
    return splitmix64_at(dataset_seed, index)


def parse_seed(text: str) -> np.uint64:
    """Parse a uint64 seed from a decimal string, rejecting anything out of range."""
    if not text.isdigit():
        raise ValueError(f'seed must be a decimal integer, got "{text}"')
    value = int(text)
    if value > 0xFFFFFFFFFFFFFFFF:
        raise ValueError(f"seed exceeds 64 bits: {text}")
    return np.uint64(value)


@njit(cache=True)
def create_rng(seed: uint64) -> np.ndarray:
    """xoshiro128** state from a 64-bit seed via two SplitMix64 outputs (gitma ``createRng``)."""
    a = splitmix64_at(seed, 0)
    b = splitmix64_at(seed, 1)
    s = np.empty(4, dtype=np.uint32)
    s[0] = uint32(a & uint64(0xFFFFFFFF))
    s[1] = uint32(a >> uint64(32))
    s[2] = uint32(b & uint64(0xFFFFFFFF))
    s[3] = uint32(b >> uint64(32))
    if s[0] == 0 and s[1] == 0 and s[2] == 0 and s[3] == 0:
        s[0] = 1
    return s


@njit(cache=True)
def _rotl(x: uint32, k: int) -> uint32:
    return uint32((x << uint32(k)) | (x >> uint32(32 - k)))


@njit(cache=True)
def next_u32(s: np.ndarray) -> uint32:
    """Next uint32 from xoshiro128** (Blackman & Vigna 2018). Mutates ``s``."""
    s0 = s[0]
    s1 = s[1]
    result = uint32(_rotl(uint32(s1 * uint32(5)), 7) * uint32(9))
    t = uint32(s1 << uint32(9))
    s2 = uint32(s[2] ^ s0)
    s3 = uint32(s[3] ^ s1)
    s[1] = uint32(s1 ^ s2)
    s[0] = uint32(s0 ^ s3)
    s[2] = uint32(s2 ^ t)
    s[3] = _rotl(s3, 11)
    return result


@njit(cache=True)
def uniform01(s: np.ndarray) -> float:
    """Uniform double in [0, 1) with 53 random bits (two u32 draws)."""
    a = float(next_u32(s) >> uint32(5))
    b = float(next_u32(s) >> uint32(6))
    return (a * 67108864.0 + b) / TWO_POW_53


@njit(cache=True)
def uniform(s: np.ndarray, lo: float, hi: float) -> float:
    """Uniform double in [lo, hi)."""
    return lo + (hi - lo) * uniform01(s)


@njit(cache=True)
def log_uniform(s: np.ndarray, lo: float, hi: float) -> float:
    """Log-uniform double in [lo, hi), lo > 0."""
    return float(np.exp(uniform(s, np.log(lo), np.log(hi))))


@njit(cache=True)
def gaussian(s: np.ndarray) -> float:
    """Standard normal via Box-Muller; the second variate is discarded (stateless)."""
    u1 = 1.0 - uniform01(s)
    u2 = uniform01(s)
    return float(np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2))


@njit(cache=True)
def uniform_int(s: np.ndarray, n: int) -> int:
    """Uniform integer in [0, n)."""
    return int(np.floor(uniform01(s) * n))
