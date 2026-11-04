"""Parameter ranges: validation (gitma's messages) and the flat numeric layout the kernel reads.

The kernel (``scenario.py``) is a numba function and cannot take Pydantic objects, so a
``ParameterRanges`` is flattened to a float64 array ``R`` indexed by the ``R_*`` constants below.
Absent optional groups are NaN; lists are padded to ``LIST_MAX`` with their lengths stored.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .geometry import deg_to_rad, kt_to_mps

LIST_MAX = 8
MAX_COUNT_WEIGHTS = 4  # 0.5.0 count model: at most 3 course changes + 1 speed change

# Layout of the flat ranges array (float64). Keep in step with ``flatten_ranges``.
R_WINDOW_MIN = 0
R_WINDOW_MAX = 1
R_DT = 2
R_OWN_SPEED_MIN = 3
R_OWN_SPEED_MAX = 4
R_ZIG_ABS_MIN = 5
R_ZIG_ABS_MAX = 6
R_ZIG_FRAC_MIN = 7
R_ZIG_FRAC_MAX = 8
R_RANGE0_MIN = 9
R_RANGE0_MAX = 10
R_RANGE_LOG_UNIFORM = 11  # 1 log-uniform, 0 uniform
R_TGT_SPEED_MIN = 12
R_TGT_SPEED_MAX = 13
R_N_SIGMA = 14
R_SIGMA0 = 15  # LIST_MAX slots
R_DROPOUT_MIN = R_SIGMA0 + LIST_MAX
R_DROPOUT_MAX = R_DROPOUT_MIN + 1
R_MIN_RANGE = R_DROPOUT_MAX + 1
R_TURN_RATE_MIN = R_MIN_RANGE + 1  # NaN when absent
R_TURN_RATE_MAX = R_TURN_RATE_MIN + 1
R_ACROSS_LOS = R_TURN_RATE_MAX + 1  # 1 when zig_rule == across_los
R_LOS_MIN = R_ACROSS_LOS + 1  # NaN when absent
R_LOS_MAX = R_LOS_MIN + 1
R_ZIG2_DELAY_MIN = R_LOS_MAX + 1  # NaN when absent
R_ZIG2_DELAY_MAX = R_ZIG2_DELAY_MIN + 1
R_TM_FRACTION = R_ZIG2_DELAY_MAX + 1  # 0.4.0 target_manoeuvre_fraction; NaN when absent
R_TM_ANGLE_MIN = R_TM_FRACTION + 1
R_TM_ANGLE_MAX = R_TM_ANGLE_MIN + 1
R_TM_RATE_MIN = R_TM_ANGLE_MAX + 1
R_TM_RATE_MAX = R_TM_RATE_MIN + 1
R_TM_AFTER = R_TM_RATE_MAX + 1
R_TM_MARGIN = R_TM_AFTER + 1
R_N_WEIGHTS = R_TM_MARGIN + 1  # 0.5.0: number of count weights; 0 when absent
R_WEIGHT0 = R_N_WEIGHTS + 1  # LIST_MAX slots
R_SPEED_CHANGE_FRACTION = R_WEIGHT0 + LIST_MAX
R_DV_MIN = R_SPEED_CHANGE_FRACTION + 1  # NaN when absent
R_DV_MAX = R_DV_MIN + 1
R_ACC_MIN = R_DV_MAX + 1
R_ACC_MAX = R_ACC_MIN + 1
R_TM_SPACING = R_ACC_MAX + 1
# Generator 0.6.0 (SRD Annex B, MAN2); NaN when absent.
R_LEG_MEAN = R_TM_SPACING + 1
R_LEG_SD = R_LEG_MEAN + 1
R_LEG_MIN = R_LEG_SD + 1
R_KIND_COURSE = R_LEG_MIN + 1  # change-kind weights, normalised at flatten time
R_KIND_SPEED = R_KIND_COURSE + 1
R_KIND_BOTH = R_KIND_SPEED + 1
R_WANDER_SD = R_KIND_BOTH + 1
R_WANDER_TAU = R_WANDER_SD + 1
R_WANDER_CLIP = R_WANDER_TAU + 1
R_OSC_AMP_MIN = R_WANDER_CLIP + 1
R_OSC_AMP_MAX = R_OSC_AMP_MIN + 1
R_OSC_PERIOD_MIN = R_OSC_AMP_MAX + 1
R_OSC_PERIOD_MAX = R_OSC_PERIOD_MIN + 1
R_WW_NONE = R_OSC_PERIOD_MAX + 1  # wander-kind weights, normalised
R_WW_WANDER = R_WW_NONE + 1
R_WW_OSC = R_WW_WANDER + 1
R_WW_BOTH = R_WW_OSC + 1
R_LEN = R_WW_BOTH + 1

DEFAULT_RANGES: dict[str, Any] = {
    "window_s": {"min": 600, "max": 2400},
    "dt_s": 10,
    "ownship_speed_mps": {"min": kt_to_mps(5), "max": kt_to_mps(15)},
    "zig_angle_abs_rad": {"min": deg_to_rad(30), "max": deg_to_rad(90)},
    "zig_fraction": {"min": 0.4, "max": 0.6},
    "target_range0_m": {"min": 2000, "max": 20000},
    "range_distribution": "log_uniform",
    "target_speed_mps": {"min": kt_to_mps(3), "max": kt_to_mps(20)},
    "noise_sigma_rad_values": [deg_to_rad(0.5), deg_to_rad(1), deg_to_rad(2)],
    "dropout_fraction": {"min": 0, "max": 0.1},
    "min_range_m": 100,
}
"""Iteration-1 ranges, as gitma ``DEFAULT_RANGES`` (``packages/sim/src/ranges.ts``)."""

HELDOUT_RANGES: dict[str, Any] = {**DEFAULT_RANGES, "target_range0_m": {"min": 20000, "max": 30000}}


def noise_free(ranges: dict[str, Any]) -> dict[str, Any]:
    """The same ranges with σ = 0 and no dropouts (G0)."""
    return {**ranges, "noise_sigma_rad_values": [0], "dropout_fraction": {"min": 0, "max": 0}}


def rows_for(ranges: dict[str, Any]) -> int:
    """Padded rows per window: floor(window_s.max / dt_s) (gitma ``rowsFor``)."""
    return int(math.floor(ranges["window_s"]["max"] / ranges["dt_s"]))


class RangesError(ValueError):
    """A ranges file that gitma would refuse, with gitma's message."""


