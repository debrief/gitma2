"""``tma2-ranges``: describe the manoeuvre model a ranges file selects (spec 006, FR-053).

    uv run tma2-ranges --describe configs/man2-ranges.json [--sample 10000 --seed 314]

Without ``--sample`` it prints what the file asks for. With it, it generates the scenarios in
memory and prints what came out: leg lengths (complete legs inside the window, which favours short
legs), transition durations, changes per engagement, change kinds, wander kinds and how often the
ownship zig overlaps a target change. Exit 0; it is a diagnostic.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from tma2.sim.generate import generate_scenario
from tma2.sim.ranges import flatten_ranges, rows_for

_Z95 = 1.6448536269514722


def _deg(x: float) -> float:
    return math.degrees(x)


def describe(r: dict[str, Any]) -> list[str]:
    flatten_ranges(r)  # validates
    out: list[str] = []
    leg = r.get("target_leg_length_s")
    if leg is not None:
        sem = "generator 0.6.0 leg model (MAN2)"
    elif r.get("target_course_change_count_weights") is not None:
        sem = "generator 0.5.0 manoeuvre count model"
    elif r.get("target_manoeuvre_fraction") is not None:
        sem = "generator 0.4.0 single target turn"
    else:
        sem = "constant-velocity target (generator 0.3.0 or earlier)"
    w = r["window_s"]
    out.append(f"semantics: {sem}")
    out.append(
        f"window: {w['min'] / 60:.0f}–{w['max'] / 60:.0f} min at dt {r['dt_s']:g} s "
        f"({rows_for(r)} rows)"
    )
    if leg is not None:
        m, sd, lo = leg["mean"], leg["sd"], leg["min"]
        p5, p95 = max(lo, m - _Z95 * sd), m + _Z95 * sd
        share = 0.5 * (1.0 + math.erf((600.0 - m) / (sd * math.sqrt(2.0))))
        out.append(
            f"target legs: N({m / 60:.1f}, {sd / 60:.1f}) min, floor {lo / 60:.1f} min; "
            f"P5/P50/P95 {p5 / 60:.1f} / {m / 60:.1f} / {p95 / 60:.1f} min; "
            f"P(leg ≤ 10 min) {share:.3f}"
        )
        k = r.get("target_change_kind_weights") or {"course": 1, "speed": 0, "both": 0}
        tot = k["course"] + k["speed"] + k["both"]
        out.append(
            f"leg ends: course {k['course'] / tot:.2f}, speed {k['speed'] / tot:.2f}, "
            f"both {k['both'] / tot:.2f}"
        )
    ang = r.get("target_manoeuvre_angle_abs_rad")
    rate = r.get("target_turn_rate_rad_s")
    if ang is not None and rate is not None:
        out.append(
            f"turns: {_deg(ang['min']):.0f}–{_deg(ang['max']):.0f}° at "
            f"{_deg(rate['min']):.2f}–{_deg(rate['max']):.2f}°/s, so "
            f"{ang['min'] / rate['max']:.0f}–{ang['max'] / rate['min']:.0f} s"
        )
    dv = r.get("target_speed_change_abs_mps")
    acc = r.get("target_speed_change_rate_mps2")
    if dv is not None and acc is not None:
        out.append(
            f"speed changes: {dv['min'] / 0.514444:.1f}–{dv['max'] / 0.514444:.1f} kt at "
            f"{acc['min']:.3f}–{acc['max']:.3f} m/s², so "
            f"{dv['min'] / acc['max']:.0f}–{dv['max'] / acc['min']:.0f} s"
        )
    ww = r.get("ownship_wander_weights")
    if ww is not None:
        hw = r.get("ownship_wander")
        osc = r.get("ownship_oscillation")
        parts = [f"weights none {ww['none']:g}, wander {ww['wander']:g}, "]
        parts.append(f"oscillation {ww['oscillation']:g}, both {ww['both']:g}")
        if hw is not None:
            parts.append(
                f"; helm wander sd {_deg(hw['sd_rad']):.1f}°, τ {hw['tau_s']:g} s, "
                f"clip {_deg(hw['clip_rad']):.1f}°"
            )
        if osc is not None:
            parts.append(
                f"; oscillation {_deg(osc['amp_rad']['min']):.1f}–"
                f"{_deg(osc['amp_rad']['max']):.1f}°, period "
                f"{osc['period_s']['min']:g}–{osc['period_s']['max']:g} s"
            )
        out.append("ownship wander: " + "".join(parts))
    return out


def sample(r: dict[str, Any], n: int, seed: int) -> list[str]:
    legs: list[float] = []
    trans: list[float] = []
    changes: list[int] = []
    kinds: collections.Counter[str] = collections.Counter()
    wander: collections.Counter[str] = collections.Counter()
    zom = 0
    for i in range(n):
        m = generate_scenario(seed, i, r).scenario.metadata
        dt = float(m.parameters.dt_s)
        spans = m.manoeuvres or []
        changes.append(len(spans))
        for sp in spans:
            kinds[str(getattr(sp.kind, "value", sp.kind))] += 1
            trans.append((sp.end_index - sp.start_index + 1) * dt)
        for a, b in zip(spans, spans[1:], strict=False):
            legs.append((b.start_index - 1 - a.end_index) * dt / 60.0)
        if m.ownship_wander is not None:
            wander[str(getattr(m.ownship_wander.kind, "value", m.ownship_wander.kind))] += 1
        zom += bool(m.zig_on_manoeuvre)
    out = [f"sample: {n} scenarios, seed {seed}"]
    if legs:
        q = np.quantile(legs, [0.05, 0.5, 0.95])
        out.append(
            f"complete legs in the window: {len(legs)}; P5/P50/P95 "
            f"{q[0]:.1f} / {q[1]:.1f} / {q[2]:.1f} min; share ≤ 10 min "
            f"{np.mean(np.asarray(legs) <= 10.0):.3f} (complete legs favour short ones)"
        )
    if trans:
        q = np.quantile(trans, [0.1, 0.5, 0.9])
        out.append(f"transitions: P10/P50/P90 {q[0]:.0f} / {q[1]:.0f} / {q[2]:.0f} s")
    counts = np.bincount(np.asarray(changes, dtype=np.int64))
    dist = ", ".join(f"{k}: {c / n:.2f}" for k, c in enumerate(counts) if c)
    out.append(
        f"changes per engagement: {dist}; two or more {np.mean(np.asarray(changes) >= 2):.2f}"
    )
    out.append("change kinds: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    if wander:
        out.append("wander drawn: " + ", ".join(f"{k} {v}" for k, v in sorted(wander.items())))
    out.append(f"ownship zig overlapping a target change: {zom} of {n}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-ranges", description=__doc__.split("\n")[0])
    ap.add_argument("--describe", required=True, metavar="RANGES")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=314)
    a = ap.parse_args(argv)
    r = json.loads(Path(a.describe).read_text(encoding="utf-8"))
    lines = describe(r)
    if a.sample > 0:
        lines += sample(r, a.sample, a.seed)
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
