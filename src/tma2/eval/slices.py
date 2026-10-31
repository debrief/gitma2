"""Slicing keys (gitma ``packages/eval/src/slices.ts``): range band by mean range, zig band by
|zig angle|, noise σ, dropout band and the target's manoeuvre plan."""

from __future__ import annotations

from typing import Any

from tma2.sim.geometry import rad_to_deg

RANGE_BANDS_KM = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 30)]
ZIG_BANDS_DEG = [(30, 50), (50, 70), (70, 90), (90, 120), (120, 150), (150, 180)]
MANOEUVRE_BANDS_DEG = [(30, 60), (60, 90), (90, 120)]
DROPOUT_BANDS_PCT = [(0, 5), (5, 10)]


def _js(n: float) -> str:
    """Integers print without a decimal (gitma's ``String(lo)`` on integer bands)."""
    return str(int(n)) if float(n).is_integer() else repr(n)


def band(value: float, bands: list[tuple[int, int]], unit: str) -> str:
    for lo, hi in bands:
        if value >= lo and value < hi:
            return f"{_js(lo)}-{_js(hi)}{unit}"
    last = bands[-1]
    if value >= last[1]:
        return f"{_js(last[1])}+{unit}"
    return "other"


def zig_band(deg: float) -> str:
    if 90 <= deg < 90.001:
        return "70-90deg"
    if 180 <= deg < 180.001:
        return "150-180deg"
    if 29.999 < deg < 30:
        return "30-50deg"
    return band(deg, ZIG_BANDS_DEG, "deg")


def dropout_band(fraction: float) -> str:
    pct = fraction * 100
    b = band(pct, DROPOUT_BANDS_PCT, "pct")
    return "5-10pct" if (b == "10+pct" and pct < 10.001) else b


def manoeuvre_band(m: dict[str, Any]) -> str:
    plan = m["parameters"].get("target_manoeuvres")
    if plan is not None:
        turns = sum(1 for x in plan if x["kind"] == "course")
        speed = any(x["kind"] == "speed" for x in plan)
        if turns == 0 and not speed:
            return "held"
        return f"{turns}turn{'' if turns == 1 else 's'}{'+speed' if speed else ''}"
    a = m["parameters"].get("target_manoeuvre_angle_rad")
    if a is None:
        return "held"
    deg = abs(rad_to_deg(float(a)))
    if 120 <= deg < 120.001:
        return "90-120deg"
    if 29.999 < deg < 30:
        return "30-60deg"
    return band(deg, MANOEUVRE_BANDS_DEG, "deg")


def _sigma_label(sigma_rad: float) -> str:
    """JavaScript ``Math.round(x * 100) / 100`` then ``String``: 1 → "1", 0.5 → "0.5"."""
    import math

    v = math.floor(rad_to_deg(sigma_rad) * 100 + 0.5) / 100
    return _js(v)


def slice_keys(m: dict[str, Any]) -> list[str]:
    """Every slice a scenario belongs to, "overall" first."""
    p = m["parameters"]
    return [
        "overall",
        f"range_band={band(float(m['mean_range_m']) / 1000, RANGE_BANDS_KM, 'km')}",
        f"zig_band={zig_band(abs(rad_to_deg(float(p['zig_angle_rad']))))}",
        f"sigma={_sigma_label(float(p['noise_sigma_rad']))}deg",
        f"dropout_band={dropout_band(float(p['dropout_fraction']))}",
        f"manoeuvre={manoeuvre_band(m)}",
    ]
