"""Spec 016: readings of a test record that its summary does not carry as tables, from
``summary.json`` and ``<split>.periods.json`` (FR-021: generated, not typed).

    uv run python scripts/research/tl4_supplement.py <experiment dir> [--out supplement.md]

* the model's own track against the two controls (the registered comparison is on the arc
  read-out; this is "reported beside");
* the read-out against the model's own track, and how often the read-out fell back;
* manoeuvres missed and false for the control and the model, and how often each calls a
  target quiet;
* the forecasts' quantities in one table.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tl4_tables import SPLITS, ci, f

SEEDS = ("learned-s1", "learned-s2", "learned-s3")


def text(d: Path) -> str:
    s = json.loads((d / "summary.json").read_text())["splits"]
    have = [(k, lab) for k, lab in SPLITS if k in s]
    out = ["## The model's own track (not the registered comparison)", ""]
    out += [
        "| Split | Seed | Declared control ÷ own track | Hedged track ÷ own track | Own track ÷ its arc read-out (from medians) | Read-out fell back |"
    ]
    out += ["| --- | --- | --- | --- | --- | --- |"]
    for k, lab in have:
        per = json.loads((d / f"{k}.periods.json").read_text())
        c, sy = s[k]["comparisons"], s[k]["systems"]
        for seed in SEEDS:
            arc = f"{seed}-arc"
            fell = sum(bool(r["histories"][arc].get("fell_back")) for r in per) / len(per)
            ratio = sy[seed]["median_period_range"] / sy[arc]["median_period_range"]
            out += [
                f"| {lab} | `{seed}` | {ci(c.get(f'ctl-d1-q0.01_over_{seed}'))} | "
                f"{ci(c.get(f'ctl-h1_over_{seed}'))} | {ratio:.2f} | {fell:.2f} |"
            ]
    out += ["", "## Manoeuvres (matched within 120 s) and targets called quiet", ""]
    out += [
        "| Split | System | Missed (share) | False (per period) | No true manoeuvre: given one | One true manoeuvre: called quiet |"
    ]
    out += ["| --- | --- | --- | --- | --- | --- |"]
    for k, lab in have:
        for n in ("c2", "search3", "ctl-d1-q0.01", "learned-s1", "learned-s1-arc"):
            cn = s[k]["counts"].get(n)
            dq = s[k]["declares"].get(n)
            if not cn or not dq:
                continue
            q0, q1 = dq["0"]["called_quiet"], dq["1"]["called_quiet"]
            out += [
                f"| {lab} | `{n}` | {f(cn['120']['missed_share'], 2)} | "
                f"{f(cn['120']['false_per_period'], 2)} | "
                f"{f(None if q0 is None else 1 - q0['rate'], 2)} ({dq['0']['n']}) | "
                f"{f(q1 and q1['rate'], 2)} ({dq['1']['n']}) |"
            ]
    out += ["", "## The controls (L-b)", ""]
    out += [
        "| Split | Search ÷ declared control | Gap to the reference closed by `ctl` | Declared ÷ hedged | `ctl` ÷ reference (held where drifted) | References held |"
    ]
    out += ["| --- | --- | --- | --- | --- | --- |"]
    for k, lab in have:
        c: dict[str, Any] = s[k]["comparisons"]
        out += [
            f"| {lab} | {ci(c.get('search3_over_ctl-d1-q0.01'))} | "
            f"{ci(s[k]['gap_closed'].get('ctl'), 'share')} | "
            f"{ci(c.get('ctl-d1-q0.01_over_ctl-h1'))} | {ci(c.get('ctl_over_history-best'))} | "
            f"{s[k]['reference_flagged_share']:.2f} |"
        ]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    t = text(Path(a.dir))
    if a.out:
        Path(a.out).write_text(t)
    else:
        print(t, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
