"""Spec 037 slides: the test record in three SVG charts, from committed JSON only.

    uv run python scripts/research/rmis_charts.py --out-dir site/static/img/2026-11-26-regressor-mismatch

* ``range-by-condition.svg``: median range error of each system on the seven conditions
  (`experiments/20261126-rmis/summary.json`).
* ``readings.svg``: the registered paired ratios with their intervals
  (`experiments/20261126-rmis/readings.json`).
* ``coverage.svg``: coverage of the stated 95% intervals on the three decided conditions.

Writes ``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REC = Path("experiments/20261126-rmis")
SUMMARY = REC / "summary.json"
READINGS = REC / "readings.json"


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
    summ: dict[str, Any] = json.loads((ROOT / SUMMARY).read_text())
    rd: dict[str, Any] = json.loads((ROOT / READINGS).read_text())
    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]

    def side(name: str, inputs: list[Path], note: str) -> None:
        (out / f"{name}.svg.json").write_text(
            json.dumps(
                {
                    "figure": f"{name}.svg",
                    "script": "scripts/research/rmis_charts.py",
                    "inputs": {
                        str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in inputs
                    },
                    "note": note,
                    "git_commit": g.commit,
                    "git_dirty": g.dirty,
                },
                indent=1,
            )
            + "\n"
        )

    with plt.rc_context(STYLE):
        conds = summ["conditions"]
        labels = {
            "off": "clean",
            "all-central": "primary\n(all four kinds)",
            "ho-both": "held out\n(sinusoid + bursts)",
            "out-central": "outliers",
            "corr-central": "correlated",
            "ho-osc": "sinusoid",
            "ho-burst": "bursts",
        }
        series = [
            ("c2-robust", "C″, robust final solve", grey),
            ("reg", "regressor, unchanged", orange),
            ("ft", "regressor, fine-tuned", green),
            ("robust-true", "robust solve told the true manoeuvre times", purple),
        ]
        fig, ax = plt.subplots(figsize=(9.2, 3.8))
        x = np.arange(len(conds))
        w = 0.2
        for i, (key, lab, col) in enumerate(series):
            ax.bar(
                x + (i - 1.5) * w,
                [summ["median_range"][c][key] for c in conds],
                w,
                label=lab,
                color=col,
            )
        ax.set_xticks(x)
        ax.set_xticklabels([labels[c] for c in conds], fontsize=8)
        ax.set_ylabel("median relative range error")
        ax.set_title(
            "Test seed 371, 1,000 engagements a condition (the same engagements)", fontsize=9
        )
        ax.legend(fontsize=7, frameon=False)
        fig.tight_layout()
        fig.savefig(out / "range-by-condition.svg")
        plt.close(fig)
        side(
            "range-by-condition",
            [SUMMARY],
            "median over engagements of the engagement's median error over its scored rows",
        )

        rows = [
            ("M1  C″-robust ÷ fine-tuned, primary", rd["M1"]["range"]),
            ("M2  C″-robust ÷ fine-tuned, held out", rd["M2"]["range"]),
            ("M3  unchanged ÷ fine-tuned, primary", rd["M3"]["all-central"]["range"]["pooled"]),
            ("M3  unchanged ÷ fine-tuned, held out", rd["M3"]["ho-both"]["range"]["pooled"]),
            ("M4  unchanged ÷ fine-tuned, clean", rd["M4"]["range"]["pooled"]),
            ("Y1  C″-robust ÷ hybrid, clean", rd["Y1"]["off"]["range"]["pooled"]),
            ("Y1  C″-robust ÷ hybrid, primary", rd["Y1"]["all-central"]["range"]["pooled"]),
            ("Y2  fine-tuned ÷ hybrid, clean", rd["Y2"]["off"]["range"]["pooled"]),
            ("Y2  fine-tuned ÷ hybrid, primary", rd["Y2"]["all-central"]["range"]["pooled"]),
        ]
        fig, ax = plt.subplots(figsize=(8.4, 3.8))
        y = np.arange(len(rows))[::-1]
        for yi, (_lab, r) in zip(y, rows, strict=True):
            col = green if r["lo"] > 1 else orange if r["hi"] < 1 else grey
            ax.plot([r["lo"], r["hi"]], [yi, yi], color=col, lw=2.5)
            ax.plot([r["ratio"]], [yi], "o", color=col, ms=5)
            ax.text(r["hi"] + 0.03, yi, f"{r['ratio']:.2f}", va="center", fontsize=8)
        ax.axvline(1.0, color="k", lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([lab for lab, _ in rows], fontsize=8)
        ax.set_xlabel(
            "paired per-engagement ratio of range error, three seeds pooled (95% interval)"
        )
        ax.set_xlim(0.85, 2.6)
        fig.tight_layout()
        fig.savefig(out / "readings.svg")
        plt.close(fig)
        side(
            "readings",
            [READINGS],
            "above 1: the denominator is better; green wholly above 1, orange wholly below",
        )

        cov = rd["M5"]["coverage"]
        fig, ax = plt.subplots(figsize=(7.4, 3.4))
        cs = ["off", "all-central", "ho-both"]
        qs = [
            ("range", "range", green),
            ("course_deg", "course (where stated)", orange),
            ("speed_kt", "speed", purple),
        ]
        x = np.arange(len(cs))
        for i, (q, lab, col) in enumerate(qs):
            vals = [float(np.mean(cov[c][q]["coverage_each"])) for c in cs]
            lo = [cov[c][q]["lo_min"] for c in cs]
            hi = [cov[c][q]["hi_max"] for c in cs]
            xx = x + (i - 1) * 0.22
            ax.errorbar(
                xx,
                vals,
                yerr=[np.array(vals) - lo, np.array(hi) - vals],
                fmt="o",
                color=col,
                label=lab,
                capsize=3,
                ms=5,
            )
        ax.axhline(0.95, color="k", lw=0.8)
        ax.axhspan(0.90, 0.99, color="k", alpha=0.06)
        ax.set_xticks(x)
        ax.set_xticklabels(["clean", "primary", "held out"])
        ax.set_ylim(0.86, 1.0)
        ax.set_ylabel("coverage of the stated 95% interval")
        ax.set_title(
            "Average coverage, three fine-tuned seeds (bar: widest interval over seeds)", fontsize=9
        )
        ax.legend(fontsize=7, frameon=False, loc="lower left")
        fig.tight_layout()
        fig.savefig(out / "coverage.svg")
        plt.close(fig)
        side(
            "coverage",
            [READINGS],
            "registered band 0.90 to 0.99 shaded; coverage is an average and is not conditional (review.md)",
        )
    print(f"wrote three figures to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
