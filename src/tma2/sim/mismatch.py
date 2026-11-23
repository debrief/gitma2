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

Spec 037 (research R2) adds two kinds, drawn from a second stream so that no draw above moves
and every condition without them is byte-identical to 0.7.0:

- ``white_t_df`` (an integer ν > 2): the white part is Student-t with ν degrees of freedom,
  scaled to the same sd: the kernel's own normal draw divided by sqrt(χ²_ν / ν), times
  sqrt((ν − 2) / ν);
- ``sigma_step_factor`` (f ≥ 1): from a sample drawn uniformly in the engagement, the white,
  correlated and outlier parts are multiplied by f or by 1 / f (an even draw).

Two more kinds of the second stream, added after the first two proved harmless to every system
on tuning data (spec 037 T018):

- ``osc_amp`` and ``osc_period_s``: a sinusoidal error of that amplitude (in units of the true
  sd) and period, with a phase drawn once per engagement (recorded in the correlated column);
- ``burst_rate``, ``burst_len_s`` and ``burst_spread``: with that probability per sample a burst
  starts; for a geometric number of samples of that mean duration every bearing carries one
  common offset drawn N(0, (spread × true sd)²) (recorded in the outlier column, flagged).

The truth side file's per-engagement columns do not describe the kinds of the second stream;
the per-sample components do.
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

MISMATCH_VERSION_2 = "0.8.0"
"""The same, for a condition that uses a kind of the second stream (spec 037)."""

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
M_T_DF = 7
M_STEP = 8
M_OSC_AMP = 9
M_OSC_PERIOD = 10
M_BURST_RATE = 11
M_BURST_LEN = 12
M_BURST_SPREAD = 13
M_LEN = 14
M_SECOND = 7  # columns from here on belong to the second stream

MISMATCH_STREAM_2 = 1_000_033
"""The second stream's SplitMix64 output number (spec 037): the two kinds added later."""

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

    @property
    def version(self) -> str:
        """The generator version a split under this condition records."""
        second = not np.all(np.isnan(self.M[M_SECOND:]))
        return MISMATCH_VERSION_2 if second else MISMATCH_VERSION


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
    df = c.get("white_t_df")
    if df is not None:
        if float(df) != int(df) or int(df) < 3:
            raise ValueError(f"mismatch condition {c.get('id')}: white_t_df is an integer >= 3")
        M[M_T_DF] = float(df)
    step = c.get("sigma_step_factor")
    if step is not None:
        if float(step) < 1.0:
            raise ValueError(f"mismatch condition {c.get('id')}: sigma_step_factor must be >= 1")
        M[M_STEP] = float(step)
    pair("osc_amp", "osc_period_s", M_OSC_AMP, M_OSC_PERIOD)
    burst = [c.get(k) for k in ("burst_rate", "burst_len_s", "burst_spread")]
    if any(v is not None for v in burst):
        if any(v is None or float(v) <= 0 for v in burst) or float(burst[0]) >= 1.0:
            raise ValueError(
                f"mismatch condition {c.get('id')}: burst_rate (below 1), burst_len_s and "
                "burst_spread go together and are positive"
            )
        M[M_BURST_RATE], M[M_BURST_LEN], M[M_BURST_SPREAD] = (float(v) for v in burst)
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
    # the second stream (spec 037): read only when one of its kinds is on
    df = 0 if math.isnan(M[M_T_DF]) else int(M[M_T_DF])
    step = 1.0 if math.isnan(M[M_STEP]) else M[M_STEP]
    osc = 0.0 if math.isnan(M[M_OSC_AMP]) else M[M_OSC_AMP] * sigma_true
    osc_w = 0.0 if math.isnan(M[M_OSC_PERIOD]) else 2.0 * math.pi / M[M_OSC_PERIOD]
    b_rate = 0.0 if math.isnan(M[M_BURST_RATE]) else M[M_BURST_RATE]
    b_len = 0.0 if math.isnan(M[M_BURST_LEN]) else M[M_BURST_LEN] / dt
    b_sd = 0.0 if math.isnan(M[M_BURST_SPREAD]) else M[M_BURST_SPREAD] * sigma_true
    second = df > 0 or step > 1.0 or osc > 0.0 or b_rate > 0.0
    step_at = samples
    phase = 0.0
    b_left = 0
    b_off = 0.0
    if second:
        s2 = create_rng(derive_seed(scenario_seed, MISMATCH_STREAM_2))
        u_at = uniform01(s2)
        u_dir = uniform01(s2)
        phase = 2.0 * math.pi * uniform01(s2)
        if step > 1.0:
            step_at = int(u_at * samples)
            if u_dir < 0.5:
                step = 1.0 / step
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
        g = white[i]
        if df > 0:
            chi = 0.0
            for _ in range(df):
                x = gaussian(s2)
                chi += x * x
            g = g / math.sqrt(chi / df) * math.sqrt((df - 2.0) / df)
        level = step if i >= step_at else 1.0
        w = level * sigma_w * g
        c = level * sigma_c * zc
        b = sigma_b * zb
        o = level * out_sd * go if is_out else 0.0
        if second:  # three draws per sample, whatever is on
            ub = uniform01(s2)
            gbst = gaussian(s2)
            ul = uniform01(s2)
            if b_left == 0 and ub < b_rate:
                b_off = b_sd * gbst
                b_left = max(1, int(-math.log(1.0 - ul) * b_len))
            if b_left > 0:
                b_left -= 1
                o += level * b_off
                is_out = True
            if osc > 0.0:
                c += level * osc * math.sin(osc_w * i * dt + phase)
        comp[i, 0] = w
        comp[i, 1] = c
        comp[i, 2] = b
        comp[i, 3] = o
        outlier[i] = is_out
        if valid[i]:
            bearing[i] = f32_angle(clean[i] + w + c + b + o)
