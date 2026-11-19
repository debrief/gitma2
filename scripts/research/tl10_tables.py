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
    extra = variants_section(rec) if _has_variants(rec) else ""
    p.write_text(p.read_text() + section(rec) + extra)
    return 0


def _has_variants(rec: Path) -> bool:
    sp = json.loads((rec / "summary.json").read_text())["splits"]
    return any("variants" in r.get("cprior", {}) for r in sp.values())


def _variant_coverage(rec: Path, split: str, name: str) -> dict[str, float]:
    periods = json.loads((rec / f"{split}.periods.json").read_text())
    md, ch = [], []
    for e in periods:
        for q in (e.get("cv") or {}).get(name, []):
            if "truth_md2" in q:
                md.append(q["truth_md2"])
            if "chose_carried" in q:
                ch.append(q["chose_carried"])
    a = np.array(md)
    return {
        "n": float(a.size),
        "in95": float(np.mean(a < CHI2_4_95)) if a.size else float("nan"),
        "med": float(np.median(a)) if a.size else float("nan"),
        "carried": float(np.mean(ch)) if ch else float("nan"),
    }


def variant_rows(rec: Path) -> list[dict[str, Any]]:
    """One row per (split, variant): the readings the choice rule uses."""
    sp = json.loads((rec / "summary.json").read_text())["splits"]
    rows = []
    for s_, r in sp.items():
        c = r["cprior"]
        named = {"cprior": None, **{k: k for k in c.get("variants", {})}}
        for name in named:
            if name == "cprior":
                rat = c["ratios"]["alone/cprior"]["range"]
                vj = c["ratios"]["cprior/joint"]["range"]
                own = c["by_kind"]["own_turn"]["alone/cprior"]["range"]
                noown = c["by_kind"]["no_own_turn"]["alone/cprior"]["range"]
                cov = _coverage(rec, s_)
                cov = {"in95": cov["in95"], "med": cov["med"], "carried": 1.0}
            else:
                v = c["variants"][name]
                key = f"cv-{name}"
                rat = v["ratios"][f"alone/{key}"]["range"]
                vj = v["ratios"][f"{key}/joint"]["range"]
                own = v["by_kind"]["own_turn"][f"alone/{key}"]["range"]
                noown = v["by_kind"]["no_own_turn"][f"alone/{key}"]["range"]
                cov = _variant_coverage(rec, s_, name)
            rows.append(
                {
                    "split": s_,
                    "variant": name,
                    "alone_v": rat,
                    "v_joint": vj,
                    "own": own,
                    "no_own": noown,
                    **{k: cov[k] for k in ("in95", "med", "carried")},
                }
            )
    return rows


def variants_section(rec: Path) -> str:
    rows = variant_rows(rec)
    out = [
        "",
        "## Refinements (range; periods after an engagement's first)",
        "",
        "| split | variant | alone ÷ v | v ÷ joint | alone ÷ v, own turn | alone ÷ v, no own turn | inside 95% (4 dof) | median d² | carried part chosen |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for x in rows:
        out.append(
            f"| {x['split']} | {x['variant']} | {_r(x['alone_v'])} | {_r(x['v_joint'])} | {_r(x['own'])} "
            f"| {_r(x['no_own'])} | {x['in95']:.3f} | {x['med']:.2f} | {x['carried']:.2f} |"
        )
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
