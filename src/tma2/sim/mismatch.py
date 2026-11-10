"""Bearing-error mismatch overlay (generator 0.7.0, spec 010 research R1 and R2).

The 0.6.0 kernel runs unchanged and exposes each sample's noise-free bearing ``b`` and its
standard normal draw ``g``. This overlay rebuilds the bearing as

    bearing = b + sigma_w * g + c + beta + o

from its own stream, so no kernel draw moves and a split without a condition is byte-identical to
generator 0.6.0. Every draw is made for every sample and every kind, whether the kind is enabled
or the sample dropped, in one fixed order; a single-kind condition is therefore a component of the
combined one for the same seed.

- sigma_true = sigma_nominal * s, s log-uniform on [1/k, k] (once per engagement);
- white: sd sigma_w = sqrt(1 - share) * sigma_true (share = 0 without the correlated kind);
- c: first-order Gauss-Markov, stationary sd sqrt(share) * sigma_true, correlation time tau;
- beta: first-order Gauss-Markov, stationary sd sigma_b, correlation time tau_b;
- o: with probability p, an added N(0, (spread * sigma_true)^2).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numba import njit, uint64

from .geometry import f32_angle
from .prng import create_rng, derive_seed, gaussian, uniform01

MISMATCH_VERSION = "0.7.0"
"""Generator version recorded in the header of a split that carries a mismatch."""

MISMATCH_STREAM = 1_000_003
"""SplitMix64 output number of the scenario seed that seeds the overlay's stream. The kernel uses
small numbers (0, 1 for its own state; 2 + and 3 + 2·attempt for the manoeuvre and wander
streams, attempt ≤ MAX_REDRAWS), so this cannot collide."""

M_CORR_TAU = 0
M_CORR_SHARE = 1
M_BIAS_SD = 2
M_BIAS_TAU = 3
M_SIGMA_K = 4
M_OUT_RATE = 5
M_OUT_SPREAD = 6
M_LEN = 7

# Per-engagement truth columns.
E_SIGMA_TRUE = 0
E_SIGMA_W = 1
E_SIGMA_C = 2
E_TAU_C = 3
E_SIGMA_B = 4
E_TAU_B = 5
E_OUT_RATE = 6
E_OUT_SD = 7
E_LEN = 8


@dataclass(frozen=True)
class Condition:
    """A mismatch condition (schema ``MismatchCondition``) flattened for the kernel."""

    id: str
    M: np.ndarray

    @property
    def off(self) -> bool:
        return bool(np.all(np.isnan(self.M)))


def flatten_condition(c: dict[str, Any]) -> Condition:
    """Validate a ``MismatchCondition`` dict and flatten it (NaN: kind off)."""
    M = np.full(M_LEN, np.nan)

    def pair(a: str, b: str, ia: int, ib: int) -> None:
        va, vb = c.get(a), c.get(b)
        if (va is None) != (vb is None):
            raise ValueError(f"mismatch condition {c.get('id')}: {a} and {b} go together")
        if va is not None and vb is not None:
            if not (float(va) > 0 and float(vb) > 0):
                raise ValueError(f"mismatch condition {c.get('id')}: {a}, {b} must be positive")
            M[ia], M[ib] = float(va), float(vb)

    pair("corr_tau_s", "corr_share", M_CORR_TAU, M_CORR_SHARE)
    pair("bias_sd_rad", "bias_tau_s", M_BIAS_SD, M_BIAS_TAU)
    pair("outlier_rate", "outlier_spread", M_OUT_RATE, M_OUT_SPREAD)
    if not math.isnan(M[M_CORR_SHARE]) and M[M_CORR_SHARE] >= 1.0:
        raise ValueError(f"mismatch condition {c.get('id')}: corr_share must be below 1")
    if not math.isnan(M[M_OUT_RATE]) and M[M_OUT_RATE] >= 1.0:
        raise ValueError(f"mismatch condition {c.get('id')}: outlier_rate must be below 1")
    k = c.get("sigma_factor_max")
    if k is not None:
        if float(k) < 1.0:
            raise ValueError(f"mismatch condition {c.get('id')}: sigma_factor_max must be >= 1")
        M[M_SIGMA_K] = float(k)
    return Condition(id=str(c["id"]), M=M)


@njit(cache=True)
def apply_mismatch(
    scenario_seed: uint64,
    M: np.ndarray,
    samples: int,
    dt: float,
    sigma_nominal: float,
    clean: np.ndarray,
    white: np.ndarray,
    valid: np.ndarray,
    bearing: np.ndarray,
    eng: np.ndarray,
    comp: np.ndarray,
    outlier: np.ndarray,
) -> None:
    """Rewrite ``bearing`` on valid samples under condition ``M``; fill the truth arrays.

    ``eng`` ``[E_LEN]`` receives the engagement's error-model parameters; ``comp`` ``[samples, 4]``
    the per-sample components (white, correlated, bias, outlier) in radians, for every sample;
    ``outlier`` ``[samples]`` the outlier flags.
    """
    s = create_rng(derive_seed(scenario_seed, MISMATCH_STREAM))
    u_sigma = uniform01(s)
    k = M[M_SIGMA_K]
    factor = 1.0
    if not math.isnan(k) and k > 1.0:
        factor = math.exp((2.0 * u_sigma - 1.0) * math.log(k))
    sigma_true = sigma_nominal * factor
    share = 0.0 if math.isnan(M[M_CORR_SHARE]) else M[M_CORR_SHARE]
    sigma_w = math.sqrt(1.0 - share) * sigma_true
    sigma_c = math.sqrt(share) * sigma_true
    tau_c = M[M_CORR_TAU]
    phi_c = 0.0 if math.isnan(tau_c) else math.exp(-dt / tau_c)
    sigma_b = 0.0 if math.isnan(M[M_BIAS_SD]) else M[M_BIAS_SD]
    tau_b = M[M_BIAS_TAU]
    phi_b = 0.0 if math.isnan(tau_b) else math.exp(-dt / tau_b)
    rate = 0.0 if math.isnan(M[M_OUT_RATE]) else M[M_OUT_RATE]
    out_sd = 0.0 if math.isnan(M[M_OUT_SPREAD]) else M[M_OUT_SPREAD] * sigma_true
    eng[E_SIGMA_TRUE] = sigma_true
    eng[E_SIGMA_W] = sigma_w
    eng[E_SIGMA_C] = sigma_c
    eng[E_TAU_C] = 0.0 if math.isnan(tau_c) else tau_c
    eng[E_SIGMA_B] = sigma_b
    eng[E_TAU_B] = 0.0 if math.isnan(tau_b) else tau_b
    eng[E_OUT_RATE] = rate
    eng[E_OUT_SD] = out_sd
    zc = 0.0
    zb = 0.0
    for i in range(samples):
        gc = gaussian(s)
        gb = gaussian(s)
        uo = uniform01(s)
        go = gaussian(s)
        if i == 0:
            zc = gc
            zb = gb
        else:
            zc = phi_c * zc + math.sqrt(1.0 - phi_c * phi_c) * gc
            zb = phi_b * zb + math.sqrt(1.0 - phi_b * phi_b) * gb
        is_out = uo < rate
        w = sigma_w * white[i]
        c = sigma_c * zc
        b = sigma_b * zb
        o = out_sd * go if is_out else 0.0
        comp[i, 0] = w
        comp[i, 1] = c
        comp[i, 2] = b
        comp[i, 3] = o
        outlier[i] = is_out
        if valid[i]:
            bearing[i] = f32_angle(clean[i] + w + c + b + o)
