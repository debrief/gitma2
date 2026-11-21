"""Spec 034: the long-engagement track's figures of record in one place, from the registered test
records of specs 026, 028, 029, 031 and 032, and two charts.

    uv run python scripts/research/long_synthesis.py

Every number is read from a record's ``study.json``; nothing is typed by hand. Writes
``experiments/20261121-long-synthesis/tables.md`` and ``summary.json``, and the charts
``ratios.svg`` (every decided ratio with its engagement interval, on one log axis) and
``errors.svg`` (median range error of the standing systems and their comparators on the windows
each study decided) under ``site/static/img/2026-11-21-long-synthesis-slides/``, each with a
``.svg.json`` sidecar naming the inputs' digests and the commit.

Specs 023 and 024 were one engagement per length (anecdotes, not results); their figures are
in their own generated ``tables.md`` (``experiments/20261117-long/``, ``20261117-long2/``).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/20261121-long-synthesis"
FIG = ROOT / "site/static/img/2026-11-21-long-synthesis-slides"
REC = {
    "026": ROOT / "experiments/20261118-ls/study.json",
    "028": ROOT / "experiments/20261119-cp/study.json",
    "029": ROOT / "experiments/20261119-hold/study.json",
    "031": ROOT / "experiments/20261120-cmp/study.json",
    "032": ROOT / "experiments/20261120-legs/study.json",
}


def _load() -> dict[str, Any]:
    return {k: json.loads(p.read_text()) for k, p in REC.items()}


def _shares_counts(r: dict[str, Any]) -> dict[str, float | None]:
    n = r["better"] + r["worse"] + r["level"]
    return {
        "better": r["better"] / n,
        "twice_better": r["twice_better"] / n,
        "twice_worse": r["twice_worse"] / n,
    }


def rows(d: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per decided (or registered-beside) ratio, in the track's order."""
    out: list[dict[str, Any]] = []

    def add(
        spec: str,
        name: str,
        ratio: str,
        above: str,
        conv: str,
        gm: float,
        iv: list[float],
        median: float | None,
        shares: dict[str, float | None] | None,
        n: str,
        reading: str,
        decided: bool = True,
    ) -> None:
        out.append(
            {
                "spec": spec,
                "name": name,
                "ratio": ratio,
                "above_1": above,
                "convention": conv,
                "gm": gm,
                "interval": iv,
                "median": median,
                "shares": shares,
                "n": n,
                "reading": reading,
                "decided": decided,
            }
        )

    ls = d["026"]
    e1 = ls["E1"]
    add(
        "026",
        "E1",
        "ctl ÷ ctl-carry (2 h windows)",
        "carried start better",
        "tended contact, all windows after each chain's first; chain-first windows count as ties",
        e1["gm_ctl_over_carry"],
        e1["interval"],
        e1["median"],
        _shares_counts(e1),
        f"{e1['windows']} windows, {e1['engagements']} engagements",
        "non-inferior" if e1["non_inferior"] else "not non-inferior",
    )
    e1b = ls["E1_contact2_reported"]
    add(
        "026",
        "E1 contact 2",
        "ctl ÷ ctl-carry (2 h windows)",
        "carried start better",
        "untended contact; reported beside",
        e1b["gm_ctl_over_carry"],
        e1b["interval"],
        e1b["median"],
        _shares_counts(e1b),
        f"{e1b['windows']} windows, {e1b['engagements']} engagements",
        "reported",
        decided=False,
    )
    e2 = ls["E2"]
    add(
        "026",
        "E2",
        "untended ÷ tended contact (ctl)",
        "untended worse",
        "median range error by range band, rows each contact answers",
        e2["gm_c2_over_c1"],
        e2["interval"],
        None,
        None,
        f"{e2['engagements']} engagements",
        "untended worse",
    )
    e3 = ls["E3"]
    add(
        "026",
        "E3",
        "IMM hours 6–12 ÷ 0–6",
        "IMM drifts",
        "answered rows only; 12-hour engagements",
        e3["late_over_early"],
        e3["interval"],
        None,
        None,
        f"{e3['engagements']} engagements",
        "drift shown" if e3["drift_shown"] else "drift not shown",
    )

    cp = d["028"]
    for split, label in (("weak", "weak geometry (decided)"), ("other", "other windows")):
        r = cp["rule"]["by_split"][split]["range"]
        add(
            "028",
            label,
            "ctl ÷ ctl-prior (2 h windows)",
            "carried prior better",
            "ownship turning every 20–40 min; windows with no hand-over are ties",
            r["gm"],
            r["interval"],
            r["median"],
            _shares_counts(r),
            f"{r['windows']} windows, {r['engagements']} engagements",
            cp["rule"]["outcome"] if split == "weak" else "reported",
            decided=split == "weak",
        )
    for c, label in (("contact1", "tended contact"),):
        r = cp["beside"][c]["ctl/ctl-prior"]
        add(
            "028",
            label,
            "ctl ÷ ctl-prior (2 h windows)",
            "carried prior better",
            "contact 1, all windows; reported beside",
            r["gm"],
            r["interval"],
            r["median"],
            _shares_counts(r),
            f"{r['windows']} windows, {r['engagements']} engagements",
            "reported",
            decided=False,
        )

    hd = d["029"]
    for k, label in (("held", "blind 1 h windows (decided)"), ("one", "one-turn 1 h windows")):
        r = hd["rule"]["by_class"][k]["range"]
        add(
            "029",
            label,
            "ctl ÷ ctl-prior (1 h windows)",
            "carried prior better",
            "ownship legs 1–2 h; the same 1-hour window alone as comparator",
            r["gm"],
            r["interval"],
            r["median"],
            {
                "better": r["share_better"],
                "twice_better": r["share_twice_better"],
                "twice_worse": r["share_twice_worse"],
            },
            f"{r['windows']} windows, {r['engagements']} engagements",
            hd["rule"]["outcome"] if k == "held" else "no harm",
        )

    cm = d["031"]
    for key, label, ratio in (
        ("D1_2h_over_prior", "D1", "2 h ctl ÷ 1 h ctl-prior"),
        ("D2_joint_over_prior", "D2", "joint solve ÷ 1 h ctl-prior"),
        ("D3_prior2h_over_prior", "D3", "2 h ctl-prior ÷ 1 h ctl-prior"),
    ):
        r = cm["estimands"][key]["range"]
        add(
            "031",
            label,
            ratio,
            "1 h ctl-prior better",
            "blind 1 h windows, legs 1–2 h; D2 the same past bearings (the clean comparison)",
            r["gm"],
            r["interval"],
            r["median"],
            {
                "better": r["share_a_better"],
                "twice_better": r["share_twice_a_better"],
                "twice_worse": r["share_twice_a_worse"],
            },
            f"{r['windows']} windows, {r['engagements']} engagements",
            cm["estimands"][key]["reading"],
        )
    r = cm["beside"]["ctl1h_over_prior_held"]
    add(
        "031",
        "spec 029 replicated",
        "ctl ÷ ctl-prior (1 h windows)",
        "carried prior better",
        "fresh seed 366, blind 1 h windows; reported beside",
        r["gm"],
        r["interval"],
        r.get("median"),
        None,
        f"{r['windows']} windows",
        "reported",
        decided=False,
    )

    lg = d["032"]
    for key, label, ratio in (
        ("E1_ctl_over_prior", "E1", "ctl ÷ ctl-prior (2 h windows)"),
        ("E2_joint_over_prior", "E2", "joint 3.5 h ÷ ctl-prior"),
        ("E1_one_turn", "harm (one-turn)", "ctl ÷ ctl-prior (2 h windows)"),
    ):
        r = lg["estimands"][key]["range"]
        add(
            "032",
            label,
            ratio,
            "carried prior better",
            "ownship legs 2–4 h; blind 2 h windows where contact held (85 of 165)"
            if key != "E1_one_turn"
            else "one-turn 2 h windows",
            r["gm"],
            r["interval"],
            r["median"],
            {
                "better": r["share_prior_better"],
                "twice_better": r["share_twice_prior_better"],
                "twice_worse": r["share_twice_prior_worse"],
            },
            f"{r['windows']} windows, {r['engagements']} engagements",
            lg["estimands"][key]["reading"],
        )
    return out


