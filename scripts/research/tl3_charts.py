"""Spec 015 slides: four SVG figures from the committed records.

    uv run python scripts/research/tl3_charts.py --out-dir <dir>

* ``quiet.svg``: false-manoeuvre rate on held-course periods by period length, spec 014's
  search against the repaired one, with the flat and mixed priors and C″ (test seed, D4).
* ``decided.svg``: the refit's share of the search's gain (D1) and the two attainable-headroom
  figures (D3) on the development, validation and test seeds, with 95% intervals.
* ``headroom.svg``: the headroom with a perfect evidence at every registered class threshold
  and match tolerance, and on every split of the test seed.
* ``declared-quiet.svg``: share of targets with one, two and three or more manoeuvres that
  each system calls quiet (test seed).

Reads `experiments/20261113-tl3{-dev,-val,}/summary.json`; writes ``<fig>.svg.json`` beside
each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEEDS = [
    ("development 335\n(spent)", Path("experiments/20261113-tl3-dev/summary.json")),
    ("validation 336", Path("experiments/20261113-tl3-val/summary.json")),
    ("test 337", Path("experiments/20261113-tl3/summary.json")),
]
SPLITS = [
    ("man2", "Annex B"),
    ("shift", "shifted\nprior"),
    ("man2-corr", "correlated\nerrors"),
    ("man2-out", "outliers"),
    ("quiet", "held\ncourse"),
]


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
    have = [(lab, p) for lab, p in SEEDS if (ROOT / p).exists()]
    study = json.loads((ROOT / have[-1][1]).read_text())["study"]
    sums = {lab: json.loads((ROOT / p).read_text())["splits"] for lab, p in have}
    test_lab, test_path = have[-1]
    test: dict[str, Any] = sums[test_lab]
    line = float(study["materiality"])

    def err(v: dict[str, float], key: str) -> list[list[float]]:
        return [[v[key] - v["lo"]], [v["hi"] - v[key]]]

    with plt.rc_context(STYLE):
        # 1. held course by period length
        q = test["quiet"]["quiet"]
        bands = list(q["by_minutes"])
        series = [
            ("spec 014's search", "search2", grey, "o", "--"),
            ("repaired search", "search3", purple, "o", "-"),
            ("repaired, mixed prior", "search3-mix", green, "s", "-"),
            ("repaired, flat prior", "search3-flat", green, "^", ":"),
            ("C″", "c2", orange, "D", "-"),
        ]
        fig, ax = plt.subplots(figsize=(7.4, 3.8))
        x = np.arange(len(bands))
        for name, key, col, mk, ls in series:
            r = [q["by_minutes"][b][key] for b in bands]
            v = np.array([c["rate"] for c in r])
            lo = np.array([c["lo"] for c in r])
            hi = np.array([c["hi"] for c in r])
            ax.errorbar(
                x, v, yerr=[v - lo, hi - v], color=col, marker=mk, ls=ls, capsize=3, label=name
            )
        ax.set_xticks(x, [f"{b} min\n({q['by_minutes'][b]['search3']['n']})" for b in bands])
        ax.set_ylabel("share of quiet periods given a manoeuvre")
        ax.set_ylim(-0.03, 1.05)
        ax.set_title(
            f"Held course: false manoeuvres by period length ({test_lab}, {q['periods']} periods)",
            fontsize=10,
        )
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "quiet.svg")
        plt.close(fig)
        used["quiet.svg"] = [test_path]

        # 2. decided quantities across seeds
        fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.7))
        for i, (lab, _p) in enumerate(have):
            r = sums[lab]["man2"]
            gs = r["gain_share"]["registered"]
            axes[0].errorbar(
                i, gs["share"], yerr=err(gs, "share"), fmt="o", color=orange, capsize=4
            )
            axes[0].text(i + 0.07, gs["share"], f"{gs['share']:.2f}", fontsize=8, va="center")
            for j, (key, col, name) in enumerate(
                (
                    ("ident-search", grey, "a perfect search"),
                    ("ident-all", purple, "a perfect evidence as well"),
                )
            ):
                p = r["headroom"]["registered"][key]["paired"]
                xx = i + (j - 0.5) * 0.25
                axes[1].errorbar(
                    xx,
                    p["geometric_mean"],
                    yerr=err(p, "geometric_mean"),
                    fmt="o",
                    color=col,
                    capsize=4,
                    label=name if i == 0 else None,
                )
                axes[1].text(
                    xx + 0.05, p["geometric_mean"], f"{p['geometric_mean']:.2f}", fontsize=8
                )
        for ax in axes:
            ax.set_xticks(range(len(have)), [lab for lab, _ in have], fontsize=8)
            ax.set_xlim(-0.5, len(have) - 0.3)
        axes[0].axhline(0.5, color="0.6", lw=0.8, ls="--")
        axes[0].set_ylabel("share of the search's gain the refit obtains")
        axes[0].set_title("D1: C″'s transitions refitted, no search", fontsize=9)
        axes[1].axhline(line, color="0.6", lw=0.8, ls="--")
        axes[1].axhline(1.0, color="0.8", lw=0.8)
        axes[1].set_ylabel("search ÷ attainable (paired, per period)")
        axes[1].set_title(f"D3: attainable headroom (line at {line:.2f})", fontsize=9)
        axes[1].legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "decided.svg")
        plt.close(fig)
        used["decided.svg"] = [p for _, p in have]

        # 3. headroom by sensitivity and by split
        fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), gridspec_kw={"width_ratios": [1.5, 1]})
        h = test["man2"]["headroom"]
        ths, tols = (1, 3, 5), (60, 120, 240)
        cols = {60: grey, 120: purple, 240: green}
        for ti, th in enumerate(ths):
            for j, tol in enumerate(tols):
                p = h[f"threshold_{th}_tol_{tol}"]["ident-all"]["paired"]
                xx = ti + (j - 1) * 0.22
                reg = th == 3 and tol == 120
                axes[0].errorbar(
                    xx,
                    p["geometric_mean"],
                    yerr=err(p, "geometric_mean"),
                    fmt="o",
                    color=cols[tol],
                    capsize=4,
                    mfc=cols[tol] if reg else "white",
                    label=f"match within {tol} s" if ti == 0 else None,
                )
                axes[0].text(xx + 0.03, p["hi"] + 0.005, f"{p['geometric_mean']:.2f}", fontsize=7)
        axes[0].set_xticks(range(3), [f"evidence threshold {t}" for t in ths], fontsize=8)
        axes[0].set_title(
            f"Annex B, {test_lab}: every registered sensitivity (filled: registered)", fontsize=9
        )
        axes[0].set_ylabel("search ÷ attainable, perfect evidence (paired)")
        axes[0].legend(frameon=False, fontsize=8)
        sp = [(k, lab) for k, lab in SPLITS if k in test]
        for i, (k, _lab) in enumerate(sp):
            p = test[k]["headroom"]["registered"]["ident-all"]["paired"]
            axes[1].errorbar(
                i,
                p["geometric_mean"],
                yerr=err(p, "geometric_mean"),
                fmt="o",
                color=purple,
                capsize=4,
            )
            axes[1].text(i + 0.08, p["geometric_mean"], f"{p['geometric_mean']:.2f}", fontsize=8)
        axes[1].set_xticks(
            range(len(sp)), [f"{lab}\n({test[k]['periods_scored']})" for k, lab in sp], fontsize=7
        )
        axes[1].set_xlim(-0.5, len(sp) - 0.3)
        axes[1].set_title("Every split (registered settings)", fontsize=9)
        for ax in axes:
            ax.axhline(line, color="0.6", lw=0.8, ls="--")
            ax.axhline(1.0, color="0.8", lw=0.8)
        fig.tight_layout()
        fig.savefig(out / "headroom.svg")
        plt.close(fig)
        used["headroom.svg"] = [test_path]

        # 4. manoeuvring targets called quiet
        dq = test["man2"]["declared_quiet"]
        sysd = [
            ("C″", "c2", orange),
            ("spec 014's search", "search2", grey),
            ("repaired search", "search3", purple),
            ("repaired, mixed prior", "search3-mix", green),
        ]
        sysd = [s for s in sysd if s[1] in dq]
        groups = list(dq[sysd[0][1]])
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        x = np.arange(len(groups))
        w = 0.8 / len(sysd)
        for j, (name, key, col) in enumerate(sysd):
            r = [dq[key][gk] for gk in groups]
            v = np.array([c["rate"] for c in r])
            lo = np.array([max(c["lo"], 0.0) for c in r])
            hi = np.array([c["hi"] for c in r])
            xx = x + (j - (len(sysd) - 1) / 2) * w
            ax.bar(
                xx,
                v,
                w,
                color=col,
                label=name,
                yerr=[v - lo, hi - v],
                capsize=2,
                error_kw={"lw": 0.8},
            )
            for xi, vi, hi_i in zip(xx, v, hi, strict=True):
                ax.text(xi, hi_i + 0.005, f"{vi:.2f}", ha="center", va="bottom", fontsize=7)
        ax.set_xticks(
            x,
            [
                f"{gk} true manoeuvre{'s' if gk != '1' else ''}\n({dq[sysd[0][1]][gk]['n']} periods)"
                for gk in groups
            ],
        )
        ax.set_ylabel("share called quiet (no manoeuvre found)")
        ax.set_title(f"Manoeuvring targets called quiet (Annex B, {test_lab})", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "declared-quiet.svg")
        plt.close(fig)
        used["declared-quiet.svg"] = [test_path]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl3_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
