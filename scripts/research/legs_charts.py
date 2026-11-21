"""Spec 032 slides: SVG figures from the test record experiments/20261120-legs/.

    uv run python scripts/research/legs_charts.py

* ``estimands.svg``: E1, E2 and E1 on one-turn windows (range, course, speed; the system named ÷
  2-hour ``ctl-prior``), geometric means with engagement intervals, against 1.
* ``bands.svg``: E1 and E2 by range band, with engagement intervals and window counts.
* ``errors.svg``: median range error on decided held windows, by system.
* ``windows.svg``: per-window range ratios for E1 and E2 (log scale), with medians.

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / "experiments/20261120-legs"
CFG = ROOT / "configs/long/legs-test.json"
OUT = ROOT / "site/static/img/2026-11-20-long-legs-slides"


def _sidecar(path: Path, inputs: list[Path]) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/legs_charts.py",
                "git_commit": g.commit,
                "git_dirty": g.dirty,
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
            },
            indent=1,
        )
        + "\n"
    )


def main() -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    from tma2.long.study import engagements
    from tma2.long.study27 import load27
    from tma2.long.study29 import klass, turns_in
    from tma2.long.study30 import _load_joint

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    OUT.mkdir(parents=True, exist_ok=True)
    study = json.loads((REC / "study.json").read_text())
    inputs = [REC / "study.json", CFG]
    cols = {"range": "#1f77b4", "course": "#ff7f0e", "speed": "#2ca02c"}

    # estimands
    est = study["estimands"]
    rows = [
        ("E1: ctl ÷ ctl-prior\n(blind window, registered)", est["E1_ctl_over_prior"]),
        ("E2: joint 3.5 h ÷ ctl-prior\n(blind window, registered)", est["E2_joint_over_prior"]),
        ("ctl ÷ ctl-prior\n(one-turn windows: harm)", est["E1_one_turn"]),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 3.3))
    for i, (_, r) in enumerate(rows):
        for j, q in enumerate(("range", "course", "speed")):
            v = r[q]
            lo, hi = v["interval"]
            ax.errorbar(
                i + (j - 1) * 0.15,
                v["gm"],
                yerr=[[v["gm"] - lo], [hi - v["gm"]]],
                fmt="o",
                color=cols[q],
                capsize=3,
                label=q if i == 0 else None,
            )
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_xticks(range(len(rows)), [n for n, _ in rows], fontsize=7)
    ax.set_ylabel("error ratio (above 1: ctl-prior better)")
    ax.set_title("Test, seed 368: geometric means and 95% engagement intervals", fontsize=8)
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    p = OUT / "estimands.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # bands
    b = study["beside"]
    bands = ("<15", "15-25", "25-35", ">35")
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    for k, (key, col, lab) in enumerate(
        (("E1", "#1f77b4", "E1 ctl ÷ ctl-prior"), ("E2", "#9467bd", "E2 joint ÷ ctl-prior"))
    ):
        for i, band in enumerate(bands):
            r = b[f"{key}_range_{band}"]
            lo, hi = r["interval"]
            x = i + (k - 0.5) * 0.25
            ax.errorbar(
                x,
                r["gm"],
                yerr=[[r["gm"] - lo], [hi - r["gm"]]],
                fmt="o",
                color=col,
                capsize=3,
                label=lab if i == 0 else None,
            )
            if k == 0:
                ax.text(i, 0.05, f"n={r['windows']}", ha="center", fontsize=7)
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.05, 0.25, 1, 4], ["0.05", "0.25", "1", "4"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(len(bands)), [f"{x} km" for x in bands])
    ax.set_ylabel("ratio (above 1: ctl-prior better)")
    ax.set_title("By range at the window (reported, not decided)", fontsize=8)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    p = OUT / "bands.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # errors
    me = b["median_error_held"]
    systems = (
        ("ctl", "2-hour ctl", "#7f7f7f"),
        ("carry", "ctl-carry\n(start only)", "#c5b0d5"),
        ("joint", "joint 3.5 h", "#9467bd"),
        ("prior", "ctl-prior", "#2ca02c"),
        ("ref", "span reference\n(told the truth)", "#d62728"),
    )
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    for j, (k, _, col) in enumerate(systems):
        ax.bar(j, 100 * me[k], 0.7, color=col)
        ax.text(j, 100 * me[k] + 0.3, f"{100 * me[k]:.1f}", ha="center", fontsize=7)
    ax.set_xticks(range(len(systems)), [s[1] for s in systems], fontsize=7)
    ax.set_ylabel("median range error, %")
    ax.set_title("Decided blind 2-hour windows (85), test seed 368", fontsize=8)
    fig.tight_layout()
    p = OUT / "errors.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # windows
    cfg = CFG.resolve()
    stem = cfg.stem
    ratios: dict[str, list[float]] = {"E1": [], "E2": []}
    for e in engagements(cfg, 1):
        a = load27(REC / "raw", f"{stem}-c1", e, 1)
        c = _load_joint(REC / "raw", stem, e)
        if a is None:
            continue
        for w in a["windows"]:
            if w["index"] == 0 or w["carried"] is None:
                continue
            if klass(turns_in(e, int(w["first"]), int(w["rows"]))) != "held":
                continue
            den = w["med"]["ctl-prior"]["range"]
            n1 = w["med"]["ctl-d1-q0.01"]["range"]
            n2 = c[w["index"]]["ctl"]["range"] if c and w["index"] in c else math.nan
            if not all(np.isfinite(x) and x > 0 for x in (den, n1, n2)):
                continue
            ratios["E1"].append(n1 / den)
            ratios["E2"].append(n2 / den)
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    g = np.random.default_rng(0)
    for i, r in enumerate(ratios.values()):
        v = np.clip(np.array(r), 0.03, 30.0)
        ax.scatter(i + g.uniform(-0.3, 0.3, v.size), v, s=6, alpha=0.45, color="#1f77b4")
        ax.plot([i - 0.35, i + 0.35], [np.median(v)] * 2, color="#d62728", lw=1.5)
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.06, 0.25, 1, 4, 16], ["0.06", "0.25", "1", "4", "16"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(2), ["E1: ctl ÷ ctl-prior", "E2: joint ÷ ctl-prior"], fontsize=8)
    ax.set_ylabel("ratio per blind window")
    ax.set_title("Every decided blind window (red: median; clipped 0.03–30)", fontsize=8)
    fig.tight_layout()
    p = OUT / "windows.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)
    print(sorted(x.name for x in OUT.glob("*.svg")), {k: len(v) for k, v in ratios.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
