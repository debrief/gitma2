"""Spec 014 slides: six SVG figures from the committed records.

    uv run python scripts/research/tl2_charts.py --out-dir <dir>

* ``systems.svg``: median period range error of each system on the test seed's Annex B,
  shifted and held-course splits.
* ``decided.svg``: the refit's share of the search's gain (D1) and the two attainable-headroom
  figures (D3) on the tuning, validation and test seeds, with 95% intervals.
* ``classes.svg``: periods by class (right, ambiguous, search failure, evidence failure).
* ``quiet.svg``: false-manoeuvre rate on held-course periods by system and seed (D4).
* ``thinning.svg``: each thinning form's cost against the search's run time (tuning seed).
* ``conditions.svg``: C″ and the search under correlated and outlying bearing errors.

Reads `experiments/20261112-tl2{-tuning,-val,}/summary.json` and
`experiments/20261112-tl2-thin/*.json`; writes ``<fig>.svg.json`` beside each figure naming
the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SEEDS = [
    ("tuning 333", Path("experiments/20261112-tl2-tuning/summary.json")),
    ("validation 334", Path("experiments/20261112-tl2-val/summary.json")),
    ("test 335", Path("experiments/20261112-tl2/summary.json")),
]
THIN = [
    Path("experiments/20261112-tl2-thin/thin-clean.json"),
    Path("experiments/20261112-tl2-thin/thin-outliers.json"),
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
    sums = {lab: json.loads((ROOT / p).read_text())["splits"] for lab, p in have}
    last_lab, last_path = have[-1]
    test: dict[str, Any] = sums[last_lab]

    def err(v: dict[str, float], key: str = "geometric_mean") -> list[list[float]]:
        return [[v[key] - v["lo"]], [v["hi"] - v[key]]]

    with plt.rc_context(STYLE):
        # 1. every system, three splits
        rows = [
            ("C″ as\na track", "c2", orange),
            ("C″\nrefitted", "c2-refit", orange),
            ("search,\nflat prior", "search-flat", grey),
            ("search", "search2", purple),
            ("search,\nmixed prior", "search-mix", purple),
            ("true\nhistory", "history-map", green),
        ]
        splits = [
            (k, lab)
            for k, lab in (
                ("man2", "Annex B"),
                ("shift", "shifted prior"),
                ("quiet", "held course"),
            )
            if k in test
        ]
        fig, axes = plt.subplots(1, len(splits), figsize=(3.6 * len(splits), 3.8), squeeze=False)
        for ax, (k, lab) in zip(axes[0], splits, strict=True):
            sy = test[k]["systems"]
            keep = [r for r in rows if r[1] in sy]
            v = [sy[r[1]]["median_period_range"] for r in keep]
            xs = np.arange(len(keep))
            ax.bar(xs, v, 0.65, color=[r[2] for r in keep])
            for xi, vi in zip(xs, v, strict=True):
                ax.text(xi, vi, f"{vi:.3f}", ha="center", va="bottom", fontsize=7)
            ax.set_xticks(xs, [r[0] for r in keep], fontsize=6.5)
            ax.set_title(f"{lab} ({test[k]['periods_with_determined_rows']} periods)", fontsize=9)
        axes[0][0].set_ylabel("median period range error (relative)")
        fig.suptitle(f"Every system as a track ({last_lab})", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "systems.svg")
        plt.close(fig)
        used["systems.svg"] = [last_path]

        # 2. the decided quantities across seeds
        fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
        for i, (lab, _p) in enumerate(have):
            r = sums[lab]["man2"]
            gs = r["gain_share"]["all"]
            axes[0].errorbar(
                i, gs["share"], yerr=err(gs, "share"), fmt="o", color=orange, capsize=4
            )
            axes[0].text(i + 0.06, gs["share"], f"{gs['share']:.2f}", fontsize=8, va="center")
            for j, (key, col, name) in enumerate(
                (
                    ("ident-search", grey, "a perfect search"),
                    ("ident-all", purple, "a perfect evidence as well"),
                )
            ):
                p = r["headroom"][key]["paired"]
                x = i + (j - 0.5) * 0.25
                axes[1].errorbar(
                    x,
                    p["geometric_mean"],
                    yerr=err(p),
                    fmt="o",
                    color=col,
                    capsize=4,
                    label=name if i == 0 else None,
                )
                axes[1].text(
                    x + 0.05, p["geometric_mean"], f"{p['geometric_mean']:.2f}", fontsize=8
                )
        for ax in axes:
            ax.set_xticks(range(len(have)), [lab for lab, _ in have])
            ax.set_xlim(-0.5, len(have) - 0.3)
        axes[0].axhline(1.0, color="k", lw=0.6, ls=":")
        axes[0].axhline(0.0, color="k", lw=0.6, ls=":")
        axes[0].set_ylabel("share of the search's gain over C″")
        axes[0].set_title("Obtained by refitting C″'s own manoeuvre times", fontsize=9)
        axes[1].axhline(1.10, color="k", lw=0.8, ls="--")
        axes[1].set_ylabel("search ÷ composite (geometric mean per period)")
        axes[1].set_title("Attainable headroom; dashed: the 10% line", fontsize=9)
        axes[1].legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "decided.svg")
        plt.close(fig)
        used["decided.svg"] = [p for _, p in have]

        # 3. classes
        names = ["right", "ambiguous", "search_failure", "evidence_failure"]
        labels = ["history right", "ambiguous", "search failure", "evidence failure"]
        cols = [green, grey, orange, purple]
        ks = [k for k in ("man2", "shift", "quiet") if k in test]
        fig, ax = plt.subplots(figsize=(7.4, 3.2))
        left = np.zeros(len(ks))
        for n, lab, col in zip(names, labels, cols, strict=True):
            v = np.array([test[k]["classes"][n]["rate"] for k in ks])
            ax.barh(range(len(ks)), v, left=left, color=col, label=lab)
            for y, (lv, vv) in enumerate(zip(left, v, strict=True)):
                if vv > 0.05:
                    ax.text(lv + vv / 2, y, f"{vv:.0%}", ha="center", va="center", fontsize=8)
            left += v
        tick = {"man2": "Annex B", "shift": "shifted prior", "quiet": "held course"}
        ax.set_yticks(range(len(ks)), [tick[k] for k in ks])
        ax.set_xlim(0, 1)
        ax.set_xlabel("share of periods")
        ax.set_title(f"Why the search's first candidate is wrong ({last_lab})", fontsize=10)
        ax.legend(
            frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.25)
        )
        fig.tight_layout()
        fig.savefig(out / "classes.svg", bbox_inches="tight")
        plt.close(fig)
        used["classes.svg"] = [last_path]

        # 4. false manoeuvres on held course
        sysq = [
            ("C″", "c2", orange),
            ("search,\nflat prior", "search-flat", grey),
            ("search", "search2", purple),
            ("search,\nmixed prior", "search-mix", purple),
        ]
        fig, ax = plt.subplots(figsize=(7.4, 3.6))
        w = 0.8 / max(len(have), 1)
        for i, (lab, _p) in enumerate(have):
            q = sums[lab]["quiet"]["quiet"]["false_manoeuvre_rate"]
            for j, (_n, key, col) in enumerate(sysq):
                if key not in q:
                    continue
                v = q[key]
                x = j + (i - (len(have) - 1) / 2) * w
                ax.bar(
                    x, v["rate"], w * 0.9, color=col, alpha=0.45 + 0.55 * i / max(len(have) - 1, 1)
                )
                ax.errorbar(
                    x,
                    v["rate"],
                    yerr=[[v["rate"] - v["lo"]], [v["hi"] - v["rate"]]],
                    color="k",
                    lw=0.8,
                )
                ax.text(x, v["hi"] + 0.02, f"{v['rate']:.0%}", ha="center", fontsize=7)
        ax.set_xticks(range(len(sysq)), [n for n, *_ in sysq], fontsize=8)
        ax.set_ylim(0, 1)
        ax.set_ylabel("held-course periods with a manoeuvre declared")
        ax.set_title(
            "A target that never manoeuvres (" + ", ".join(lab for lab, _ in have) + ")",
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(out / "quiet.svg")
        plt.close(fig)
        used["quiet.svg"] = [p for _, p in have]

        # 5. thinning
        if all((ROOT / p).exists() for p in THIN):
            fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
            for ax, p, title in zip(
                axes, THIN, ("clean bearings", "2% outlying bearings"), strict=True
            ):
                rows_t = next(iter(json.loads((ROOT / p).read_text())["splits"].values()))
                for r in rows_t:
                    kind = r["form"].split(":")[0]
                    col = {"none": "k", "drop": grey, "fixed": green, "adaptive": orange}[kind]
                    c = r["cost"]
                    ax.errorbar(
                        r["seconds"],
                        c["geometric_mean"],
                        yerr=err(c),
                        fmt="o",
                        color=col,
                        capsize=3,
                    )
                    ax.text(r["seconds"] + 0.4, c["geometric_mean"], r["form"], fontsize=7)
                ax.axhline(1.0, color="k", lw=0.6, ls=":")
                ax.set_xlabel("search seconds a period")
                ax.set_title(title, fontsize=9)
            axes[0].set_ylabel("range error ÷ full data's (per period)")
            fig.suptitle(
                "Thinning the bearings: dropped (grey), normal points (green), "
                "bearing-rate bins (orange); tuning seed 333",
                fontsize=10,
            )
            fig.tight_layout()
            fig.savefig(out / "thinning.svg")
            plt.close(fig)
            used["thinning.svg"] = list(THIN)

        # 6. bearing-error conditions
        cond = [
            (k, lab)
            for k, lab in (
                ("man2", "independent"),
                ("man2-corr", "correlated"),
                ("man2-out", "2% outliers"),
            )
            if k in test
        ]
        if len(cond) == 3:
            sysc = [
                ("C″ as a track", "c2", orange),
                ("C″ refitted", "c2-refit", grey),
                ("search", "search2", purple),
                ("true history", "history-map", green),
            ]
            fig, ax = plt.subplots(figsize=(7.4, 3.6))
            x = np.arange(len(cond))
            for j, (name, key, col) in enumerate(sysc):
                v = [test[k]["systems"][key]["median_period_range"] for k, _ in cond]
                ax.bar(x + (j - 1.5) * 0.2, v, 0.2, color=col, label=name)
                for xi, vi in zip(x, v, strict=True):
                    ax.text(
                        xi + (j - 1.5) * 0.2, vi, f"{vi:.3f}", ha="center", va="bottom", fontsize=7
                    )
            ax.set_xticks(
                x,
                [f"{lab}\n({test[k]['periods_with_determined_rows']} periods)" for k, lab in cond],
            )
            ax.set_ylabel("median period range error (relative)")
            ax.set_title(f"Bearing errors the fits are not told about ({last_lab})", fontsize=10)
            ax.legend(frameon=False, fontsize=8)
            fig.tight_layout()
            fig.savefig(out / "conditions.svg")
            plt.close(fig)
            used["conditions.svg"] = [last_path]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl2_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
