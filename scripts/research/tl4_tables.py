"""Spec 016: every table of a record, generated from its ``summary.json`` (FR-021).

    uv run python scripts/research/tl4_tables.py <experiment dir> [--out tables.md]

Prints Markdown: per split, the systems' median period range error; the standing search
over each control, paired per period; the share of the gap to the reference each control
closes; systems over the true-history reference under each convention; manoeuvre counts;
the declaration grid (held-course false manoeuvres against manoeuvring targets called
quiet); what the correlation estimate and the prior diagnostic said. A test checks that a
record's ``tables.md`` equals what this prints for its summary.
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
    ("man2-corr-mild", "Correlated, mild"),
    ("man2-corr", "Correlated"),
    ("man2-out", "Outliers"),
    ("man2-out-harsh", "Outliers, harsh"),
    ("man2-bias", "Bias"),
    ("whole", "Whole"),
]
REFS = [
    ("history-map", "times free"),
    ("history-best", "held where drifted"),
    ("history-held", "times held"),
]


def f(x: Any, d: int = 3) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "–"
    return f"{x:.{d}f}"


def ci(p: dict[str, Any] | None, key: str = "geometric_mean") -> str:
    if not p:
        return "–"
    return f"{p[key]:.2f} [{p['lo']:.2f}, {p['hi']:.2f}]"


def plain(name: str) -> bool:
    return "-h" not in name and "-d" not in name


def tables(summary: dict[str, Any]) -> str:
    sp = summary["splits"]
    have = [(k, lab) for k, lab in SPLITS if k in sp]
    out: list[str] = []
    names = sorted({n for k, _ in have for n in sp[k]["systems"] if plain(n)})
    out += ["## Median period range error", ""]
    out += ["| System | " + " | ".join(lab for _, lab in have) + " |"]
    out += ["| --- |" + " --- |" * len(have)]
    out += [
        "| Periods (scored) | "
        + " | ".join(f"{sp[k]['periods']} ({sp[k]['periods_scored']})" for k, _ in have)
        + " |"
    ]
    for n in names:
        row = [
            f(sp[k]["systems"].get(n, {}).get("median_period_range")) if n != "one-leg" else "…"
            for k, _ in have
        ]
        if n == "one-leg":
            row = [f(min(sp[k]["systems"][n]["median_period_range"], 9.999)) for k, _ in have]
        out += [f"| `{n}` | " + " | ".join(row) + " |"]
    out += ["", "## The standing search ÷ each system (paired per period; above 1: better)", ""]
    for k, lab in have:
        c = sp[k]["comparisons"]
        out += [
            f"### {lab}",
            "",
            "| System | Ratio | Share of periods where the search is better |",
        ]
        out += ["| --- | --- | --- |"]
        for key in sorted(c):
            if not key.startswith("search3_over_") or "history" in key:
                continue
            n = key[len("search3_over_") :]
            if "-d" in n:
                continue
            out += [f"| `{n}` | {ci(c[key])} | {c[key]['a_better']:.2f} |"]
        out += [""]
    out += ["## Share of the gap from the search to the reference that a control closes", ""]
    out += ["| Split | Control | Share |", "| --- | --- | --- |"]
    for k, lab in have:
        for n, v in sorted(sp[k]["gap_closed"].items()):
            if plain(n):
                out += [f"| {lab} | `{n}` | {ci(v, 'share')} |"]
    out += ["", "## System ÷ the true-history reference, by how the reference is fitted", ""]
    out += ["| Split | System | " + " | ".join(lab for _, lab in REFS) + " |"]
    out += ["| --- | --- |" + " --- |" * len(REFS)]
    for k, lab in have:
        for s in ("search3", "ctl"):
            row = [ci(sp[k]["comparisons"].get(f"{s}_over_{r}")) for r, _ in REFS]
            out += [f"| {lab} | `{s}` | " + " | ".join(row) + " |"]
    out += ["", "## Manoeuvres missed (share) and false (per period), matched within 120 s", ""]
    out += ["| Split | System | Missed | False |", "| --- | --- | --- | --- |"]
    for k, lab in have:
        for n, v in sorted(sp[k]["counts"].items()):
            if plain(n):
                c = v["120"]
                out += [
                    f"| {lab} | `{n}` | {f(c['missed_share'], 2)} | {f(c['false_per_period'], 2)} |"
                ]
    if "quiet" in sp and "man2" in sp:
        out += [
            "",
            "## Declaration: held-course periods given a manoeuvre, and Annex B targets called quiet",
            "",
        ]
        out += [
            "| System | Held course: false | One manoeuvre: called quiet | Two or more: called quiet | Annex B median | Held-course median |"
        ]
        out += ["| --- | --- | --- | --- | --- | --- |"]
        qd, md = sp["quiet"]["declares"], sp["man2"]["declares"]
        for n in sorted(qd):
            if n not in md or "-h" in n:
                continue
            q0 = qd[n]["0"]["called_quiet"]
            false = None if q0 is None else 1.0 - q0["rate"]
            one, two = md[n]["1"]["called_quiet"], md[n]["2+"]["called_quiet"]
            out += [
                f"| `{n}` | {f(false, 2)} | {f(one and one['rate'], 2)} | {f(two and two['rate'], 2)} | "
                f"{f(sp['man2']['systems'].get(n, {}).get('median_period_range'))} | "
                f"{f(sp['quiet']['systems'].get(n, {}).get('median_period_range'))} |"
            ]
    out += ["", "## What the estimates said", ""]
    out += [
        "| Split | References held | Wild bearings edited a period | Correlated share (median) | Correlation used by `ctl` | Bayes factor for the broad prior (median log) | Share above 0 |"
    ]
    out += ["| --- | --- | --- | --- | --- | --- | --- |"]
    for k, lab in have:
        r = sp[k]
        out += [
            f"| {lab} | {f(r['reference_flagged_share'], 2)} | {f(r['edited_per_period'], 1)} | "
            f"{f(r['corr_estimate']['share_median'], 2)} | {f(r['corr_estimate']['ctl_used_share'], 2)} | "
            f"{f(r['log_bayes_broad']['median'], 1)} | {f(r['log_bayes_broad']['share_above_0'], 2)} |"
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
