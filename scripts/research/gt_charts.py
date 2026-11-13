"""Gate T slides: five SVG figures from the committed gate records.

    uv run python scripts/research/gt_charts.py --out-dir <dir>

* ``ratios.svg``: C″ ÷ search (ratio of period medians, 95% interval) on the three seeds
  scored, Annex B data and the shifted prior.
* ``systems.svg``: median period range error of each system on the test seed.
* ``reference.svg``: error against the bound by how tight the bound is, for the reference
  fitted from neutral starts and for the fit started at the truth.
* ``calibration.svg``: stated probability of the first candidate against how often it is the
  true history, by bin.
* ``counts.svg``: manoeuvres in the search's first candidate minus the true number.

Reads only `experiments/20261112-{gt-val,gt2-val,gt2}/`. Writes ``<fig>.svg.json`` beside each
figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNS = [
    ("validation 330\n(first registration)", Path("experiments/20261112-gt-val")),
    ("validation 332", Path("experiments/20261112-gt2-val")),
    ("test 331", Path("experiments/20261112-gt2")),
]
TEST = RUNS[2][1]
SPLITS = [("man2", "Annex B data"), ("shift", "shifted prior")]


def load(p: Path) -> Any:
    return json.loads((ROOT / p).read_text())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import ESTIMATORS, STYLE

    g = read_git_provenance()  # before writing anything
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    used: dict[str, list[Path]] = {}
    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]
    sums = [load(d / "summary.json") for _, d in RUNS]
    test = sums[2]

    with plt.rc_context(STYLE):
        # 1. the headline ratio on three seeds
        fig, ax = plt.subplots(figsize=(8.0, 3.8))
        for j, ((split, lab), col) in enumerate(zip(SPLITS, (purple, orange), strict=True)):
            for i, s in enumerate(sums):
                r = s["splits"][split]["ratios"]["c2_over_search"]
                x = i + (j - 0.5) * 0.25
                ax.errorbar(
                    x,
                    r["value"],
                    yerr=[[r["value"] - r["lo"]], [r["hi"] - r["value"]]],
                    fmt="o",
                    color=col,
                    capsize=4,
                    label=lab if i == 0 else None,
                )
                ax.text(x + 0.04, r["value"], f"{r['value']:.2f}", fontsize=8, va="center")
        ax.axhline(1.10, color=purple, lw=0.8, ls="--")
        ax.axhline(1.00, color=orange, lw=0.8, ls="--")
        ax.set_xticks(range(3), [lab for lab, _ in RUNS])
        ax.set_xlim(-0.5, 2.6)
        ax.set_ylabel("C″ ÷ search (ratio of period medians)")
        ax.set_title(
            "The search against C″ read as a track; dashed lines are the registered thresholds",
            fontsize=10,
        )
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "ratios.svg")
        plt.close(fig)
        used["ratios.svg"] = [d / "summary.json" for _, d in RUNS]

        # 2. every system on the test seed
        rows = [
            ("true history,\ntimes held", "history-fixed", green),
            ("true history,\nwith the prior", "history-map", green),
            ("search", "search", purple),
            ("search from\nnothing", "search-none", purple),
            ("C″ read\nas a track", "c2", orange),
            ("one leg", "one-leg", grey),
        ]
        fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8), sharey=True)
        for ax, (split, lab) in zip(axes, SPLITS, strict=True):
            sp = test["splits"][split]
            v = [sp["systems"][k]["median_period_range"] for _, k, _ in rows]
            xs = np.arange(len(rows))
            ax.bar(xs, v, 0.6, color=[c for *_, c in rows])
            for xi, vi in zip(xs, v, strict=True):
                ax.text(xi, vi + 0.005, f"{vi:.3f}", ha="center", fontsize=8)
            ax.set_xticks(xs, [r[0] for r in rows], fontsize=7)
            ax.set_title(f"{lab} ({sp['periods_with_determined_rows']} periods)", fontsize=10)
        axes[0].set_ylabel("median period range error (relative)")
        fig.suptitle("Test seed 331: every system as a track over the period", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "systems.svg")
        plt.close(fig)
        used["systems.svg"] = [TEST / "summary.json"]

        # 3. the reference by how tight the bound is
        bands = ["tight", "middle", "loose"]
        fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8), sharey=True)
        for ax, (split, lab) in zip(axes, SPLITS, strict=True):
            sy = test["splits"][split]["systems"]
            x = np.arange(3)
            for i, (k, name, col) in enumerate(
                [
                    ("history-fixed", "fitted from neutral starts, times held", green),
                    ("truth-fit", "fit started at the truth (first registration)", grey),
                ]
            ):
                e = [sy[k][f"efficiency_range_{b}"] for b in bands]
                ax.bar(x + (i - 0.5) * 0.35, e, 0.35, color=col, label=name)
                for xi, ei in zip(x, e, strict=True):
                    ax.text(xi + (i - 0.5) * 0.35, ei + 0.03, f"{ei:.2f}", ha="center", fontsize=8)
            ax.axhline(1.0, color="k", lw=0.8, ls="--")
            ax.axhspan(0.8, 1.3, color=green, alpha=0.08)
            ax.set_xticks(x, ["bound < 0.05", "0.05 to 0.2", "0.2 to 0.5"], fontsize=8)
            ax.set_xlabel("bound on relative range")
            ax.set_title(lab, fontsize=10)
        axes[0].set_ylabel("range error ÷ Cramér–Rao bound")
        fig.legend(
            *axes[0].get_legend_handles_labels(),
            frameon=False,
            fontsize=8,
            loc="lower center",
            ncol=2,
        )
        fig.suptitle(
            "Below 1 is a fault: a fit started at the truth stays there (test seed 331)",
            fontsize=10,
        )
        fig.tight_layout(rect=(0, 0.06, 1, 1))
        fig.savefig(out / "reference.svg")
        plt.close(fig)
        used["reference.svg"] = [TEST / "summary.json"]

        # 4. candidates: stated against right
        fig, ax = plt.subplots(figsize=(5.6, 4.6))
        ax.plot([0, 1], [0, 1], color="k", lw=0.8, ls="--")
        for (split, lab), col in zip(SPLITS, (purple, orange), strict=True):
            c = test["splits"][split]["candidates"]
            st = [b["stated"] for b in c["bins"]]
            rt = [b["right"] for b in c["bins"]]
            n = [b["periods"] for b in c["bins"]]
            se = [1.96 * (r * (1 - r) / k) ** 0.5 for r, k in zip(rt, n, strict=True)]
            ax.errorbar(st, rt, yerr=se, fmt="o-", color=col, capsize=3, label=lab)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("stated probability of the first candidate")
        ax.set_ylabel("share where it is the true history")
        ax.set_title("Honest on average on Annex B data; not under the shifted prior", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "calibration.svg")
        plt.close(fig)
        used["calibration.svg"] = [TEST / "summary.json"]

        # 5. manoeuvres found minus true
        fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6), sharey=True)
        for ax, (split, lab), col in zip(axes, SPLITS, (purple, orange), strict=True):
            per = load(TEST / f"{split}.periods.json")
            d = np.array([len(p["candidates"][0]["spans"]) - len(p["true"]) for p in per])
            ks = np.arange(-4, 4)
            share = [float((d == k).mean()) for k in ks]
            ax.bar(ks, share, 0.7, color=col)
            ax.set_xticks(ks)
            ax.set_xlabel("manoeuvres in the first candidate minus true")
            ax.set_title(
                f"{lab}: fewer {float((d < 0).mean()):.0%}, right {float((d == 0).mean()):.0%}, "
                f"more {float((d > 0).mean()):.0%}",
                fontsize=10,
            )
        axes[0].set_ylabel("share of periods")
        fig.suptitle("The search under-counts manoeuvres (test seed 331, 300 periods)", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "counts.svg")
        plt.close(fig)
        used["counts.svg"] = [TEST / "man2.periods.json", TEST / "shift.periods.json"]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/gt_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
