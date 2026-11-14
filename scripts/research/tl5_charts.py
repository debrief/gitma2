"""Spec 017 slides: five SVG figures from one committed record.

    uv run python scripts/research/tl5_charts.py --record experiments/20261114-tl5 --out-dir <dir>

* ``detectable.svg``: the share of whole true manoeuvres whose omission adds less than 10,
  20 and 40 to the χ² of the true history's fit, by split.
* ``missed.svg``: the share of the shifted split's true manoeuvres each system misses, by
  detectability band.
* ``chain.svg``: the shifted-prior gap as a chain of paired ratios: control ÷ full
  reference, reference told only the detectable manoeuvres ÷ full reference, control ÷
  that reference, control ÷ the search under the true prior.
* ``share.svg``: the attainable share of the control's gap at each threshold, by split.
* ``tracks.svg`` (only when ``<record>/tracks.npz`` exists): two stored shifted periods as
  track plots, chosen by a rule, not by eye: among the stored periods with at least two
  whole true manoeuvres, the one with the largest share under 20 and the one with the
  smallest (ties: the lower ordinal).

Reads ``summary.json``, ``shift.periods.json`` and ``tracks.npz`` of the record; writes
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
    ("shift", "shifted prior"),
    ("shift2", "shifted prior 2"),
    ("man2-out", "outliers 2%"),
]
CONTROL = "ctl-d1-q0.01"
THRESHOLDS = ("10", "20", "40")


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
    have = [(k, lab) for k, lab in SPLITS if k in sp and sp[k]["detectability"].get("manoeuvres")]
    what = (ROOT / rec / "run.json").read_text()
    seed = json.loads(what)["seed"]

    def err(v: dict[str, float], key: str) -> list[list[float]]:
        return [[max(v[key] - v["lo"], 0.0)], [max(v["hi"] - v[key], 0.0)]]

    with plt.rc_context(STYLE):
        # 1. how much of the manoeuvring can be seen
        fig, ax = plt.subplots(figsize=(7.6, 3.8))
        w = 0.8 / len(THRESHOLDS)
        shades = ["#d9c9ea", "#b9a3d0", purple]
        for j, t in enumerate(THRESHOLDS):
            for i, (k, _lab) in enumerate(have):
                v = sp[k]["detectability"]["share_below"][t]
                ax.bar(
                    i + (j - 1) * w,
                    v["rate"],
                    w * 0.92,
                    color=shades[j],
                    yerr=err(v, "rate"),
                    capsize=2,
                    error_kw={"lw": 0.8},
                    label=f"under {t}" if i == 0 else None,
                )
        ax.set_xticks(
            range(len(have)),
            [f"{lab}\n({sp[k]['detectability']['manoeuvres']} manoeuvres)" for k, lab in have],
            fontsize=8,
        )
        ax.set_ylabel("share of whole true manoeuvres")
        ax.set_title(
            f"Manoeuvres whose omission adds little to the fit's χ² (seed {seed})", fontsize=10
        )
        ax.legend(frameon=False, fontsize=8, title="detectability", title_fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "detectable.svg")
        plt.close(fig)
        used["detectable.svg"] = [rec / "summary.json"]

        # 2. who misses what
        bands = sp["shift"]["detectability"]["missed_by_band"]
        systems = [
            ("C″ as a track", "c2", grey),
            ("standing search", "search3", "#b9a3d0"),
            ("classical control", CONTROL, purple),
            ("search, true prior", "true", green),
        ]
        systems = [s for s in systems if s[1] in next(iter(bands.values()))]
        fig, ax = plt.subplots(figsize=(7.6, 3.8))
        x = np.arange(len(bands))
        for name, key, col in systems:
            y = [row[key]["rate"] for row in bands.values()]
            lo = [max(row[key]["rate"] - row[key]["lo"], 0.0) for row in bands.values()]
            hi = [max(row[key]["hi"] - row[key]["rate"], 0.0) for row in bands.values()]
            ax.errorbar(x, y, yerr=[lo, hi], marker="o", ms=4, lw=1.2, capsize=2, color=col)
            ax.plot([], [], marker="o", ms=4, color=col, label=name)
        ax.set_xticks(x, [f"{b}\n({row['n']})" for b, row in bands.items()], fontsize=8)
        ax.set_xlabel("detectability of the manoeuvre (χ² its omission adds; count)")
        ax.set_ylabel("share missed (matched within 120 s)")
        ax.set_ylim(0, 1.05)
        ax.set_title(
            f"Shifted prior: manoeuvres missed, by detectability (seed {seed})", fontsize=10
        )
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "missed.svg")
        plt.close(fig)
        used["missed.svg"] = [rec / "summary.json"]

        # 3. the gap as a chain
        c = sp["shift"]["comparisons"]
        links = [
            ("control ÷\nreference told\nevery manoeuvre", f"{CONTROL}_over_ref-full", purple),
            ("told only those\nabove 20 ÷\ntold every one", "ref-d20_over_ref-full", grey),
            ("control ÷\ntold only those\nabove 20", f"{CONTROL}_over_ref-d20", orange),
            ("control ÷\nsearch under the\ntrue prior", f"{CONTROL}_over_true", green),
        ]
        links = [x for x in links if x[1] in c]
        fig, ax = plt.subplots(figsize=(7.6, 3.9))
        for i, (_lab, key, col) in enumerate(links):
            v = c[key]
            ax.errorbar(i, v["geometric_mean"], yerr=err(v, "geometric_mean"), fmt="o", color=col)
            ax.plot(i, v["median_ratio"], marker="_", color="0.3", ms=12, mew=2)
            ax.text(i + 0.08, v["geometric_mean"], f"{v['geometric_mean']:.2f}", fontsize=8)
        ax.plot(
            [], [], marker="_", color="0.3", ls="", ms=10, mew=2, label="median per-period ratio"
        )
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        ax.set_xticks(range(len(links)), [lab for lab, _, _ in links], fontsize=8)
        ax.set_xlim(-0.5, len(links) - 0.4)
        ax.set_ylabel("paired ratio of period range error")
        ax.set_title(f"Shifted prior: where the gap sits (seed {seed})", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "chain.svg")
        plt.close(fig)
        used["chain.svg"] = [rec / "summary.json"]

        # 4. the attainable share by threshold
        fig, ax = plt.subplots(figsize=(7.6, 3.8))
        cols = [grey, purple, orange, green]
        for i, (k, lab) in enumerate(have):
            gs = sp[k]["gap_split"].get(CONTROL)
            if not gs:
                continue
            xs = np.arange(len(THRESHOLDS)) + (i - (len(have) - 1) / 2) * 0.12
            y = [gs[t]["share"] for t in THRESHOLDS]
            lo = [max(gs[t]["share"] - gs[t]["lo"], 0.0) for t in THRESHOLDS]
            hi = [max(gs[t]["hi"] - gs[t]["share"], 0.0) for t in THRESHOLDS]
            ax.errorbar(
                xs, y, yerr=[lo, hi], marker="o", ms=4, lw=1.0, capsize=2, color=cols[i], label=lab
            )
        ax.axhline(0.5, color="0.5", lw=0.8, ls="--")
        ax.axhline(0.0, color="0.7", lw=0.6)
        ax.set_xticks(range(len(THRESHOLDS)), [f"threshold {t}" for t in THRESHOLDS])
        ax.set_ylim(-1.0, 1.3)
        ax.set_ylabel("attainable share of the control's gap")
        ax.set_title(f"The split depends on where 'detectable' is drawn (seed {seed})", fontsize=10)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "share.svg")
        plt.close(fig)
        used["share.svg"] = [rec / "summary.json"]

        # 5. two stored periods
        tracks = ROOT / rec / "tracks.npz"
        if tracks.exists():
            z = np.load(tracks)
            per = {
                r["ordinal"]: r for r in json.loads((ROOT / rec / "shift.periods.json").read_text())
            }
            stored = sorted(int(i) for i in np.unique(z["shift/period"]))

            def low_share(i: int) -> float | None:
                r = per[i]
                d = [x for x, cut in zip(r["detectability"], r["true_cut"], strict=True) if not cut]
                return None if len(d) < 2 else sum(x < 20.0 for x in d) / len(d)

            shares = {i: s for i in stored if (s := low_share(i)) is not None}
            hard = max(shares, key=lambda i: (shares[i], -i))
            easy = min(shares, key=lambda i: (shares[i], i))
            shown = [
                ("classical control", CONTROL, purple, "-"),
                ("true-history reference", "history-best", green, "--"),
            ]
            fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
            for ax, pid, tag in zip(axes, (hard, easy), ("most", "fewest"), strict=True):
                m = z["shift/period"] == pid
                tr = z["shift/truth"][m].astype(float) / 1000.0
                ax.plot(tr[:, 4], tr[:, 5], color="#1f77b4", lw=1.4, label="ownship")
                ax.plot(tr[:, 0], tr[:, 1], color="#d62728", lw=1.6, label="target (truth)")
                ax.plot(tr[0, 0], tr[0, 1], "o", color="#d62728", ms=4)
                for name, key, col, ls in shown:
                    st = z[f"shift/{key}"][m].astype(float) / 1000.0
                    ax.plot(st[:, 0], st[:, 1], color=col, ls=ls, lw=1.1, label=name)
                d = per[pid]["detectability"]
                ax.set_aspect("equal", adjustable="datalim")
                ax.set_title(
                    f"{tag} manoeuvres under 20: period {pid}\n"
                    f"detectabilities {', '.join(f'{x:.0f}' for x in d)}",
                    fontsize=8,
                )
                ax.set_xlabel("east (km)")
            axes[0].set_ylabel("north (km)")
            axes[0].legend(frameon=False, fontsize=7)
            fig.tight_layout()
            fig.savefig(out / "tracks.svg")
            plt.close(fig)
            used["tracks.svg"] = [rec / "tracks.npz", rec / "shift.periods.json"]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl5_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
