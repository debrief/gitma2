"""Spec 018 slides: SVG figures from one committed record.

    uv run python scripts/research/tl6_charts.py --record experiments/20261115-tl6 --out-dir <dir>

* ``verdict.svg``: control ÷ the adaptive control (declared, hedged) and ÷ the search told
  the true statistics, in range, on every split, with 95% intervals and period counts.
* ``quantities.svg``: the same two systems in range, course and speed on Annex B and
  shifted targets.
* ``kinds.svg``: on shifted targets, the comparison where the standing control misses a
  manoeuvre the bearings show and where it does not.
* ``groups.svg``: members chosen per period and by groups of 5, 20 and all periods.
* ``spread.svg``: the share of rows within two stated sds of the hedged track's range, by
  split, against the registered band.
* ``tracks.svg`` (only when ``<record>/tracks.npz`` exists): two stored shifted periods,
  chosen by a rule, not by eye: of the stored periods, the one where the hedged adaptive
  track is best against the control (ratio of median range error over stored rows) and the
  one where it is worst.

Reads ``summary.json``, ``run.json`` and ``tracks.npz`` of the record; writes
``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPLITS = [
    ("man2", "Annex B"),
    ("shift", "shifted"),
    ("shift2", "shifted 2"),
    ("quiet", "held\ncourse"),
    ("man2-out", "outliers"),
    ("man2-corr", "correlated"),
]
CONTROL, ADA, HEDGE, TRUE = "ctl-d1-q0.01", "ada-d1-q0.01", "ada-h1", "true"


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
    from tma2.report.plots import ESTIMATORS, STYLE

    g = read_git_provenance()  # before writing anything
    rec = Path(a.record)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    used: dict[str, list[Path]] = {}
    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]
    summary = json.loads((ROOT / rec / "summary.json").read_text())
    sp: dict[str, Any] = summary["splits"]
    seed = json.loads((ROOT / rec / "run.json").read_text())["seed"]
    have = [(k, lab) for k, lab in SPLITS if k in sp]

    def point(ax: Any, x: float, v: dict[str, Any] | None, col: str, label: str | None) -> None:
        if not v:
            return
        lo = max(v["geometric_mean"] - v["lo"], 0.0)
        hi = max(v["hi"] - v["geometric_mean"], 0.0)
        ax.errorbar(
            x,
            v["geometric_mean"],
            yerr=[[lo], [hi]],
            fmt="o",
            color=col,
            ms=4,
            capsize=2,
            label=label,
        )
        ax.plot(x, v["median_ratio"], marker="_", color="0.35", ms=9, mew=1.5)

    def cmp(split: str, b: str, q: str = "range") -> dict[str, Any] | None:
        return (sp[split]["comparisons3"].get(f"{CONTROL}_over_{b}") or {}).get(q)

    systems = [("adaptive, declared", ADA, purple), ("adaptive, hedged", HEDGE, orange)]
    with plt.rc_context(STYLE):
        # 1. the registered comparison on every split
        fig, ax = plt.subplots(figsize=(8.8, 4.0))
        every = [*systems, ("told the true statistics", TRUE, green)]
        for i, (k, _lab) in enumerate(have):
            for j, (name, key, col) in enumerate(every):
                point(ax, i + (j - 1) * 0.22, cmp(k, key), col, name if i == 0 else None)
        ax.plot(
            [], [], marker="_", color="0.35", ls="", ms=9, mew=1.5, label="median per-period ratio"
        )
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        labels = []
        for k, lab in have:
            v = cmp(k, ADA)
            labels.append(f"{lab}\n({v['periods'] if v else 0})")
        ax.set_xticks(range(len(have)), labels, fontsize=8)
        ax.set_ylabel("standing control ÷ system, range\n(above 1: the system is better)")
        ax.set_title(
            f"Against the standing control (seed {seed}; periods in brackets)", fontsize=10
        )
        ax.legend(frameon=False, fontsize=7, ncol=2)
        fig.tight_layout()
        fig.savefig(out / "verdict.svg")
        plt.close(fig)
        used["verdict.svg"] = [rec / "summary.json"]

        # 2. three quantities on the two main splits
        fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
        for ax, (k, lab) in zip(
            axes, [("man2", "Annex B targets"), ("shift", "shifted targets")], strict=True
        ):
            for i, q in enumerate(("range", "course", "speed")):
                for j, (name, key, col) in enumerate(systems):
                    point(ax, i + (j - 0.5) * 0.25, cmp(k, key, q), col, name if i == 0 else None)
            ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
            ax.set_xticks(range(3), ["range", "course", "speed"])
            ax.set_title(lab, fontsize=9)
        axes[0].set_ylabel("standing control ÷ system")
        axes[0].legend(frameon=False, fontsize=7)
        fig.suptitle(f"Range, course and speed (seed {seed})", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "quantities.svg")
        plt.close(fig)
        used["quantities.svg"] = [rec / "summary.json"]

        # 3. by kind of period, shifted
        kinds = [
            ("control_misses", "the control misses\na manoeuvre the\nbearings show"),
            ("control_finds_all", "the control\nmisses none"),
            ("bound_tight", "bound:\ntight third"),
            ("bound_middle", "bound:\nmiddle third"),
            ("bound_loose", "bound:\nloose third"),
        ]
        bk = sp["shift"]["by_kind"]
        fig, ax = plt.subplots(figsize=(8.4, 3.9))
        ticks = []
        for i, (kind, lab) in enumerate(kinds):
            n = 0
            for j, (name, key, col) in enumerate(every):
                v = ((bk.get(f"{CONTROL}_over_{key}") or {}).get(kind) or {}).get("range")
                point(ax, i + (j - 1) * 0.22, v, col, name if i == 0 else None)
                n = v["periods"] if v else n
            ticks.append(f"{lab}\n({n})")
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        ax.set_xticks(range(len(kinds)), ticks, fontsize=7)
        ax.set_ylabel("standing control ÷ system, range")
        ax.set_title(f"Shifted targets, by kind of period (seed {seed})", fontsize=10)
        ax.legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "kinds.svg")
        plt.close(fig)
        used["kinds.svg"] = [rec / "summary.json"]

        # 4. choosing the member by groups of periods
        fig, ax = plt.subplots(figsize=(7.6, 3.7))
        sizes = [
            ("one period", ADA, None),
            ("groups of 5", "ada-pool5", "pooled"),
            ("groups of 20", "ada-pool20", "pooled"),
            ("the whole split", "ada-pool1000", "pooled"),
        ]
        cols = {"man2": grey, "shift": purple, "shift2": orange, "quiet": green}
        for j, (k, lab) in enumerate([x for x in have if x[0] in cols]):
            for i, (_name, key, where) in enumerate(sizes):
                if where:
                    v = (
                        (sp[k].get("pooled_comparisons") or {}).get(f"{CONTROL}_over_{key}") or {}
                    ).get("range")
                else:
                    v = cmp(k, key)
                point(
                    ax, i + (j - 1.5) * 0.17, v, cols[k], lab.replace("\n", " ") if i == 0 else None
                )
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        ax.set_xticks(range(len(sizes)), [s[0] for s in sizes], fontsize=8)
        ax.set_xlabel("who chooses the prior")
        ax.set_ylabel("standing control ÷ adaptive, range")
        ax.set_title(f"Choosing the prior together adds nothing (seed {seed})", fontsize=10)
        ax.legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "groups.svg")
        plt.close(fig)
        used["groups.svg"] = [rec / "summary.json"]

        # 5. the stated spread
        fig, ax = plt.subplots(figsize=(7.6, 3.6))
        xs, two, one = [], [], []
        for i, (k, _lab) in enumerate(have):
            c = (sp[k].get("coverage") or {}).get("all")
            if c:
                xs.append(i)
                two.append(c["within_2sd"])
                one.append(c["within_1sd"])
        ax.axhspan(0.90, 0.99, color=green, alpha=0.12, label="registered band (two sds)")
        ax.bar([x - 0.18 for x in xs], one, 0.34, color="#d9c9ea", label="within one stated sd")
        ax.bar([x + 0.18 for x in xs], two, 0.34, color=purple, label="within two stated sds")
        ax.set_xticks(range(len(have)), [lab for _, lab in have], fontsize=8)
        ax.set_ylim(0, 1.3)
        ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_ylabel("share of rows")
        ax.set_title(f"The hedged track's stated spread in range (seed {seed})", fontsize=10)
        ax.legend(frameon=False, fontsize=7, loc="upper left", ncol=3)
        fig.tight_layout()
        fig.savefig(out / "spread.svg")
        plt.close(fig)
        used["spread.svg"] = [rec / "summary.json"]

        # 6. two stored periods
        tracks = ROOT / rec / "tracks.npz"
        if tracks.exists():
            z = np.load(tracks)

            def med(key: str, pid: int) -> float:
                m = z["shift/period"] == pid
                tr = z["shift/truth"][m].astype(float)
                st = z[f"shift/{key}"][m].astype(float)
                rng = np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])
                est = np.hypot(st[:, 0] - tr[:, 4], st[:, 1] - tr[:, 5])
                return float(np.nanmedian(np.abs(est - rng) / rng))

            ids = [int(i) for i in np.unique(z["shift/period"])]
            ratio = {i: med(CONTROL, i) / med(HEDGE, i) for i in ids}
            ratio = {i: r for i, r in ratio.items() if np.isfinite(r) and r > 0}
            best = max(ratio, key=lambda i: (ratio[i], -i))
            worst = min(ratio, key=lambda i: (ratio[i], i))
            shown = [
                ("standing control", CONTROL, grey, "-"),
                ("adaptive, declared", ADA, purple, "-"),
                ("adaptive, hedged", HEDGE, orange, "--"),
            ]
            fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
            for ax, pid, tag in zip(axes, (best, worst), ("best", "worst"), strict=True):
                m = z["shift/period"] == pid
                tr = z["shift/truth"][m].astype(float) / 1000.0
                ax.plot(tr[:, 4], tr[:, 5], color="#1f77b4", lw=1.4, label="ownship")
                ax.plot(tr[:, 0], tr[:, 1], color="#d62728", lw=1.6, label="target (truth)")
                ax.plot(tr[0, 0], tr[0, 1], "o", color="#d62728", ms=4)
                for name, key, col, ls in shown:
                    st = z[f"shift/{key}"][m].astype(float) / 1000.0
                    ax.plot(st[:, 0], st[:, 1], color=col, ls=ls, lw=1.1, label=name)
                ax.set_aspect("equal", adjustable="datalim")
                ax.set_title(
                    f"the hedged track at its {tag}: period {pid}\n"
                    f"control ÷ hedged {ratio[pid]:.2f}",
                    fontsize=8,
                )
                ax.set_xlabel("east (km)")
            axes[0].set_ylabel("north (km)")
            axes[0].legend(frameon=False, fontsize=7)
            fig.tight_layout()
            fig.savefig(out / "tracks.svg")
            plt.close(fig)
            used["tracks.svg"] = [rec / "tracks.npz"]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl6_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