def errors(d: dict[str, Any]) -> list[dict[str, Any]]:
    """Median range error of the standing systems on the windows each study decided."""
    cp = d["028"]["beside"]["median_error"]
    hd = d["029"]["beside"]["median_error"]["held"]
    cm = d["031"]["beside"]["median_error_held"]
    lg = d["032"]["beside"]["median_error_held"]
    return [
        {
            "study": "028: 2 h windows after the first, both contacts",
            "ctl": cp["ctl-d1-q0.01"]["range"],
            "ctl-prior": cp["ctl-prior"]["range"],
            "reference": cp["history-map"]["range"],
        },
        {
            "study": "029: blind 1 h windows",
            "ctl": hd["ctl-d1-q0.01"],
            "ctl-prior": hd["ctl-prior"],
            "reference": hd["history-map"],
        },
        {
            "study": "031: blind 1 h windows",
            "ctl": cm["a_ctl"],
            "ctl-prior": cm["a"],
            "2 h ctl": cm["b"],
            "2 h ctl-prior": cm["b_prior"],
            "joint": cm["c"],
            "reference": cm["c_ref"],
        },
        {
            "study": "032: blind 2 h windows",
            "ctl": lg["ctl"],
            "ctl-prior": lg["prior"],
            "joint": lg["joint"],
            "reference": lg["ref"],
        },
    ]


def _f(x: float | None, n: int = 3) -> str:
    return "–" if x is None or not math.isfinite(x) else f"{x:.{n}f}"


