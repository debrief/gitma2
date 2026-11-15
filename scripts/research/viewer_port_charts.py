"""Spec 021 slides: figures from the port's committed record.

    uv run python scripts/research/viewer_port_charts.py --record experiments/20261116-port \\
        --out-dir site/static/img/<slug>

* ``stages.svg``: live mode in Chromium on each demo engagement, the time in each stage
  (``browser-live.json``).
* ``margins.svg``: per check scenario, the largest browser–Python difference in a confirmation
  cost drop against the smallest margin of any decision from its threshold, C and E
  (``node-per-scenario.json``): the gap between them is why no decision differs.
* ``agreement.svg``: per check scenario, rows with an identical segmentation, C and E.

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import STYLE

    g = read_git_provenance()
    rec, out = Path(a.record), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    live = json.loads((rec / "browser-live.json").read_text())
    per = json.loads((rec / "node-per-scenario.json").read_text())
    used: dict[str, list[Path]] = {}
    with plt.rc_context(STYLE):
        # 1. stage times of live mode
        names = ["least squares", "GLR statistic", "search", "confirmation", "estimates"]
        cols = ["#c7c7c7", "#9edae5", "#aec7e8", "#9467bd", "#2ca02c"]
        fig, ax = plt.subplots(figsize=(7.6, 3.4))
        for i, e in enumerate(live["live"]):
            st = {s["stage"]: s["seconds"] for s in e["stages"]}
            marks = [
                (names[0], st["least squares"], st["GLR statistic"]),
                (names[1], st["GLR statistic"], st["search"]),
                (names[2], st["search"], st["confirmation"]),
                (names[3], st["confirmation"], st["estimates"]),
                (names[4], st["estimates"], st["done"]),
            ]
            for (n, t0, t1), c in zip(marks, cols, strict=True):
                ax.barh(i, t1 - t0, left=t0, color=c, label=n if i == 0 else None)
            ax.text(st["done"] + 1, i, f"{e['rows']} rows", va="center", fontsize=8)
        ax.set_yticks(range(len(live["live"])), [f"{e['engagement'] + 1}" for e in live["live"]])
        ax.set_ylabel("demo engagement")
        ax.set_xlabel("seconds in Chromium, one WASM thread")
        ax.invert_yaxis()
        ax.legend(
            frameon=False, fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.22)
        )
        fig.tight_layout()
        fig.savefig(out / "stages.svg")
        plt.close(fig)
        used["stages.svg"] = [rec / "browser-live.json"]

        # 2. differences against margins
        fig, ax = plt.subplots(figsize=(7.6, 3.4))
        x = np.arange(len(per))
        for k, col, m in (("c", "#9467bd", "o"), ("e", "#2ca02c", "s")):
            d = [max(r["stages"][k]["max_drop_abs_diff_before"], 1e-16) for r in per]
            mg = [r["stages"][k]["min_abs_score"] for r in per]
            ax.scatter(
                x,
                d,
                color=col,
                marker=m,
                s=14,
                alpha=0.6,
                label=f"{k.upper()}: largest cost-drop difference",
            )
            ax.scatter(
                x,
                mg,
                color=col,
                marker=m,
                s=22,
                facecolors="none",
                label=f"{k.upper()}: smallest decision margin",
            )
        ax.set_yscale("log")
        ax.set_xticks(x, [str(r["ordinal"]) for r in per], fontsize=6)
        ax.set_xlabel("check scenario (seed 319 ordinal)")
        ax.set_ylabel("χ² units")
        ax.legend(frameon=False, fontsize=6.5, ncol=2)
        fig.tight_layout()
        fig.savefig(out / "margins.svg")
        plt.close(fig)
        used["margins.svg"] = [rec / "node-per-scenario.json"]

        # 3. identical rows
        fig, ax = plt.subplots(figsize=(7.6, 2.8))
        for j, (k, col) in enumerate((("c", "#9467bd"), ("e", "#2ca02c"))):
            same = [r["stages"][k]["rows_same"] for r in per]
            rows = [r["stages"][k]["rows"] for r in per]
            ax.bar(x + (j - 0.5) * 0.4, rows, 0.4, color="#dddddd")
            ax.bar(x + (j - 0.5) * 0.4, same, 0.4, color=col, label=f"{k.upper()}: identical rows")
        ax.set_xticks(x, [str(r["ordinal"]) for r in per], fontsize=6)
        ax.set_ylabel("scored rows")
        tot = sum(r["stages"][k]["rows"] for r in per for k in "ce")
        ok = sum(r["stages"][k]["rows_same"] for r in per for k in "ce")
        ax.set_title(f"{ok} of {tot} scored rows identical (grey: rows not identical)", fontsize=9)
        ax.legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "agreement.svg")
        plt.close(fig)
        used["agreement.svg"] = [rec / "node-per-scenario.json"]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/viewer_port_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
