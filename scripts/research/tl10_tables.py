"""Tables for spec 028's records: spec 025/027's tables (``tl8_tables.py``) and then the carried
prior's readings and the coverage of its stated uncertainty, all generated from the record's
``summary.json`` and ``<split>.periods.json`` (never hand-copied).

    uv run python scripts/research/tl10_tables.py experiments/<record>

Writes ``<record>/tables.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tl8_tables  # noqa: E402

CHI2_4_95, CHI2_4_99, CHI2_2_95 = 9.488, 13.277, 5.991
CMP = ("cprior/joint", "alone/cprior", "carry/cprior", "carry/joint")


def _r(d: dict[str, Any]) -> str:
    return f"{d['value']:.3f} [{d['lo']:.3f}, {d['hi']:.3f}] (median {d['median']:.2f})"


def _coverage(rec: Path, split: str) -> dict[str, float]:
    periods = json.loads((rec / f"{split}.periods.json").read_text())
    md, mx, sd = [], [], []
    for e in periods:
        for q in e.get("cprior", []):
            if "truth_md2" in q:
                md.append(q["truth_md2"])
                mx.append(q["truth_md2_xy"])
                sd.append(q["prior_sd"])
    a, b, s = np.array(md), np.array(mx), np.array(sd)
    return {
        "n": float(a.size),
        "in95": float(np.mean(a < CHI2_4_95)),
        "in99": float(np.mean(a < CHI2_4_99)),
        "med": float(np.median(a)),
        "xy95": float(np.mean(b < CHI2_2_95)),
        "xymed": float(np.median(b)),
        "sd_x": float(np.median(s[:, 0])),
        "sd_y": float(np.median(s[:, 1])),
        "sd_c": float(np.degrees(np.median(s[:, 2]))),
        "sd_v": float(np.median(s[:, 3])),
    }


def section(rec: Path) -> str:
    sp = json.loads((rec / "summary.json").read_text())["splits"]
    out = ["", "## Carried prior (spec 028), periods after an engagement's first", ""]
    out += ["| split | quantity | " + " | ".join(CMP) + " |", "|---|---|" + "---|" * len(CMP)]
    for s_, r in sp.items():
        for q in ("range", "course", "speed"):
            out.append(
                f"| {s_} | {q} | " + " | ".join(_r(r["cprior"]["ratios"][c][q]) for c in CMP) + " |"
            )
    out += ["", "Range, on rows the period determines alone (own rows):", ""]
    out += ["| split | periods | " + " | ".join(CMP) + " |", "|---|---|" + "---|" * len(CMP)]
    for s_, r in sp.items():
        c = r["cprior"]
        d = c["ratios_own_rows"]
        out.append(
            f"| {s_} | {c['periods_scored_own']} | "
            + " | ".join(_r(d[k]["range"]) for k in CMP)
            + " |"
        )
    out += ["", "Range, by whether the period has an ownship turn of its own:", ""]
    out += [
        "| split | kind | periods | " + " | ".join(CMP[:3]) + " |",
        "|---|---|---|" + "---|" * 3,
    ]
    for s_, r in sp.items():
        for k, b in r["cprior"]["by_kind"].items():
            out.append(
                f"| {s_} | {k} | {b['periods']} | "
                + " | ".join(_r(b[c]["range"]) for c in CMP[:3])
                + " |"
            )
    out += ["", "Shares of periods (range; within 1% counts as a tie):", ""]
    out += [
        "| split | alone vs cprior: tie / cprior better / worse | cprior vs joint: tie / joint better / worse |",
        "|---|---|---|",
    ]
    for s_, r in sp.items():
        a, j = r["cprior"]["ties_alone"], r["cprior"]["ties_joint"]
        out.append(
            f"| {s_} | {a['within_1pct']:.2f} / {a['better']:.2f} / {a['worse']:.2f} "
            f"| {j['within_1pct']:.2f} / {j['better']:.2f} / {j['worse']:.2f} |"
        )
    out += [
        "",
        "Coverage of the carried uncertainty (FR-004): the truth's squared Mahalanobis distance from",
        "the carried prior at the period's first row, against χ² with 4 degrees of freedom (all four",
        "starting parameters; 95% below 9.49, median 3.36) and 2 (position only; 95% below 5.99, median 1.39).",
        "",
        "| split | carried periods | inside 95% (4 dof) | inside 99% | median | position inside 95% | position median | prior sd x, y (m) | course (deg) | speed (m/s) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s_ in sp:
        c = _coverage(rec, s_)
        out.append(
            f"| {s_} | {c['n']:.0f} | {c['in95']:.3f} | {c['in99']:.3f} | {c['med']:.2f} | {c['xy95']:.3f} "
            f"| {c['xymed']:.2f} | {c['sd_x']:.0f}, {c['sd_y']:.0f} | {c['sd_c']:.1f} | {c['sd_v']:.2f} |"
        )
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    rec = Path(args[0])
    tl8_tables.main([str(rec)])
    p = rec / "tables.md"
    p.write_text(p.read_text() + section(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