def validate_ranges(r: dict[str, Any]) -> None:
    """Raise ``RangesError`` for the combinations gitma's generator throws on."""
    if r.get("zig_rule") == "across_los" and r.get("los_offset_rad") is None:
        raise RangesError("zig_rule across_los needs los_offset_rad")
    if r.get("target_manoeuvre_fraction") is not None and any(
        r.get(k) is None
        for k in (
            "target_manoeuvre_angle_abs_rad",
            "target_turn_rate_rad_s",
            "target_manoeuvre_after_zig_s",
            "target_manoeuvre_margin_s",
        )
    ):
        raise RangesError(
            "target_manoeuvre_fraction needs target_manoeuvre_angle_abs_rad, "
            "target_turn_rate_rad_s, target_manoeuvre_after_zig_s and target_manoeuvre_margin_s"
        )
    weights = r.get("target_course_change_count_weights")
    if weights is not None:
        speed_fraction = r.get("target_speed_change_fraction") or 0
        missing = any(
            r.get(k) is None
            for k in (
                "target_manoeuvre_angle_abs_rad",
                "target_turn_rate_rad_s",
                "target_manoeuvre_after_zig_s",
                "target_manoeuvre_margin_s",
                "target_manoeuvre_spacing_s",
            )
        ) or (
            speed_fraction > 0
            and (
                r.get("target_speed_change_abs_mps") is None
                or r.get("target_speed_change_rate_mps2") is None
            )
        )
        if missing:
            raise RangesError(
                "target_course_change_count_weights needs target_manoeuvre_angle_abs_rad, "
                "target_turn_rate_rad_s, target_manoeuvre_after_zig_s, "
                "target_manoeuvre_margin_s and target_manoeuvre_spacing_s (and the speed-change "
                "ranges when there are speed changes)"
            )
        if r.get("target_manoeuvre_fraction") is not None:
            raise RangesError(
                "target_manoeuvre_fraction and target_course_change_count_weights are exclusive"
            )
        if len(weights) > MAX_COUNT_WEIGHTS:
            raise RangesError(
                f"at most {MAX_COUNT_WEIGHTS} count weights (0 to {MAX_COUNT_WEIGHTS - 1} course "
                "changes) are supported by the kernel's fixed manoeuvre table"
            )
    if len(r["noise_sigma_rad_values"]) > LIST_MAX:
        raise RangesError(f"at most {LIST_MAX} noise sigma values are supported")
    # generator 0.6.0
    leg = r.get("target_leg_length_s")
    if leg is not None:
        clash = [
            k
            for k in (
                "target_course_change_count_weights",
                "target_manoeuvre_spacing_s",
                "target_manoeuvre_after_zig_s",
                "target_manoeuvre_margin_s",
                "target_manoeuvre_fraction",
            )
            if r.get(k) is not None
        ]
        if clash:
            raise RangesError(
                "target_leg_length_s cannot be combined with target_course_change_count_weights, "
                "target_manoeuvre_spacing_s, target_manoeuvre_after_zig_s, "
                "target_manoeuvre_margin_s or target_manoeuvre_fraction"
            )
        if not (float(leg["mean"]) > 0 and float(leg["sd"]) > 0 and float(leg["min"]) > 0):
            raise RangesError("target_leg_length_s mean, sd and min must be positive")
        if float(leg["min"]) < 2 * float(r["dt_s"]):
            # a shorter leg can round into the previous change's last row
            raise RangesError("target_leg_length_s.min must be at least two rows (2 × dt_s)")
        from .scenario import MAX_TM

        # each start rounds to a row, which can shorten a leg by up to one row
        dt = float(r["dt_s"])
        if float(r["window_s"]["max"]) / (float(leg["min"]) - dt) + 2 > MAX_TM:
            raise RangesError(
                f"target_leg_length_s.min is too short for window_s.max: the kernel's table holds "
                f"{MAX_TM} changes"
            )
        if any(
            r.get(k) is None for k in ("target_manoeuvre_angle_abs_rad", "target_turn_rate_rad_s")
        ):
            raise RangesError(
                "target_leg_length_s needs target_manoeuvre_angle_abs_rad and "
                "target_turn_rate_rad_s"
            )
        kinds = r.get("target_change_kind_weights")
        if kinds is not None and (kinds.get("speed", 0) > 0 or kinds.get("both", 0) > 0):
            if (
                r.get("target_speed_change_abs_mps") is None
                or r.get("target_speed_change_rate_mps2") is None
            ):
                raise RangesError(
                    "target_change_kind_weights with speed or both needs "
                    "target_speed_change_abs_mps and target_speed_change_rate_mps2"
                )
            if not (
                float(r["target_speed_change_abs_mps"]["min"]) > 0
                and float(r["target_speed_change_rate_mps2"]["min"]) > 0
            ):
                raise RangesError(
                    "target_speed_change_abs_mps and target_speed_change_rate_mps2 must be "
                    "positive when speed or both changes are drawn"
                )
    elif r.get("target_change_kind_weights") is not None:
        raise RangesError("target_change_kind_weights needs target_leg_length_s")
    if (r.get("ownship_wander") is not None or r.get("ownship_oscillation") is not None) and r.get(
        "ownship_wander_weights"
    ) is None:
        raise RangesError("ownship_wander or ownship_oscillation needs ownship_wander_weights")
    for key, names in (
        ("target_change_kind_weights", ("course", "speed", "both")),
        ("ownship_wander_weights", ("none", "wander", "oscillation", "both")),
    ):
        w = r.get(key)
        if w is None:
            continue
        missing = [n for n in names if n not in w]
        if missing:
            raise RangesError(f"{key} needs every weight: {', '.join(names)}")
        vals = [float(w[n]) for n in names]
        if any(v < 0 for v in vals) or sum(vals) <= 0:
            raise RangesError(f"{key} must be non-negative with a positive sum")
    hw = r.get("ownship_wander")
    if hw is not None and not (
        float(hw["sd_rad"]) >= 0 and float(hw["tau_s"]) > 0 and float(hw["clip_rad"]) > 0
    ):
        raise RangesError("ownship_wander needs sd_rad ≥ 0, tau_s > 0 and clip_rad > 0")
    osc = r.get("ownship_oscillation")
    if osc is not None and not (
        0 <= float(osc["amp_rad"]["min"]) <= float(osc["amp_rad"]["max"])
        and 0 < float(osc["period_s"]["min"]) <= float(osc["period_s"]["max"])
    ):
        raise RangesError("ownship_oscillation needs 0 ≤ amp min ≤ max and 0 < period min ≤ max")
    ww = r.get("ownship_wander_weights")
    if ww is not None:
        if (float(ww["wander"]) > 0 or float(ww["both"]) > 0) and r.get("ownship_wander") is None:
            raise RangesError("ownship_wander_weights with wander or both needs ownship_wander")
        if (float(ww["oscillation"]) > 0 or float(ww["both"]) > 0) and r.get(
            "ownship_oscillation"
        ) is None:
            raise RangesError(
                "ownship_wander_weights with oscillation or both needs ownship_oscillation"
            )


