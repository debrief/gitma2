"""Spec 018: every table of a record, generated from its ``summary.json`` (FR-015).

    uv run python scripts/research/tl6_tables.py <experiment dir> [--out tables.md]

Prints Markdown: each system's median period range error; the paired comparisons the plan
names in range, course and speed, each with its period count, median per-period ratio and
the shares over twice as bad; the adaptive control's share of the true-prior search's gain;
the main comparisons by kind of period; manoeuvres missed and false at three tolerances,
periods with any false manoeuvre, one-manoeuvre targets called quiet, quiet targets given a
manoeuvre; the inferred rate; the coverage of the hedged track's stated spread.
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
    ("quiet", "Held course"),
    ("man2-out", "Outliers"),
    ("man2-corr", "Correlated"),
]
KINDS = [
    ("control_misses", "control misses a detectable manoeuvre"),
    ("control_finds_all", "control misses none"),
    ("bound_tight", "bound: tight third"),
    ("bound_middle", "bound: middle third"),
    ("bound_loose", "bound: loose third"),
]
QUANT = ("range", "course", "speed")


def f(x: Any, d: int = 3) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return f"{x:.{d}f}"


def ci(p: dict[str, Any] | None, key: str = "geometric_mean") -> str:
    if not p or p.get(key) is None or not math.isfinite(p[key]):
        return "–"
    return f"{p[key]:.2f} [{p['lo']:.2f}, {p['hi']:.2f}]"


def rate(p: dict[str, Any] | None) -> str:
    return f"{p['rate']:.2f} ({p['n']})" if p else "–"


def tables(summary: dict[str, Any]) -> str:
    sp = summary["splits"]
    have = [(k, lab) for k, lab in SPLITS if k in sp]
    out = ["## Median period range error", ""]
    names = sorted(
        {n for k, _ in have for n in sp[k]["systems"] if "history" not in n and n != "ctl"}
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
    out += ["", "## Paired comparisons (a ÷ b per period; above 1: b is better)", ""]
    for k, lab in have:
        comp = sp[k]["comparisons3"]
        out += [
            f"### {lab}",
            "",
            "| a | b | Quantity | Periods | Ratio | Median per-period ratio | a over twice as bad | b over twice as bad |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for key in sorted(comp):
            a, b = key.split("_over_")
            for q in QUANT:
                v = comp[key].get(q)
                if v:
                    out += [
                        f"| `{a}` | `{b}` | {q} | {v['periods']} | {ci(v)} | {v['median_ratio']:.2f} | "
                        f"{v['a_twice_as_bad']:.2f} | {v['b_twice_as_bad']:.2f} |"
                    ]
        out += [""]
    out += ["## The adaptive control's share of the true-prior search's gain over the control", ""]
    out += ["| Split | Range | Course | Speed |", "| --- | --- | --- | --- |"]
    for k, lab in have:
        s = sp[k]["share_of_ceiling"]
        if s:
            out += [f"| {lab} | " + " | ".join(ci(s.get(q), "share") for q in QUANT) + " |"]
    out += ["", "## By kind of period (range; a ÷ b)", ""]
    for k, lab in have:
        bk = sp[k]["by_kind"]
        if not any(bk.values()):
            continue
        out += [f"### {lab}", "", "| a | b | Kind of period | Periods | Ratio | Median |"]
        out += ["| --- | --- | --- | --- | --- | --- |"]
        for key in sorted(bk):
            a, b = key.split("_over_")
            for kind, klab in KINDS:
                v = (bk[key].get(kind) or {}).get("range")
                if v:
                    out += [
                        f"| `{a}` | `{b}` | {klab} | {v['periods']} | {ci(v)} | {v['median_ratio']:.2f} |"
                    ]
        out += [""]
    out += [
        "## Manoeuvres missed (share) and false (per period), matched within 60, 120 and 240 s",
        "",
    ]
    out += [
        "| Split | System | Missed 60 / 120 / 240 | False 60 / 120 / 240 | Periods with a false one 60 / 120 / 240 | One-manoeuvre targets called quiet | Quiet targets given a manoeuvre |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for k, lab in have:
        for n, v in sorted(sp[k]["counts"].items()):
            if "-h" in n or n == "ctl" or n == "ada":
                continue
            af = sp[k]["any_false"].get(n) or {}
            dq = (sp[k]["declares"].get(n) or {}).get("0") or {}
            cq = dq.get("called_quiet")
            given = f"{1 - cq['rate']:.2f} ({cq['n']})" if cq else "–"
            out += [
                f"| {lab} | `{n}` | "
                + " / ".join(f(v[t]["missed_share"], 2) for t in ("60", "120", "240"))
                + " | "
                + " / ".join(f(v[t]["false_per_period"], 2) for t in ("60", "120", "240"))
                + " | "
                + " / ".join(f((af.get(t) or {}).get("rate"), 2) for t in ("60", "120", "240"))
                + f" | {rate(sp[k]['one_called_quiet'].get(n))} | {given} |"
            ]
    out += ["", "## The inferred rate", ""]
    out += [
        "| Split | Periods | Inferred leg length, median (quartiles), s | Share of periods picking each rate |",
        "| --- | --- | --- | --- |",
    ]
    for k, lab in have:
        r = sp[k]["rate"]
        if not r["periods"]:
            continue
        q = r["leg_inferred_quartiles_s"]
        picked = ", ".join(f"{name[4:]} s: {share:.2f}" for name, share in r["picked"].items())
        out += [
            f"| {lab} | {r['periods']} | {r['leg_inferred_median_s']:.0f} ({q[0]:.0f}, {q[1]:.0f}) | {picked} |"
        ]
    out += ["", "## The hedged track's stated spread in range: coverage", ""]
    out += [
        "(share of rows whose true range is within one and two stated sds of the mixture's mean range; a normal spread gives 0.68 and 0.95)",
        "",
        "| Split | True manoeuvres | Periods | Rows | Within 1 sd | Within 2 sd | Median stated sd ÷ range |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for k, lab in have:
        c = sp[k]["coverage"]
        for g in ("all", "0", "1", "2+"):
            v = c.get(g)
            if v and v["rows"]:
                out += [
                    f"| {lab} | {g} | {v['periods']} | {v['rows']} | {f(v.get('within_1sd'), 2)} | "
                    f"{f(v.get('within_2sd'), 2)} | {f(v['median_relative_sd'])} |"
                ]
    out += ["", "## Per-period choice: share of periods in which the declared history is given", ""]
    out += [
        "| Split | " + " | ".join(lab for _, lab in have) + " |",
        "| --- |" + " --- |" * len(have),
    ]
    keys = sorted({t for k, _ in have for t in sp[k]["auto_declares_share"]}, key=float)
    for t in keys:
        out += [
            f"| first candidate at least {t} | "
            + " | ".join(f(sp[k]["auto_declares_share"].get(t), 2) for k, _ in have)
            + " |"
        ]
    out += ["", "## Efficiency against the bound (range, course, speed) and references held", ""]
    out += ["| Split | References drifting when free | System | Range | Course | Speed |"]
    out += ["| --- | --- | --- | --- | --- | --- |"]
    for k, lab in have:
        for n in ("ctl-d1-q0.01", "ada-d1-q0.01", "ada-h1", "true", "ref-full", "c2"):
            v = sp[k]["systems"].get(n)
            if v:
                out += [
                    f"| {lab} | {sp[k]['reference_flagged_share']:.2f} | `{n}` | "
                    f"{f(v['efficiency_range'], 2)} | {f(v['efficiency_course'], 2)} | {f(v['efficiency_speed'], 2)} |"
                ]
    out += [
        "",
        "## Seconds per period",
        "",
        "| Split | " + " | ".join(lab for _, lab in have) + " |",
    ]
    out += ["| --- |" + " --- |" * len(have)]
    for key in sorted({s for k, _ in have for s in sp[k]["seconds_per_period"]}):
        out += [
            f"| {key} | "
            + " | ".join(f(sp[k]["seconds_per_period"].get(key), 1) for k, _ in have)
            + " |"
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
