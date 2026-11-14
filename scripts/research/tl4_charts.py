"""Spec 016 slides: six SVG figures from the committed records.

    uv run python scripts/research/tl4_charts.py --out-dir <dir>

* ``verdicts.svg``: the registered comparison, declared control ÷ learned arc read-out, for
  three seeds on every criterion split, with 95% intervals.
* ``systems.svg``: median period range error of every system on every split.
* ``controls.svg``: the standing search ÷ the declared control by split on the tuning,
  validation and test seeds.
* ``manoeuvres.svg``: manoeuvres missed and false for C″, the search, the control and the
  model's detector.
* ``training.svg``: the monitor curve of the three training seeds.
* ``tracks.svg``: three stored periods as track plots (ownship blue, target red, the
  control and the learned track). The periods are chosen by a rule, not by eye: on the
  shifted split, of the 20 stored periods, the one where the learned read-out is worst
  against the control and the one where it is best; on the outlier split the first stored
  period with a true manoeuvre.

Reads `experiments/20261113-tl4-{tuning,val}/summary.json`, `experiments/20261114-tl4/`
(`summary.json`, `tracks.npz`: tracks at scored rows for the first 20 periods of three
splits, extracted from the results branch) and `experiments/20261114-tlm-runs/`; writes
``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TEST = Path("experiments/20261114-tl4")
SEEDS = [
    ("tuning 338", Path("experiments/20261113-tl4-tuning/summary.json")),
    ("validation 340", Path("experiments/20261113-tl4-val/summary.json")),
    ("test 341", TEST / "summary.json"),
]
SPLITS = [
    ("man2", "Annex B"),
    ("shift", "shifted\nprior"),
    ("shift2", "shifted\nprior 2"),
    ("quiet", "held\ncourse"),
    ("man2-corr", "correlated\nerrors"),
    ("man2-out", "outliers\n2%"),
    ("man2-out-harsh", "outliers\n5%"),
    ("man2-bias", "bias"),
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
    sums = {lab: json.loads((ROOT / p).read_text())["splits"] for lab, p in SEEDS}
    summary = json.loads((ROOT / TEST / "summary.json").read_text())
    test: dict[str, Any] = summary["splits"]
    crit = summary["criteria"]

    def bar(v: dict[str, float]) -> list[list[float]]:
        return [[v["geometric_mean"] - v["lo"]], [v["hi"] - v["geometric_mean"]]]

    with plt.rc_context(STYLE):
        # 1. the registered comparison
        rows = [(k, lab, crit["splits"].get(k) or crit["no_harm"].get(k)) for k, lab in SPLITS]
        rows = [r for r in rows if r[2]]
        fig, ax = plt.subplots(figsize=(8.6, 3.9))
        for i, (_k, _lab, v) in enumerate(rows):
            for j, (_seed, r) in enumerate(sorted(v["seeds"].items())):
                d = r["declared"]
                ax.errorbar(
                    i + (j - 1) * 0.2,
                    d["geometric_mean"],
                    yerr=bar(d),
                    fmt="o",
                    color=purple,
                    capsize=3,
                    ms=4,
                    label="one training seed" if i == 0 and j == 0 else None,
                )
                ax.plot(
                    i + (j - 1) * 0.2,
                    d["median_ratio"],
                    marker="_",
                    color=orange,
                    ms=10,
                    mew=2,
                    label="median per-period ratio" if i == 0 and j == 0 else None,
                )
            ax.text(i, 0.615, v["verdict"], ha="center", fontsize=7, color="0.3")
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        ax.set_xticks(range(len(rows)), [lab for _, lab, _ in rows], fontsize=8)
        ax.set_ylim(0.6, 1.2)
        ax.set_ylabel("declared control ÷ learned track\n(above 1: the learned track is better)")
        ax.set_title("The registered comparison, test seed 341 (paired per period)", fontsize=10)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
        fig.tight_layout()
        fig.savefig(out / "verdicts.svg")
        plt.close(fig)
        used["verdicts.svg"] = [TEST / "summary.json"]

        # 2. every system
        systems = [
            ("C″ as a track", "c2", grey),
            ("standing search", "search3", "#b9a3d0"),
            ("classical control", "ctl-d1-q0.01", purple),
            ("learned, own track", "learned-s1", "#f3cf95"),
            ("learned, arc read-out", "learned-s1-arc", orange),
            ("true history", "history-best", green),
        ]
        have = [(k, lab) for k, lab in SPLITS if k in test]
        fig, ax = plt.subplots(figsize=(10.0, 4.0))
        x = np.arange(len(have))
        w = 0.8 / len(systems)
        for j, (name, key, col) in enumerate(systems):
            v = [test[k]["systems"][key]["median_period_range"] for k, _ in have]
            ax.bar(x + (j - (len(systems) - 1) / 2) * w, v, w, color=col, label=name)
        ax.set_xticks(x, [lab for _, lab in have], fontsize=8)
        ax.set_ylim(0, 0.3)
        for i, (k, _) in enumerate(have):
            c2 = test[k]["systems"]["c2"]["median_period_range"]
            if c2 > 0.3:
                ax.text(i - 0.33, 0.292, f"{c2:.2f}", ha="center", fontsize=7, color="0.3")
        ax.set_ylabel("median period range error (relative)")
        ax.set_title("Every system, test seed 341 (seed 1 of the learned model)", fontsize=10)
        ax.legend(frameon=False, fontsize=8, ncol=3)
        fig.tight_layout()
        fig.savefig(out / "systems.svg")
        plt.close(fig)
        used["systems.svg"] = [TEST / "summary.json"]

        # 3. the controls across seeds
        fig, ax = plt.subplots(figsize=(9.0, 3.8))
        cols = {"tuning 338": grey, "validation 340": "#b9a3d0", "test 341": purple}
        for i, (k, _lab) in enumerate(have):
            for j, (lab, _p) in enumerate(SEEDS):
                c = sums[lab].get(k, {}).get("comparisons", {}).get("search3_over_ctl-d1-q0.01")
                if not c:
                    continue
                ax.errorbar(
                    i + (j - 1) * 0.22,
                    c["geometric_mean"],
                    yerr=bar(c),
                    fmt="o",
                    color=cols[lab],
                    capsize=3,
                    ms=4,
                    label=lab if i == 0 else None,
                )
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        ax.set_yscale("log")
        ax.set_yticks([0.8, 1, 1.5, 2, 3, 4], ["0.8", "1", "1.5", "2", "3", "4"])
        ax.set_xticks(x, [lab for _, lab in have], fontsize=8)
        ax.set_ylabel("standing search ÷ classical control\n(above 1: the control is better)")
        ax.set_title("What the classical control adds, on three seeds", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "controls.svg")
        plt.close(fig)
        used["controls.svg"] = [p for _, p in SEEDS]

        # 4. manoeuvres missed and false
        who = [
            ("C″", "c2", grey),
            ("standing search", "search3", "#b9a3d0"),
            ("classical control", "ctl-d1-q0.01", purple),
            ("model's detector", "learned-s1", orange),
        ]
        picks = [(k, lab) for k, lab in have if k in ("man2", "shift", "man2-corr", "man2-out")]
        fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
        xx = np.arange(len(picks))
        ww = 0.8 / len(who)
        for ax, key, title in (
            (axes[0], "missed_share", "true manoeuvres missed (share)"),
            (axes[1], "false_per_period", "false manoeuvres (per period)"),
        ):
            for j, (name, sysk, col) in enumerate(who):
                v = [test[k]["counts"][sysk]["120"][key] for k, _ in picks]
                ax.bar(xx + (j - (len(who) - 1) / 2) * ww, v, ww, color=col, label=name)
            ax.set_xticks(xx, [lab for _, lab in picks], fontsize=8)
            ax.set_title(title, fontsize=9)
        axes[1].legend(frameon=False, fontsize=8)
        fig.suptitle("Manoeuvres, matched within 120 s (test seed 341)", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "manoeuvres.svg")
        plt.close(fig)
        used["manoeuvres.svg"] = [TEST / "summary.json"]

        # 5. training
        runs = sorted((ROOT / "experiments/20261114-tlm-runs").glob("tlm-s*.run.json"))
        fig, ax = plt.subplots(figsize=(6.6, 3.6))
        for j, p in enumerate(runs):
            r = json.loads(p.read_text())
            u = [v["update"] * 256 / 1e6 for v in r["validation"]]
            e = [v["ln_range_abs_median"] for v in r["validation"]]
            ax.plot(u, e, color=[purple, orange, green][j % 3], lw=1.2, label=f"seed {j + 1}")
        ax.set_xlabel("simulated periods seen (millions)")
        ax.set_ylabel("median |error of ln range| on the monitor slice")
        ax.set_ylim(0.05, 0.3)
        ax.set_title("Training the whole-period model (three seeds, a T4 each)", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "training.svg")
        plt.close(fig)
        used["training.svg"] = [p.relative_to(ROOT) for p in runs]

        # 6. tracks
        z = np.load(ROOT / TEST / "tracks.npz")

        def med(split: str, system: str, period: int) -> float:
            m = z[f"{split}/period"] == period
            tr, st = z[f"{split}/truth"][m].astype(float), z[f"{split}/{system}"][m].astype(float)
            rng = np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])
            est = np.hypot(st[:, 0] - tr[:, 4], st[:, 1] - tr[:, 5])
            return float(np.median(np.abs(est - rng) / rng))

        ids = [int(i) for i in np.unique(z["shift/period"])]
        ratio = {
            i: med("shift", "learned-s1-arc", i) / med("shift", "ctl-d1-q0.01", i) for i in ids
        }
        worst, best = max(ratio, key=lambda i: ratio[i]), min(ratio, key=lambda i: ratio[i])
        per = json.loads((ROOT / TEST / "man2-out.periods.json").read_text())
        stored = {int(i) for i in np.unique(z["man2-out/period"])}
        first = next(r["ordinal"] for r in per if r["ordinal"] in stored and r["true"])
        panels = [
            ("shift", worst, "shifted prior: the learned track at its worst"),
            ("shift", best, "shifted prior: the learned track at its best"),
            ("man2-out", first, "2% outliers"),
        ]
        fig, axes = plt.subplots(1, 3, figsize=(11.4, 4.0))
        shown = [
            ("classical control", "ctl-d1-q0.01", purple, "-"),
            ("learned, arc read-out", "learned-s1-arc", orange, "-"),
            ("learned, own track", "learned-s1", orange, ":"),
        ]
        for ax, (split, pid, title) in zip(axes, panels, strict=True):
            m = z[f"{split}/period"] == pid
            tr = z[f"{split}/truth"][m].astype(float) / 1000.0
            ax.plot(tr[:, 4], tr[:, 5], color="#1f77b4", lw=1.4, label="ownship")
            ax.plot(tr[:, 0], tr[:, 1], color="#d62728", lw=1.6, label="target (truth)")
            ax.plot(tr[0, 0], tr[0, 1], "o", color="#d62728", ms=4)
            for name, key, col, ls in shown:
                st = z[f"{split}/{key}"][m].astype(float) / 1000.0
                ax.plot(st[:, 0], st[:, 1], color=col, ls=ls, lw=1.1, label=name)
            ax.set_aspect("equal", adjustable="datalim")
            ax.set_title(f"{title}\n(period {pid}, {int(m.sum()) // 2} min)", fontsize=8)
            ax.set_xlabel("east (km)")
        axes[0].set_ylabel("north (km)")
        axes[0].legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "tracks.svg")
        plt.close(fig)
        used["tracks.svg"] = [TEST / "tracks.npz", TEST / "man2-out.periods.json"]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl4_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
