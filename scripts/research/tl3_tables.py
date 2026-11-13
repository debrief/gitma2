"""Spec 015: every table of a record, generated from its ``summary.json`` (FR-014: no table is
copied by hand).

    uv run python scripts/research/tl3_tables.py <experiment dir> [--out tables.md]

Prints Markdown: the systems table by split, the paired comparisons, the decided quantities
D1 to D4 with their sensitivities, false manoeuvres by period length, manoeuvring targets
declared quiet, counts and candidates. A test checks that a record's ``tables.md`` equals
what this script prints for its summary.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SYSTEMS = [
    ("One leg", "one-leg"),
    ("C″ read as a track", "c2"),
    ("C″ refitted", "c2-refit"),
    ("Search, flat prior", "search3-flat"),
    ("Search, spec 014's evidence", "search2"),
    ("Search, repaired evidence", "search3"),
    ("Search, repaired, mixed prior", "search3-mix"),
    ("True history, best evidence", "history-best"),
    ("True history, times held", "history-fixed"),
]
SPLITS = [
    ("man2", "Annex B"),
    ("shift", "Shifted"),
    ("quiet", "Held course"),
    ("man2-corr", "Correlated"),
    ("man2-out", "Outliers"),
    ("whole", "Whole"),
]
STATING = [
    n
    for _, n in SYSTEMS
    if n in ("c2", "c2-refit", "search3-flat", "search2", "search3", "search3-mix")
]


def num(x: Any, d: int = 3) -> str:
    return "–" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{d}f}"


def ci(v: dict[str, Any], key: str, d: int = 2) -> str:
    return f"{num(v[key], d)} [{num(v['lo'], d)}, {num(v['hi'], d)}]"


def tables(summary: dict[str, Any]) -> str:
    sp = summary["splits"]
    have = [(k, lab) for k, lab in SPLITS if k in sp]
    out: list[str] = []
    out += ["## Systems (median period range error)", ""]
    out.append(
        "| System | " + " | ".join(f"{lab} ({sp[k]['periods_scored']})" for k, lab in have) + " |"
    )
    out.append("| --- |" + " --- |" * len(have))
    for lab, key in SYSTEMS:
        cells = [
            num(sp[k]["systems"][key]["median_period_range"]) if key in sp[k]["systems"] else "–"
            for k, _ in have
        ]
        out.append(f"| {lab} | " + " | ".join(cells) + " |")
    for k, lab in have:
        r = sp[k]
        out += ["", f"## {lab}: paired comparisons", ""]
        out.append(
            "| Comparison | Paired | Of medians | First better | Over twice as bad: first / second |"
        )
        out.append("| --- | --- | --- | --- | --- |")
        for name, v in r["comparisons"].items():
            p, m = v["paired"], v["of_medians"]
            out.append(
                f"| {name.replace('_over_', ' ÷ ')} | {ci(p, 'geometric_mean')} | {ci(m, 'value')} | "
                f"{num(p['a_better'], 2)} | {num(p['a_twice_as_bad'], 2)} / {num(p['b_twice_as_bad'], 2)} |"
            )
        out += ["", f"## {lab}: classes of wrong-history periods", ""]
        out.append(
            "| Periods | Classed | First right | Wrong | Ambiguous | Search failure | Evidence failure |"
        )
        out.append("| --- | --- | --- | --- | --- | --- | --- |")
        for which in ("scored", "all", "scored_without_cut"):
            c = r["classes"][which]
            aw = c["among_wrong"]
            out.append(
                f"| {which.replace('_', ' ')} | {c['periods']} | {ci(c['right'], 'rate')} | {c['wrong']} | "
                f"{ci(aw['ambiguous'], 'rate')} | {ci(aw['search_failure'], 'rate')} | "
                f"{ci(aw['evidence_failure'], 'rate')} |"
            )
        if "headroom" in r:
            out += ["", f"## {lab}: attainable headroom (search ÷ composite, paired)", ""]
            out.append(
                "| Setting | Perfect search | Perfect evidence as well | Every wrong period | Where it helps only |"
            )
            out.append("| --- | --- | --- | --- | --- |")
            for key, h in r["headroom"].items():
                out.append(
                    f"| {key.replace('_', ' ')} | {ci(h['ident-search']['paired'], 'geometric_mean')} "
                    f"{h['ident-search'].get('verdict', '')} | {ci(h['ident-all']['paired'], 'geometric_mean')} "
                    f"{h['ident-all'].get('verdict', '')} | {ci(h['every-wrong']['paired'], 'geometric_mean')} | "
                    f"{ci(h['ident-all-hindsight']['paired'], 'geometric_mean')} |"
                )
            reg = r["headroom"]["registered"]
            out += [
                "",
                f"Ratio of medians at the registered setting: perfect search "
                f"{ci(reg['ident-search']['of_medians'], 'value')}; perfect evidence as well "
                f"{ci(reg['ident-all']['of_medians'], 'value')}.",
            ]
        if "gain_share" in r:
            g = r["gain_share"]
            out += ["", f"## {lab}: the refit's share of the search's gain", ""]
            out.append("| Estimand | Share |")
            out.append("| --- | --- |")
            for key in (
                "registered",
                "without_fallbacks",
                "medians_at_most_1",
                "search_right",
                "search_wrong",
                "flat_prior_search",
            ):
                if key in g:
                    out.append(
                        f"| {key.replace('_', ' ')} | {ci(g[key], 'share')} ({g[key]['periods']} periods) |"
                    )
            out.append(f"| ratio of log medians | {num(g['ratio_of_log_medians'], 2)} |")
            out += [
                "",
                f"Refit fall-backs: {r['refit_fell_back']} of {r['periods']}; refits with a period median of 1 or more: {r.get('refit_runaways', 0)}.",
            ]
        out += ["", f"## {lab}: manoeuvre counts (120 s match; cut manoeuvres excluded)", ""]
        out.append(
            "| System | True | Missed | Missed share | False | False a period | Timing (s) | Missed at 60 s / 240 s |"
        )
        out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for name in STATING:
            if name in r["counts"]:
                c = r["counts"][name]
                a = c["120"]
                out.append(
                    f"| {name} | {a['true']} | {a['missed']} | {num(a['missed_share'], 2)} | {a['false']} | "
                    f"{num(a['false_per_period'], 2)} | {num(a['timing_median_s'], 0)} | "
                    f"{num(c['60']['missed_share'], 2)} / {num(c['240']['missed_share'], 2)} |"
                )
        q = r["quiet"]
        if q["periods"]:
            out += [
                "",
                f"## {lab}: periods with no true manoeuvre ({q['periods']}): share with one declared",
                "",
            ]
            bins = [b for b in q["by_minutes"] if any(v["n"] for v in q["by_minutes"][b].values())]
            out.append("| System | All | " + " | ".join(f"{b} min" for b in bins) + " |")
            out.append("| --- | --- |" + " --- |" * len(bins))
            for name in STATING:
                if name in q["false_manoeuvre_rate"]:
                    cells = [
                        f"{num(q['by_minutes'][b][name]['rate'], 2)} ({q['by_minutes'][b][name]['n']})"
                        for b in bins
                    ]
                    out.append(
                        f"| {name} | {ci(q['false_manoeuvre_rate'][name], 'rate')} | "
                        + " | ".join(cells)
                        + " |"
                    )
        dq = r["declared_quiet"]
        if any(v["n"] for d in dq.values() for v in d.values()):
            out += [
                "",
                f"## {lab}: manoeuvring targets declared quiet, by true manoeuvres (periods with none cut)",
                "",
            ]
            out.append("| System | 1 | 2 | 3 or more |")
            out.append("| --- | --- | --- | --- |")
            for name in STATING:
                if name in dq:
                    out.append(
                        f"| {name} | "
                        + " | ".join(
                            f"{num(dq[name][k]['rate'], 3)} ({dq[name][k]['n']})"
                            for k in ("1", "2", "3+")
                        )
                        + " |"
                    )
        for key, what in (("candidates", "repaired"), ("candidates2", "spec 014's")):
            if key in r and r[key].get("periods"):
                c = r[key]
                top = next(k for k in c if k.startswith("truth_in_top"))
                out += [
                    "",
                    f"Candidates ({what} evidence, {c['periods']} periods): first right {num(c['top_right'], 3)}; "
                    f"true history in the first three {num(c[top], 3)}; calibration gap {num(c['calibration_gap'], 3)}; "
                    f"kinds differ among right {num(c['kinds_differ_among_right'], 2)}.",
                ]
        out += [
            "",
            f"References held to the true times: {num(r['reference_flagged_share'], 3)}; true-history fits "
            f"with a consistent cost: {num(r['history_converged_share'], 3)}; periods with a cut manoeuvre: "
            f"{r['periods_with_a_cut_manoeuvre']} of {r['periods']}.",
        ]
    if summary.get("soundness"):
        s = summary["soundness"]
        out += [
            "",
            "## Soundness",
            "",
            f"Reference efficiency on tight rows {num(s['reference_efficiency_tight'], 2)} (band "
            f"{s['band'][0]} to {s['band'][1]}); consistent fits {num(s['history_converged_share'], 3)} "
            f"(at least {s['convergence_min']}); references held {num(s['reference_flagged_share'], 3)} "
            f"(at most {s['reference_flagged_max']}): {'pass' if s['pass'] else 'fail'}.",
        ]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("experiment")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    text = tables(json.loads((Path(a.experiment) / "summary.json").read_text()))
    if a.out:
        Path(a.out).write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