def tables(rs: list[dict[str, Any]], es: list[dict[str, Any]], seeds: dict[str, int]) -> str:
    lines = [
        "# The long-engagement track: figures of record (spec 034)",
        "",
        "Generated by `scripts/research/long_synthesis.py` from the registered test records'",
        "`study.json`; do not edit. Geometric means of per-window median range error with 95%",
        "intervals over engagements; median window ratio; shares of windows where the side named",
        'in "above 1" is better, twice as good, and twice as bad.',
        "",
        "| spec (seed) | reading | ratio | above 1 means | ratio value | median | better / ×2 better / ×2 worse | windows | outcome |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rs:
        sh = r["shares"]
        s = (
            "–"
            if sh is None
            else f"{_f(sh['better'], 2)} / {_f(sh['twice_better'], 2)} / {_f(sh['twice_worse'], 2)}"
        )
        mark = "" if r["decided"] else " (beside)"
        lines.append(
            f"| {r['spec']} ({seeds[r['spec']]}) | {r['name']}{mark} | {r['ratio']} | {r['above_1']} | "
            f"{_f(r['gm'])} [{_f(r['interval'][0])}, {_f(r['interval'][1])}] | {_f(r['median'], 2)} | "
            f"{s} | {r['n']} | {r['reading']} |"
        )
    lines += ["", "Conventions:", ""]
    for r in rs:
        lines.append(f"- {r['spec']} {r['name']}: {r['convention']}.")
    lines += [
        "",
        "## Median range error on the windows each study decided",
        "",
        "| study | ctl | ctl-prior | 2 h ctl | 2 h ctl-prior | joint | reference (told the truth) |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in es:
        lines.append(
            f"| {e['study']} | {_f(e.get('ctl'))} | {_f(e.get('ctl-prior'))} | {_f(e.get('2 h ctl'))} | "
            f"{_f(e.get('2 h ctl-prior'))} | {_f(e.get('joint'))} | {_f(e.get('reference'))} |"
        )
    lines += [
        "",
        "The reference is told the true manoeuvre history over its own span; it is no ceiling for",
        "a system that carries information in (spec 029 panel).",
        "",
    ]
    return "\n".join(lines)


def _sidecar(path: Path) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/long_synthesis.py",
                "git_commit": g.commit,
                "git_dirty": g.dirty,
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in REC.values()
                },
            },
            indent=1,
        )
        + "\n"
    )


def charts(rs: list[dict[str, Any]], es: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    plt.rcParams.update({"font.size": 8, "svg.fonttype": "none"})
    FIG.mkdir(parents=True, exist_ok=True)
    sel = [r for r in rs if r["spec"] != "026" or r["name"] == "E1"]
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    cols = {
        "028": "#7f7f7f",
        "026": "#7f7f7f",
        "029": "#1f77b4",
        "031": "#d62728",
        "032": "#2ca02c",
    }
    for i, r in enumerate(sel):
        y = len(sel) - 1 - i
        lo, hi = r["interval"]
        ax.errorbar(
            r["gm"],
            y,
            xerr=[[r["gm"] - lo], [hi - r["gm"]]],
            fmt="o" if r["decided"] else "s",
            mfc=cols[r["spec"]] if r["decided"] else "white",
            color=cols[r["spec"]],
            capsize=2,
        )
    ax.axvline(1.0, color="#888", lw=0.8)
    ax.set_xscale("log")
    ax.set_xticks([0.4, 0.6, 1, 1.5, 2, 3], ["0.4", "0.6", "1", "1.5", "2", "3"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks(
        range(len(sel)),
        [f"{r['spec']} {r['name']}: {r['ratio']}" for r in reversed(sel)],
        fontsize=6.5,
    )
    ax.set_xlabel("ratio of median range errors (see the table for what above 1 means)")
    ax.set_title("Every ratio of record (filled: decided; open: reported beside)", fontsize=8)
    fig.tight_layout()
    p = FIG / "ratios.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p)

    systems = (
        ("ctl", "#7f7f7f"),
        ("2 h ctl", "#1f77b4"),
        ("joint", "#9467bd"),
        ("ctl-prior", "#2ca02c"),
        ("2 h ctl-prior", "#98df8a"),
        ("reference", "#d62728"),
    )
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    w = 0.13
    for j, (s, col) in enumerate(systems):
        xs = [i + (j - 2.5) * w for i, e in enumerate(es) if e.get(s) is not None]
        ys = [100 * e[s] for e in es if e.get(s) is not None]
        ax.bar(xs, ys, w, color=col, label=s)
    ax.set_xticks(range(len(es)), [e["study"] for e in es], fontsize=7)
    ax.set_ylabel("median range error, %")
    ax.legend(fontsize=6.5, ncol=3)
    ax.set_title("Median range error on the windows each study decided", fontsize=8)
    fig.tight_layout()
    p = FIG / "errors.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p)


def main() -> int:
    d = _load()
    seeds = {k: int(v["seed"]) for k, v in d.items()}
    rs = rows(d)
    es = errors(d)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tables.md").write_text(tables(rs, es, seeds))
    (OUT / "summary.json").write_text(
        json.dumps(
            {
                "records": {k: str(p.relative_to(ROOT)) for k, p in REC.items()},
                "seeds": seeds,
                "ratios": rs,
                "median_errors": es,
            },
            indent=1,
        )
        + "\n"
    )
    charts(rs, es)
    print((OUT / "tables.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