def flatten_ranges(r: dict[str, Any]) -> np.ndarray:
    """``ParameterRanges`` (as a plain dict) → the flat float64 array the kernel reads."""
    validate_ranges(r)
    out = np.full(R_LEN, np.nan, dtype=np.float64)

    def rng(key: str, lo_i: int, hi_i: int) -> None:
        v = r.get(key)
        if v is not None:
            out[lo_i] = float(v["min"])
            out[hi_i] = float(v["max"])

    rng("window_s", R_WINDOW_MIN, R_WINDOW_MAX)
    out[R_DT] = float(r["dt_s"])
    rng("ownship_speed_mps", R_OWN_SPEED_MIN, R_OWN_SPEED_MAX)
    rng("zig_angle_abs_rad", R_ZIG_ABS_MIN, R_ZIG_ABS_MAX)
    rng("zig_fraction", R_ZIG_FRAC_MIN, R_ZIG_FRAC_MAX)
    rng("target_range0_m", R_RANGE0_MIN, R_RANGE0_MAX)
    out[R_RANGE_LOG_UNIFORM] = 1.0 if r["range_distribution"] == "log_uniform" else 0.0
    rng("target_speed_mps", R_TGT_SPEED_MIN, R_TGT_SPEED_MAX)
    sigmas = r["noise_sigma_rad_values"]
    out[R_N_SIGMA] = len(sigmas)
    for i, s in enumerate(sigmas):
        out[R_SIGMA0 + i] = float(s)
    rng("dropout_fraction", R_DROPOUT_MIN, R_DROPOUT_MAX)
    out[R_MIN_RANGE] = float(r["min_range_m"])
    rng("ownship_turn_rate_rad_s", R_TURN_RATE_MIN, R_TURN_RATE_MAX)
    out[R_ACROSS_LOS] = 1.0 if r.get("zig_rule") == "across_los" else 0.0
    rng("los_offset_rad", R_LOS_MIN, R_LOS_MAX)
    rng("zig2_delay_s", R_ZIG2_DELAY_MIN, R_ZIG2_DELAY_MAX)
    if r.get("target_manoeuvre_fraction") is not None:
        out[R_TM_FRACTION] = float(r["target_manoeuvre_fraction"])
    rng("target_manoeuvre_angle_abs_rad", R_TM_ANGLE_MIN, R_TM_ANGLE_MAX)
    rng("target_turn_rate_rad_s", R_TM_RATE_MIN, R_TM_RATE_MAX)
    if r.get("target_manoeuvre_after_zig_s") is not None:
        out[R_TM_AFTER] = float(r["target_manoeuvre_after_zig_s"])
    if r.get("target_manoeuvre_margin_s") is not None:
        out[R_TM_MARGIN] = float(r["target_manoeuvre_margin_s"])
    weights = r.get("target_course_change_count_weights")
    out[R_N_WEIGHTS] = 0.0 if weights is None else float(len(weights))
    if weights is not None:
        for i, w in enumerate(weights):
            out[R_WEIGHT0 + i] = float(w)
    out[R_SPEED_CHANGE_FRACTION] = float(r.get("target_speed_change_fraction") or 0.0)
    rng("target_speed_change_abs_mps", R_DV_MIN, R_DV_MAX)
    rng("target_speed_change_rate_mps2", R_ACC_MIN, R_ACC_MAX)
    if r.get("target_manoeuvre_spacing_s") is not None:
        out[R_TM_SPACING] = float(r["target_manoeuvre_spacing_s"])
    # generator 0.6.0
    leg = r.get("target_leg_length_s")
    if leg is not None:
        out[R_LEG_MEAN] = float(leg["mean"])
        out[R_LEG_SD] = float(leg["sd"])
        out[R_LEG_MIN] = float(leg["min"])
        kinds = r.get("target_change_kind_weights") or {"course": 1.0, "speed": 0.0, "both": 0.0}
        tot = float(kinds["course"]) + float(kinds["speed"]) + float(kinds["both"])
        out[R_KIND_COURSE] = float(kinds["course"]) / tot
        out[R_KIND_SPEED] = float(kinds["speed"]) / tot
        out[R_KIND_BOTH] = float(kinds["both"]) / tot
    w = r.get("ownship_wander")
    if w is not None:
        out[R_WANDER_SD] = float(w["sd_rad"])
        out[R_WANDER_TAU] = float(w["tau_s"])
        out[R_WANDER_CLIP] = float(w["clip_rad"])
    o = r.get("ownship_oscillation")
    if o is not None:
        out[R_OSC_AMP_MIN] = float(o["amp_rad"]["min"])
        out[R_OSC_AMP_MAX] = float(o["amp_rad"]["max"])
        out[R_OSC_PERIOD_MIN] = float(o["period_s"]["min"])
        out[R_OSC_PERIOD_MAX] = float(o["period_s"]["max"])
    ww = r.get("ownship_wander_weights")
    if ww is not None:
        tot = sum(float(ww[k]) for k in ("none", "wander", "oscillation", "both"))
        out[R_WW_NONE] = float(ww["none"]) / tot
        out[R_WW_WANDER] = float(ww["wander"]) / tot
        out[R_WW_OSC] = float(ww["oscillation"]) / tot
        out[R_WW_BOTH] = float(ww["both"]) / tot
    return out
