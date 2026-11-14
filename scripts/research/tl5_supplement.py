"""Spec 017: readings the README quotes that ``tables.md`` does not carry directly.

    uv run python scripts/research/tl5_supplement.py <record dir> [--out supplement.md]

From ``summary.json`` alone: each system's miss rate pooled over the detectability bands
under 20 and above 40 (the second half of the recommendation's logic reads the control's
rate above 40 on the shifted split), and the recommendation's two conditions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SPLITS = [
    ("man2", "Annex B"),
    ("shift", "Shifted"),
    ("shift2", "Shifted 2"),
    ("man2-out", "Outliers"),
]
CONTROL = "ctl-d1-q0.01"


def pooled(bands: dict[str, Any], system: str, names: tuple[str, ...]) -> tuple[float, int]:
    n = sum(bands[b]["n"] for b in names)
    missed = sum(bands[b][system]["rate"] * bands[b]["n"] for b in names)
    return (missed / n if n else float("nan")), n


def text(summary: dict[str, Any]) -> str:
    sp = summary["splits"]
    out = [
        "## Manoeuvres missed, pooled over detectability bands (matched within 120 s)",
        "",
        "| Split | System | Under 20 (manoeuvres) | Above 40 (manoeuvres) |",
        "| --- | --- | --- | --- |",
    ]
    for k, lab in SPLITS:
        if k not in sp:
            continue
        bands = sp[k]["detectability"]["missed_by_band"]
        for s in (CONTROL, "search3", "true", "c2"):
            lo, nlo = pooled(bands, s, ("0-5", "5-10", "10-20"))
            hi, nhi = pooled(bands, s, ("40-100", "100+"))
            out += [f"| {lab} | `{s}` | {lo:.2f} ({nlo}) | {hi:.2f} ({nhi}) |"]
    c = sp["shift"]["comparisons"][f"{CONTROL}_over_ref-d20"]
    above, n = pooled(sp["shift"]["detectability"]["missed_by_band"], CONTROL, ("40-100", "100+"))
    first, second = c["lo"] > 1.10, above > 1 / 3
    out += [
        "",
        "## The recommendation's logic (decision record), shifted split",
        "",
        f"- E4 at threshold 20, control ÷ `ref-d20`: {c['geometric_mean']:.2f} "
        f"[{c['lo']:.2f}, {c['hi']:.2f}]; lower limit above 1.10: **{'yes' if first else 'no'}**.",
        f"- The control misses {above:.2f} of the {n} manoeuvres above 40; more than a third: "
        f"**{'yes' if second else 'no'}**.",
        f"- Both needed for a proposer study to be recommended: "
        f"**{'recommended' if first and second else 'not recommended'}**.",
    ]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    t = text(json.loads((Path(a.dir) / "summary.json").read_text()))
    if a.out:
        Path(a.out).write_text(t)
    else:
        print(t, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
