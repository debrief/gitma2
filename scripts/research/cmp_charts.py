"""Spec 030 slides: SVG figures from the test record experiments/20261120-cmp/.

    uv run python scripts/research/cmp_charts.py

* ``estimands.svg``: D1, D2, D3 (range, course, speed; the system named ÷ 1-hour ``ctl-prior``)
  and, from the supplement, 2-hour ``ctl`` and the joint solve ÷ 2-hour ``ctl-prior``;
  geometric means with engagement intervals, against 1.
* ``errors.svg``: median range error on held windows, by system.
* ``windows.svg``: per-window range ratios for D1, D2 and D3 (log scale), with medians.

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / "experiments/20261120-cmp"
CFG = ROOT / "configs/long/cmp-test.json"
OUT = ROOT / "site/static/img/2026-11-20-held-comparators-slides"


def _sidecar(path: Path, inputs: list[Path]) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/cmp_charts.py",
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
    from tma2.long.study30 import _load_2h, _load_joint, _window_meds

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    OUT.mkdir(parents=True, exist_ok=True)
    study = json.loads((REC / "study.json").read_text())
    sup = json.loads((REC / "supplement.json").read_text())
    inputs = [REC / "study.json", REC / "supplement.json", CFG]
    cols = {"range": "#1f77b4", "course": "#ff7f0e", "speed": "#2ca02c"}

    # estimands
    est = study["estimands"]
    rows: list[tuple[str, dict[str, Any]]] = [
        ("D1: 2-hour ctl\n÷ 1-hour ctl-prior", est["D1_2h_over_prior"]),
        ("D2: joint solve\n÷ 1-hour ctl-prior", est["D2_joint_over_prior"]),
        ("D3: 2-hour ctl-prior\n÷ 1-hour ctl-prior", est["D3_prior2h_over_prior"]),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.3))
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
    extra = [
        ("2-hour ctl\n÷ 2-hour ctl-prior", sup["prior2h_vs_ctl2h"]["held"]),
        ("joint solve\n÷ 2-hour ctl-prior", sup["prior2h_vs_joint_held"]),
    ]
    for i, (_, v) in enumerate(extra):
        lo, hi = v["interval"]
        ax.errorbar(
            len(rows) + i,
            v["gm"],
            yerr=[[v["gm"] - lo], [hi - v["gm"]]],
            fmt="s",
            color=cols["range"],
            mfc="white",
            capsize=3,
        )
    ax.axvline(len(rows) - 0.5, color="#ccc", lw=0.8, ls=":")
    ax.axhline(1.0, color="#888", lw=0.8)
    labels = [n for n, _ in rows] + [n for n, _ in extra]
    ax.set_xticks(range(len(labels)), labels, fontsize=7)
    ax.set_ylabel("error ratio (below 1: denominator worse)")
    ax.set_title(
        "Test, seed 366, held windows: registered (left), supplement in range (right)", fontsize=8
    )
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    p = OUT / "estimands.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # errors
    me = study["beside"]["median_error_held"]
    systems = (
        ("a_ctl", "1-hour ctl", "#7f7f7f"),
        ("a", "1-hour ctl-prior", "#98df8a"),
        ("b", "2-hour ctl", "#1f77b4"),
        ("c", "joint solve", "#9467bd"),
        ("b_prior", "2-hour ctl-prior", "#2ca02c"),
        ("c_ref", "span reference\n(told the truth)", "#d62728"),
    )
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    for j, (k, _, col) in enumerate(systems):
        ax.bar(j, 100 * me[k], 0.7, color=col)
        ax.text(j, 100 * me[k] + 0.3, f"{100 * me[k]:.1f}", ha="center", fontsize=7)
    ax.set_xticks(range(len(systems)), [s[1] for s in systems], fontsize=7)
    ax.set_ylabel("median range error, %")
    ax.set_title("Held windows (no ownship turn), test seed 366", fontsize=8)
    fig.tight_layout()
    p = OUT / "errors.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)

    # windows
    cfg = CFG.resolve()
    stem = cfg.stem
    ratios: dict[str, list[float]] = {"D1": [], "D2": [], "D3": []}
    for e in engagements(cfg, 1):
        a = load27(REC / "raw", f"{stem}-c1", e, 1)
        b = _load_2h(REC / "raw", stem, e)
        c = _load_joint(REC / "raw", stem, e)
        if a is None or b is None:
            continue
        for w in a["windows"]:
            if w["index"] == 0 or w["carried"] is None:
                continue
            first, n = int(w["first"]), int(w["rows"])
            if klass(turns_in(e, first, n)) != "held":
                continue
            den = w["med"]["ctl-prior"]["range"]
            sel = (b["rows"] >= first) & (b["rows"] < first + n)
            nums = {
                "D1": _window_meds(b["states"]["ctl-d1-q0.01"][sel], b["rows"][sel], e)["range"],
                "D2": c[w["index"]]["ctl"]["range"] if c and w["index"] in c else math.nan,
                "D3": _window_meds(b["states"]["ctl-prior"][sel], b["rows"][sel], e)["range"],
            }
            for k, x in nums.items():
                if np.isfinite(x) and np.isfinite(den) and x > 0 and den > 0:
                    ratios[k].append(x / den)
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    g = np.random.default_rng(0)
    for i, r in enumerate(ratios.values()):
        v = np.clip(np.array(r), 0.03, 30.0)
        ax.scatter(i + g.uniform(-0.3, 0.3, v.size), v, s=5, alpha=0.4, color="#1f77b4")
        ax.plot([i - 0.35, i + 0.35], [np.median(v)] * 2, color="#d62728", lw=1.5)
    ax.axhline(1.0, color="#888", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.06, 0.25, 1, 4, 16], ["0.06", "0.25", "1", "4", "16"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks(range(3), [n.split(":")[0] + ":" + n.split(":")[1] for n, _ in rows], fontsize=7)
    ax.set_ylabel("ratio per held window")
    ax.set_title("Every decided held window (red: median; clipped to 0.03–30)", fontsize=8)
    fig.tight_layout()
    p = OUT / "windows.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs)
    print(sorted(x.name for x in OUT.glob("*.svg")), {k: len(v) for k, v in ratios.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
