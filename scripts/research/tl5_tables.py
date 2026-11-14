"""Spec 017: every table of a record, generated from its ``summary.json`` (FR-013).

    uv run python scripts/research/tl5_tables.py <experiment dir> [--out tables.md]

Prints Markdown: the systems' median period range error; how detectable the whole true
manoeuvres are and how often each system misses them by detectability band; the gap from
each system to the true-history reference split into an attainable share and
identifiability at each threshold; the paired comparisons the plan names, each with its
median per-period ratio and the shares over twice as bad on either side; manoeuvre counts.
A test checks that a record's ``tables.md`` equals what this prints for its summary.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SPLITS = [
    ("man2", "Annex B"),
    ("shift", "Shifted"),
    ("shift2", "Shifted 2"),
    ("man2-out", "Outliers"),
]


def f(x: Any, d: int = 3) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return f"{x:.{d}f}"


def ci(p: dict[str, Any] | None, key: str = "geometric_mean") -> str:
    if not p:
        return "–"
    return f"{p[key]:.2f} [{p['lo']:.2f}, {p['hi']:.2f}]"


def rate(p: dict[str, Any] | None) -> str:
    if not p:
        return "–"
    return f"{p['rate']:.2f} ({p['n']})"


def tables(summary: dict[str, Any]) -> str:
    sp = summary["splits"]
    have = [(k, lab) for k, lab in SPLITS if k in sp]
    out = ["## Median period range error", ""]
    names = sorted(
        {n for k, _ in have for n in sp[k]["systems"] if "-h" not in n and "history" not in n}
    )
    out += ["| System | " + " | ".join(lab for _, lab in have) + " |"]
    out += ["| --- |" + " --- |" * len(have)]
    out += [
        "| Periods (scored) | "
        + " | ".join(f"{sp[k]['periods']} ({sp[k]['periods_scored']})" for k, _ in have)
        + " |"
    ]
    for n in names:
        row = []
        for k, _ in have:
            v = sp[k]["systems"].get(n, {}).get("median_period_range")
            row.append(f(None if v is None else min(v, 9.999)))
        out += [f"| `{n}` | " + " | ".join(row) + " |"]
    out += ["", "## Detectability of the whole true manoeuvres (χ² their omission adds)", ""]
    out += [
        "| Split | Manoeuvres | 10% | 25% | Median | 75% | 90% | Under 10 | Under 20 | Under 40 |"
    ]
    out += ["| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, lab in have:
        d = sp[k]["detectability"]
        if not d.get("manoeuvres"):
            continue
        q = d["quantiles_10_25_50_75_90"]
        sb = d["share_below"]
        out += [
            f"| {lab} | {d['manoeuvres']} | "
            + " | ".join(f(x, 1) for x in q)
            + " | "
            + " | ".join(ci(sb[t], "rate") for t in sorted(sb, key=float))
            + " |"
        ]
    out += [
        "",
        "## Share of true manoeuvres missed, by detectability band (matched within 120 s)",
        "",
    ]
    for k, lab in have:
        bands = sp[k]["detectability"].get("missed_by_band")
        if not bands:
            continue
        systems = [s for s in next(iter(bands.values())) if s != "n"]
        out += [
            f"### {lab}",
            "",
            "| Detectability | Manoeuvres | " + " | ".join(f"`{s}`" for s in systems) + " |",
        ]
        out += ["| --- | --- |" + " --- |" * len(systems)]
        for band, row in bands.items():
            out += [f"| {band} | {row['n']} | " + " | ".join(rate(row[s]) for s in systems) + " |"]
        out += [""]
    out += ["## The gap to the true history, split: the attainable share at each threshold", ""]
    out += [
        "(the share of log(system ÷ full reference) that a reference told only the manoeuvres above the threshold still closes; the rest is identifiability)",
        "",
    ]
    out += [
        "| Split | System | Threshold 10 | Threshold 20 | Threshold 40 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for k, lab in have:
        for s, g in sp[k]["gap_split"].items():
            out += [
                f"| {lab} | `{s}` | "
                + " | ".join(ci(g.get(t), "share") for t in ("10", "20", "40"))
                + " |"
            ]
        for s, g in sp[k].get("gap_split_edited", {}).items():
            out += [
                f"| {lab}, edited bearings | `{s}` | "
                + " | ".join(ci(g.get(t), "share") for t in ("10", "20", "40"))
                + " |"
            ]
    out += ["", "| Split | Verdict by the rule (control, threshold 20) |", "| --- | --- |"]
    out += [f"| {lab} | {sp[k]['verdict']} |" for k, lab in have]
    out += ["", "## Paired comparisons (a ÷ b per period; above 1: b is better)", ""]
    for k, lab in have:
        c = sp[k]["comparisons"]
        keys = [x for x in sorted(c) if "-h1" not in x and "history" not in x]
        out += [
            f"### {lab}",
            "",
            "| a | b | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |",
        ]
        out += ["| --- | --- | --- | --- | --- | --- |"]
        for key in keys:
            a, b = key.split("_over_")
            v = c[key]
            out += [
                f"| `{a}` | `{b}` | {ci(v)} | {v['median_ratio']:.2f} | "
                f"{v['a_twice_as_bad']:.2f} | {v['b_twice_as_bad']:.2f} |"
            ]
        out += [""]
    out += [
        "## Manoeuvres missed (share) and false (per period), matched within 60, 120 and 240 s",
        "",
    ]
    out += [
        "| Split | System | Missed 60 / 120 / 240 | False 60 / 120 / 240 |",
        "| --- | --- | --- | --- |",
    ]
    for k, lab in have:
        for n, v in sorted(sp[k]["counts"].items()):
            if "-h" in n:
                continue
            out += [
                f"| {lab} | `{n}` | "
                + " / ".join(f(v[t]["missed_share"], 2) for t in ("60", "120", "240"))
                + " | "
                + " / ".join(f(v[t]["false_per_period"], 2) for t in ("60", "120", "240"))
                + " |"
            ]
    out += ["", "## References held, and efficiency against the bound (range, course, speed)", ""]
    out += [
        "| Split | References drifting when free | System | Range | Course | Speed |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for k, lab in have:
        for n in ("ctl-d1-q0.01", "search3", "true", "ref-full", "ref-d20", "imm", "ekf", "c2"):
            v = sp[k]["systems"].get(n)
            if v:
                out += [
                    f"| {lab} | {sp[k]['reference_flagged_share']:.2f} | `{n}` | "
                    f"{f(v['efficiency_range'], 2)} | {f(v['efficiency_course'], 2)} | {f(v['efficiency_speed'], 2)} |"
                ]
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
