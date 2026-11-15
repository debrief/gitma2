"""Spec 019: the diagnostic's tables, generated from its ``summary.json``.

    uv run python scripts/research/tl7_tables.py <experiment dir> [--out tables.md]

Each ladder system against the standing control (declared) in range, course and speed,
with its period count, the median per-period ratio, the share of its gain in the ten best
periods and the ratio with those set aside; against the true prior; and its manoeuvres
missed and false at a 120 s match. Development work on used periods.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

NAMES = [
    ("lad-0", "the broadened prior"),
    ("lad-1", "+ the truth's legs"),
    ("lad-2", "+ its turn sizes"),
    ("lad-3", "+ its turn rates"),
    ("lad-4", "+ its speed changes"),
    ("lad-5", "+ its kinds: the true prior"),
    ("one-angle", "turn sizes alone"),
    ("one-rate", "turn rates alone"),
    ("one-speed", "speed changes alone"),
    ("one-kinds", "kinds alone"),
]


def ci(v: dict[str, Any] | None) -> str:
    if not v:
        return "–"
    return f"{v['geometric_mean']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}]"


def f(x: Any, d: int = 2) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return f"{x:.{d}f}"


def tables(summary: dict[str, Any]) -> str:
    out: list[str] = []
    for split, r in summary["splits"].items():
        lad = r["ladder"]
        names = [(k, lab) for k, lab in NAMES if k in lad]
        names += [
            (k, "the nearest family member, its own search")
            for k in sorted(lad)
            if k.startswith("mem-")
        ]
        out += [
            f"## {split}: {r['periods']} periods, {r['periods_scored']} scored",
            "",
            "### Standing control ÷ system (above 1: the system is better)",
            "",
            "| System | Prior | Periods | Range | Median per-period | Course | Speed | Share of the range gain in the ten best periods | Range without them |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for k, lab in names:
            v = lad[k]["vs_control"] or {}
            rng = v.get("range")
            c = lad[k].get("concentration") or {}
            out += [
                f"| `{k}` | {lab} | {rng['periods'] if rng else '–'} | {ci(rng)} | "
                f"{f(rng['median_ratio']) if rng else '–'} | {ci(v.get('course'))} | {ci(v.get('speed'))} | "
                f"{f(c.get('share_in_top'))} | {f(c.get('ratio_without_top'))} |"
            ]
        out += [
            "",
            "### System ÷ the true prior's search (above 1: the true prior is better)",
            "",
            "| System | Range | Course | Speed |",
            "| --- | --- | --- | --- |",
        ]
        for k, _lab in names:
            v = lad[k].get("vs_true") or {}
            if v:
                out += [
                    f"| `{k}` | {ci(v.get('range'))} | {ci(v.get('course'))} | {ci(v.get('speed'))} |"
                ]
        out += [
            "",
            "### Manoeuvres, matched within 120 s",
            "",
            "| System | Missed (share) | False (per period) | Periods without a track |",
            "| --- | --- | --- | --- |",
        ]
        ctl = (r.get("counts") or {}).get("ctl-d1-q0.01")
        if ctl:
            out += [
                f"| `ctl-d1-q0.01` | {f(ctl['120']['missed_share'])} | {f(ctl['120']['false_per_period'])} | – |"
            ]
        for k, _lab in names:
            c = lad[k].get("counts")
            if c:
                out += [
                    f"| `{k}` | {f(c['120']['missed_share'])} | {f(c['120']['false_per_period'])} | "
                    f"{lad[k]['periods_without_a_track']} |"
                ]
        secs = r.get("seconds_per_period") or {}
        out += ["", f"Seconds per period, all searches: {sum(secs.values()):.0f}.", ""]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    text = tables(json.loads((Path(a.dir) / "summary.json").read_text()))
    if a.out:
        Path(a.out).write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
