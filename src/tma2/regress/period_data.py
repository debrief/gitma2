"""The on-the-fly stream of periods (spec 016 research R9): engagements from a seed, each cut to
a period as Gate T cuts them, never stored.

Update ``u`` of a configuration reads engagement indices ``stream_indices(cfg, u)`` of the
stream seed. Each engagement draws its family (Annex B, randomised statistics, quiet) and its
bearing-error overlay (none, correlated, outliers, both) from its own sub-stream, seeded from
the engagement's seed, so the generator's draws are untouched and a batch is a pure function of
(configuration, mix, update). Every draw is made for every engagement in one fixed order,
whichever family or overlay it selects. Ranges are per engagement (no grouping): the kernel
reads one flat ranges row per engagement. The overlay is spec 010's
(``sim.mismatch.apply_mismatch``, seeded as ``sim.generate.run_kernel`` seeds it); bias and the
sigma factor are never set.

Per 5-second row of a period: spec 012's canonical-frame features (rotated to the period's
first valid bearing; ownship motion as displacements, so the period's start is the origin), the
time from the period's start ÷ 7,200 s and the period's length ÷ 7,200 s. Targets: spec 012's
(ln(range ÷ 10 km), velocity ÷ 10 m/s in the frame) and whether a target manoeuvre is in
progress at the row (``Period.spans``: rows start_index … end_index).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
from numba import njit, prange, uint64

from tma2.sim import mismatch as mm
from tma2.sim import ranges as rg
from tma2.sim import scenario as sc
from tma2.sim.prng import create_rng, derive_seed, mix64, uniform01, uniform_int

from .data import stream_indices
from .frame import N_FEATURES, features, targets
from .model import RegressorConfig

if TYPE_CHECKING:
    from tma2.timelate.periods import Period

# As ``tma2.timelate.periods`` (CUT_STREAM, MIN_SECONDS). That module is not imported here: it
# pulls in the scorers and their dependencies, which the GPU image does not carry. ``_cuts``
# repeats its ``cut``; tests/unit/test_period_model.py holds the two equal.
CUT_STREAM = np.uint64(0x7D3A_91C4_55E0_13B7)
MIN_SECONDS = 1200.0
MIX_STREAM = np.uint64(0x5C1E_A07B_93D2_46F1)  # distinguishes the mix's sub-stream
T_UNIT = 7200.0  # s
N_PERIOD_FEATURES = N_FEATURES + 2
FAMILIES = ("annex_b", "randomised", "quiet")
OVERLAYS = ("none", "correlated", "outliers", "both")

# The sub-stream's draws, in order.
U_FAMILY, U_LEG, U_ANGLE, U_RATE, U_DV, U_ACC, U_COURSE, U_SPEED = range(8)
U_OVERLAY, U_KIND, U_TAU, U_SHARE, U_OUT_RATE, U_OUT_SPREAD = range(8, 14)
N_DRAWS = 14


@dataclass
class PeriodTensors:
    f: np.ndarray  # [B, R, 9] float32
    y: np.ndarray  # [B, R, 3] float32
    mask: np.ndarray  # [B, R] rows of the period
    man: np.ndarray  # [B, R] a target manoeuvre is in progress
    index: np.ndarray  # [B] engagement index in the stream
    first: np.ndarray  # [B] the period's first row in its engagement
    rows: np.ndarray  # [B]
    family: np.ndarray  # [B] index into FAMILIES
    overlay: np.ndarray  # [B] index into OVERLAYS
    condition: np.ndarray  # [B, M_LEN] the overlay's parameters (NaN: kind off)


FIELDS = ("f", "y", "mask", "man", "index", "first", "rows", "family", "overlay", "condition")


@dataclass(frozen=True)
class Mix:
    """A mix file with its ranges loaded and flattened."""

    raw: dict[str, Any]
    base: dict[str, Any]
    R_base: np.ndarray
    R_quiet: np.ndarray
    rmax: int
    dt: float


def _resolve(path: str, mix_path: Path) -> Path:
    """A path named in a mix file: as given, else from the repository the mix file is in."""
    p = Path(path)
    return p if p.exists() else mix_path.resolve().parents[2] / path


def load_mix(path: str) -> Mix:
    raw: dict[str, Any] = json.loads(Path(path).read_text())
    base = json.loads(_resolve(raw["base_ranges"], Path(path)).read_text())
    quiet = json.loads(_resolve(raw["quiet_ranges"], Path(path)).read_text())
    if rg.rows_for(base) != rg.rows_for(quiet) or base["dt_s"] != quiet["dt_s"]:
        raise ValueError("the mix's ranges must share rows and dt")
    fam = raw["families"]
    if set(fam) != set(FAMILIES) or abs(sum(fam.values()) - 1.0) > 1e-9:
        raise ValueError("families must be annex_b, randomised and quiet, summing to 1")
    kinds = raw["overlay"]["kinds"]
    if set(kinds) != set(OVERLAYS[1:]) or abs(sum(kinds.values()) - 1.0) > 1e-9:
        raise ValueError("overlay kinds must be correlated, outliers and both, summing to 1")
    if raw["overlay"]["corr_share"]["max"] >= 1.0 or raw["overlay"]["outlier_rate"]["max"] >= 1.0:
        raise ValueError("corr_share and outlier_rate must stay below 1")
    mix = Mix(
        raw,
        base,
        rg.flatten_ranges(base),
        rg.flatten_ranges(quiet),
        rg.rows_for(base),
        base["dt_s"],
    )
    for u in (0.0, 1.0):  # the family's corners must be ranges the generator accepts
        rg.validate_ranges(randomised_ranges(mix, np.full(N_DRAWS, u)))
    return mix


def _between(lim: dict[str, float], u: float) -> float:
    return float(lim["min"]) + (float(lim["max"]) - float(lim["min"])) * u


def randomised_ranges(mix: Mix, u: np.ndarray) -> dict[str, Any]:
    """The randomised-statistics family's ranges for one engagement's draws ``u``: the base
    ranges with their own leg mean (sd a fixed share of it), the turn-angle range and the
    maxima of turn rate, speed change and acceleration each scaled by its own factor, and
    perturbed kind weights."""
    p, base = mix.raw["randomised"], mix.base
    mean = _between(p["leg_mean_s"], float(u[U_LEG]))

    def scaled(key: str, draw: int, both: bool = False, cap: float = math.inf) -> dict[str, float]:
        """The base range with its maximum (``both``: and its minimum) times the factor."""
        k = _between(p["scale"], float(u[draw]))
        lo = float(base[key]["min"]) * (k if both else 1.0)
        return {"min": lo, "max": max(min(float(base[key]["max"]) * k, cap), lo)}

    course = _between(p["course_weight"], float(u[U_COURSE]))
    speed = (1.0 - course) * _between(p["speed_share_of_rest"], float(u[U_SPEED]))
    return {
        **base,
        "target_leg_length_s": {
            "mean": mean,
            "sd": float(p["leg_sd_over_mean"]) * mean,
            "min": float(p["leg_min_s"]),
        },
        "target_manoeuvre_angle_abs_rad": scaled(
            "target_manoeuvre_angle_abs_rad", U_ANGLE, True, math.pi
        ),
        "target_turn_rate_rad_s": scaled("target_turn_rate_rad_s", U_RATE),
        "target_speed_change_abs_mps": scaled("target_speed_change_abs_mps", U_DV),
        "target_speed_change_rate_mps2": scaled("target_speed_change_rate_mps2", U_ACC),
        "target_change_kind_weights": {
            "course": course,
            "speed": speed,
            "both": 1.0 - course - speed,
        },
    }


@njit(cache=True)
def _draws(stream_seed: uint64, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """([B] engagement seeds, [B, N_DRAWS] uniforms of each engagement's mix sub-stream)."""
    n = indices.shape[0]
    seeds = np.empty(n, dtype=np.uint64)
    u = np.empty((n, N_DRAWS))
    for b in range(n):
        seeds[b] = derive_seed(stream_seed, indices[b])
        s = create_rng(mix64(seeds[b] ^ MIX_STREAM))
        for j in range(N_DRAWS):
            u[b, j] = uniform01(s)
    return seeds, u


@njit(cache=True)
def _cuts(seeds: np.ndarray, samples: np.ndarray, lo: int) -> tuple[np.ndarray, np.ndarray]:
    """(first row [B], rows [B]) of each engagement's period: ``timelate.periods.cut``."""
    n = seeds.shape[0]
    first = np.zeros(n, dtype=np.int64)
    rows = np.empty(n, dtype=np.int64)
    for b in range(n):
        if samples[b] <= lo:
            rows[b] = samples[b]
            continue
        s = create_rng(mix64(seeds[b] ^ CUT_STREAM))
        rows[b] = lo + uniform_int(s, samples[b] - lo + 1)
        first[b] = uniform_int(s, samples[b] - rows[b] + 1)
    return first, rows


def assign(mix: Mix, u: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """From the draws [B, N_DRAWS]: (family [B], overlay [B], ranges rows [B, R_LEN], overlay
    conditions [B, M_LEN])."""
    n = u.shape[0]
    fam = mix.raw["families"]
    family = np.where(
        u[:, U_FAMILY] < fam["annex_b"],
        0,
        np.where(u[:, U_FAMILY] < fam["annex_b"] + fam["randomised"], 1, 2),
    ).astype(np.int8)
    R = np.where((family == 2)[:, None], mix.R_quiet[None, :], mix.R_base[None, :])
    for b in np.flatnonzero(family == 1):
        R[b] = rg.flatten_ranges(randomised_ranges(mix, u[b]))
    ov = mix.raw["overlay"]
    k = u[:, U_KIND]
    kind = np.where(
        k < ov["kinds"]["correlated"],
        1,
        np.where(k < ov["kinds"]["correlated"] + ov["kinds"]["outliers"], 2, 3),
    )
    overlay = np.where(u[:, U_OVERLAY] < ov["fraction"], kind, 0).astype(np.int8)
    M = np.full((n, mm.M_LEN), np.nan)
    corr = (overlay == 1) | (overlay == 3)
    out = (overlay == 2) | (overlay == 3)
    for col, key, draw, on in (
        (mm.M_CORR_TAU, "corr_tau_s", U_TAU, corr),
        (mm.M_CORR_SHARE, "corr_share", U_SHARE, corr),
        (mm.M_OUT_RATE, "outlier_rate", U_OUT_RATE, out),
        (mm.M_OUT_SPREAD, "outlier_spread", U_OUT_SPREAD, out),
    ):
        lo, hi = float(ov[key]["min"]), float(ov[key]["max"])
        M[on, col] = lo + (hi - lo) * u[on, draw]
    return family, overlay, R, M


@njit(parallel=True, cache=True)
def _fill(
    stream_seed: uint64,
    indices: np.ndarray,
    R: np.ndarray,
    M: np.ndarray,
    rmax: int,
    samples: np.ndarray,
    sigma: np.ndarray,
    redraws: np.ndarray,
    own: np.ndarray,
    tgt: np.ndarray,
    bearing: np.ndarray,
    valid: np.ndarray,
    man: np.ndarray,
) -> None:
    """Whole engagements: the kernel with each engagement's own ranges row, then the overlay
    where the engagement has one. ``man``: rows inside a target manoeuvre (start … end)."""
    for b in prange(indices.shape[0]):
        own_b = np.zeros((rmax, 4))
        tgt_b = np.zeros((rmax, 4))
        bearing_b = np.zeros(rmax)
        valid_b = np.zeros(rmax, dtype=np.bool_)
        clean = np.zeros(rmax)
        white = np.zeros(rmax)
        P = np.full(sc.P_LEN, np.nan)
        tm = np.zeros((sc.MAX_TM, sc.TM_COLS))
        TI = np.full(sc.TI_LEN, -1, dtype=np.int64)
        sp = np.zeros((sc.MAX_TM, 3), dtype=np.int64)
        stats = np.zeros(3)
        redraws[b] = sc.generate_parts_into(
            stream_seed,
            indices[b],
            R[b],
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
            clean,
            white,
        )
        if redraws[b] < 0:
            continue
        n_s = TI[sc.TI_SAMPLES]
        if not np.all(np.isnan(M[b])):
            eng = np.zeros(mm.E_LEN)
            comp = np.zeros((rmax, 4))
            outlier = np.zeros(rmax, dtype=np.bool_)
            mm.apply_mismatch(
                derive_seed(stream_seed, indices[b]),
                M[b],
                n_s,
                P[sc.P_DT],
                P[sc.P_SIGMA],
                clean,
                white,
                valid_b,
                bearing_b,
                eng,
                comp,
                outlier,
            )
        samples[b] = n_s
        sigma[b] = P[sc.P_SIGMA]
        for i in range(rmax):
            own[b, i, 0] = own_b[i, 0]
            own[b, i, 1] = own_b[i, 1]
            for c in range(4):
                tgt[b, i, c] = tgt_b[i, c]
            bearing[b, i] = bearing_b[i]
            valid[b, i] = valid_b[i]
        for j in range(max(TI[sc.TI_N_SPANS], 0)):
            for i in range(max(sp[j, 1], 0), min(sp[j, 2] + 1, n_s)):
                man[b, i] = True


def period_features(
    own: np.ndarray,
    bearing: np.ndarray,
    valid: np.ndarray,
    mask: np.ndarray,
    sigma: np.ndarray,
    rows: np.ndarray,
    dt: float,
) -> tuple[np.ndarray, np.ndarray]:
    """([B, R, 9] features, [B] frame rotation) of periods laid out from row 0: ``own``
    [B, R, 2], ``bearing``, ``valid``, ``mask`` [B, R], ``sigma`` and ``rows`` [B]. The one
    place the model's inputs are built: the training stream and ``tma2-tlpredict`` both call
    it."""
    b, r = mask.shape
    t = np.tile(np.arange(r, dtype=np.float64) * dt, (b, 1))
    f7, th = features(t, own, bearing, valid, mask, sigma)
    f = np.zeros((b, r, N_PERIOD_FEATURES), dtype=np.float32)
    f[..., :N_FEATURES] = f7
    f[..., N_FEATURES] = t / T_UNIT * mask
    f[..., N_FEATURES + 1] = (rows.astype(np.float64) * dt / T_UNIT)[:, None] * mask
    return f, th


def inputs_of(periods: list[Period], max_rows: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(features [B, max_rows, 9], mask [B, max_rows], frame rotation [B]) of stored periods:
    bearings, ownship and the stated sigma only (nothing of the target)."""
    n = len(periods)
    own = np.zeros((n, max_rows, 2))
    bearing = np.zeros((n, max_rows))
    valid = np.zeros((n, max_rows), dtype=bool)
    mask = np.zeros((n, max_rows), dtype=bool)
    for i, p in enumerate(periods):
        if p.rows > max_rows:
            raise ValueError(f"period {p.ordinal}: {p.rows} rows, the model reads {max_rows}")
        a, b = p.first, p.first + p.rows
        own[i, : p.rows] = p.own[a:b, 1:3]
        bearing[i, : p.rows] = p.obs[a:b, 1]
        valid[i, : p.rows] = p.obs[a:b, 2] != 0
        mask[i, : p.rows] = True
    sigma = np.array([float(p.meta["parameters"]["noise_sigma_rad"]) for p in periods])
    rows = np.array([p.rows for p in periods], dtype=np.int64)
    dts = {p.dt for p in periods}
    if len(dts) > 1:
        raise ValueError("periods of one batch must share dt")
    f, th = period_features(own, bearing, valid, mask, sigma, rows, dts.pop() if dts else 5.0)
    return f, mask, th


def periods_at(cfg: RegressorConfig, mix: Mix, indices: np.ndarray) -> PeriodTensors:
    """The periods of the given engagement indices of the stream."""
    if mix.rmax > cfg.max_rows:
        raise ValueError(f"an engagement has up to {mix.rmax} rows; max_rows is {cfg.max_rows}")
    idx = np.asarray(indices, dtype=np.int64)
    n, rmax = idx.shape[0], mix.rmax
    seed = np.uint64(cfg.stream_seed)
    seeds, u = _draws(seed, idx)
    family, overlay, R, M = assign(mix, u)
    samples = np.zeros(n, dtype=np.int64)
    sigma = np.zeros(n)
    redraws = np.zeros(n, dtype=np.int64)
    own = np.zeros((n, rmax, 2))
    tgt = np.zeros((n, rmax, 4))
    bearing = np.zeros((n, rmax))
    valid = np.zeros((n, rmax), dtype=np.bool_)
    man = np.zeros((n, rmax), dtype=np.bool_)
    _fill(seed, idx, R, M, rmax, samples, sigma, redraws, own, tgt, bearing, valid, man)
    bad = np.flatnonzero(redraws < 0)
    if bad.size:
        raise ValueError(
            f"engagement {int(idx[bad[0]])}: no valid geometry after {sc.MAX_REDRAWS} redraws"
        )
    first, rows = _cuts(seeds, samples, int(round(MIN_SECONDS / mix.dt)))
    r = cfg.max_rows
    k = np.arange(r)[None, :]
    mask = k < rows[:, None]
    src = np.minimum(first[:, None] + k, rmax - 1)
    take = np.arange(n)[:, None]
    own_p, tgt_p = own[take, src], tgt[take, src]
    f, th = period_features(own_p, bearing[take, src], valid[take, src], mask, sigma, rows, mix.dt)
    y = targets(own_p, tgt_p, th) * mask[..., None]
    return PeriodTensors(f, y, mask, man[take, src] & mask, idx, first, rows, family, overlay, M)


def batch_at(cfg: RegressorConfig, mix: Mix, update: int) -> PeriodTensors:
    """Update ``update``'s batch of periods (a pure function of the configuration and mix)."""
    return periods_at(cfg, mix, stream_indices(cfg, update))


def monitor(cfg: RegressorConfig, mix: Mix) -> PeriodTensors:
    """The training monitor: ``val_count`` periods of the SAME stream seed, at indices from
    ``monitor_start`` (2^40 by default; training reads from ``stream_start``, far below).
    Never a validation or test seed."""
    return periods_at(cfg, mix, cfg.monitor_start + np.arange(cfg.val_count, dtype=np.int64))


def token_targets(
    x: PeriodTensors, patch: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per token of ``patch`` rows from the period's start: (state target [B, T, 3] at the
    token's last existing row, manoeuvre label [B, T]: any of its rows inside a manoeuvre,
    exists [B, T]: its first row exists, last existing row [B, T])."""
    b, r = x.mask.shape
    t = r // patch
    start = np.arange(t) * patch
    exists = x.mask[:, start]
    last = np.minimum(start[None, :] + patch - 1, np.maximum(x.rows[:, None] - 1, 0))
    y = x.y[np.arange(b)[:, None], last] * exists[..., None]
    label = x.man.reshape(b, t, patch).any(axis=2)
    return y, label.astype(np.float32), exists.astype(np.float32), last
