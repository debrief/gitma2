"""Spec 016: the learned model's tables of a record that scored it, generated from its
``summary.json`` (FR-021), beside ``tl4_tables.py`` (which is bound by the decision record
and unchanged).

    uv run python scripts/research/tl4_learned_tables.py <experiment dir> [--out learned.md]

Prints Markdown: the registered verdicts L-c and L-d seed by seed; every system over every
learned track, paired per period; efficiency against the bound by split.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tl4_tables import SPLITS, ci, f


def learned(summary: dict[str, Any], have: list[tuple[str, str]]) -> list[str]:
    """The learned model's sections (only for a record that scored it)."""
    sp, crit = summary["splits"], summary["criteria"]
    lab = dict(have)
    out = ["", "## L-c and L-d: the registered verdicts", ""]
    out += [
        "| Split | Verdict | Seed | Declared control ÷ learned | Side | Hedged track ÷ learned | Side |"
    ]
    out += ["| --- | --- | --- | --- | --- | --- | --- |"]
    for block in ("splits", "no_harm"):
        for k, v in crit[block].items():
            for seed, r in v["seeds"].items():
                out += [
                    f"| {lab.get(k, k)} | {v['verdict']} | `{seed}` | {ci(r['declared'])} | "
                    f"{r['vs_declared']} | {ci(r['hedged'])} | {r['vs_hedged']} |"
                ]
    out += [
        "",
        f"Learning shown on {crit['learning_shown_on']} mismatch split(s); harm: "
        f"{'yes' if crit['harm'] else 'no'}. What follows: {crit['follows']}.",
        "",
    ]
    out += [
        "## Each system ÷ each learned track (paired per period; above 1: the learned track is better)",
        "",
    ]
    for k, lb in have:
        c = sp[k]["comparisons"]
        keys = sorted(x for x in c if "_over_learned" in x)
        if not keys:
            continue
        out += [
            f"### {lb}",
            "",
            "| System | Learned track | Ratio | Share of periods where the system is better | Learned over twice as bad in |",
        ]
        out += ["| --- | --- | --- | --- | --- |"]
        for key in keys:
            a, b = key.split("_over_")
            v = c[key]
            out += [
                f"| `{a}` | `{b}` | {ci(v)} | {v['a_better']:.2f} | {v['b_twice_as_bad']:.2f} |"
            ]
        out += [""]
    out += ["## Efficiency against the bound (range, course, speed) and rows without a state", ""]
    out += ["| Split | System | Range | Course | Speed | Periods without a track |"]
    out += ["| --- | --- | --- | --- | --- | --- |"]
    for k, lb in have:
        for n, v in sorted(sp[k]["systems"].items()):
            if not (n.startswith("learned") or n in ("ctl-d1-q0.01", "ctl-h1", "search3", "c2")):
                continue
            out += [
                f"| {lb} | `{n}` | {f(v['efficiency_range'], 2)} | {f(v['efficiency_course'], 2)} | "
                f"{f(v['efficiency_speed'], 2)} | {v.get('periods_without_a_track', 0)} |"
            ]
    return out


def tables(summary: dict[str, Any]) -> str:
    have = [(k, lab) for k, lab in SPLITS if k in summary["splits"]]
    return "\n".join(learned(summary, have)).lstrip("\n") + "\n"


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
