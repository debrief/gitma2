"""Spec 038 slides: the test record in three SVG charts, from committed JSON only.

    uv run python scripts/research/gd_charts.py --out-dir site/static/img/2026-11-28-gain-decomposition

* ``systems.svg``: C″-robust ÷ each system in range, in distribution, clean and primary.
* ``gap-closed.svg``: the share of the gap to the regressor each classical control closes.
* ``lead-by-split.svg``: C″-robust ÷ fine-tuned regressor on the three splits.

Inputs: ``experiments/20261128-gd/runs/<split>/<condition>/decomp.json``. Writes
``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REC = Path("experiments/20261128-gd")


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
    paths = sorted((ROOT / REC).glob("runs/*/*/decomp.json"))
    runs: dict[tuple[str, str], dict[str, Any]] = {
        (p.parts[-3], p.parts[-2]): json.loads(p.read_text()) for p in paths
    }
    inputs = [p.relative_to(ROOT) for p in paths]
    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]

    def side(name: str, note: str) -> None:
        (out / f"{name}.svg.json").write_text(
            json.dumps(
                {
                    "figure": f"{name}.svg",
                    "script": "scripts/research/gd_charts.py",
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

    def bars(ax: Any, rows: list[tuple[str, dict[str, Any] | None, Any]], key: str) -> None:
        y = np.arange(len(rows))[::-1]
        for yi, (_label, r, colour) in zip(y, rows, strict=True):
            if not r or key not in r:
                continue
            ax.barh(yi, r[key], color=colour, height=0.6)
            ax.plot([r["lo"], r["hi"]], [yi, yi], color="black", lw=1.2)
        ax.set_yticks(y, [label for label, _, _ in rows])

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
        names = [
            ("fine-tuned regressor", "fine_tuned", green),
            ("solve told the true\nmanoeuvre times", "true", purple),
            ("C, edited bearings\n+ threshold × 4", "c2-edit-thr", orange),
            ("C, edited bearings", "c2-edit", orange),
            ("C, threshold × 4", "c2-thr", orange),
            ("ownship-only prior\ninside C″'s solve", "own_hybrid", grey),
            ("ownship-only\nregressor alone", "own", grey),
        ]
        for ax, cond, title in zip(
            axes, ("off", "all-central"), ("clean bearings", "primary mismatch"), strict=True
        ):
            r = runs[("in", cond)]["all"]["ratios"]["range"]
            bars(ax, [(label, r.get(key), c) for label, key, c in names], "ratio")
            ax.axvline(1.0, color="black", lw=0.8)
            ax.set_title(title)
            ax.set_xlabel("C″-robust ÷ system, range error (above 1: better than C″)")
        fig.tight_layout()
        fig.savefig(out / "systems.svg")
        plt.close(fig)
        side("systems", "Paired per engagement, 500 engagements of seed 372, 95% intervals.")

        fig, ax = plt.subplots(figsize=(8, 3.6))
        ctl = [
            ("edited bearings + threshold × 4", "c2-edit-thr"),
            ("edited bearings", "c2-edit"),
            ("threshold × 4", "c2-thr"),
        ]
        conds = [
            (("in", "all-central"), "in distribution, primary"),
            (("in", "ho-both"), "in distribution, outside the mix"),
            (("shift", "all-central"), "busier targets, primary"),
            (("far", "all-central"), "far ranges, primary"),
        ]
        w = 0.25
        for i, (label, key) in enumerate(ctl):
            xs, vals, lo, hi = [], [], [], []
            for j, (rk, _) in enumerate(conds):
                s = runs[rk]["all"]["gap_closed"]["range"].get(key, {})
                if s.get("defined"):
                    xs.append(j + (i - 1) * w)
                    vals.append(s["share"])
                    lo.append(s["share"] - s["lo"])
                    hi.append(s["hi"] - s["share"])
            ax.bar(xs, vals, w, yerr=[lo, hi], label=label, color=ESTIMATORS[i + 1], capsize=2)
        ax.axhline(0.5, color="black", lw=0.8, ls="--")
        ax.axhline(0.2, color="black", lw=0.8, ls=":")
        ax.axhline(0.0, color="black", lw=0.8)
        ax.set_xticks(range(len(conds)), [c for _, c in conds], fontsize=8)
        ax.set_ylabel("share of the log gap to the regressor closed")
        ax.legend(fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
        fig.tight_layout()
        fig.savefig(out / "gap-closed.svg")
        plt.close(fig)
        side("gap-closed", "Dashed: the registered 'most' line (0.5); dotted: 'little' (0.2).")

        fig, ax = plt.subplots(figsize=(7, 3.6))
        splits = [("in", "in distribution"), ("shift", "busier targets"), ("far", "far ranges")]
        for i, (cond, label, colour) in enumerate(
            (("off", "clean", grey), ("all-central", "primary mismatch", green))
        ):
            rs = [runs[(s, cond)]["all"]["ratios"]["range"]["fine_tuned"] for s, _ in splits]
            x = np.arange(len(splits)) + (i - 0.5) * 0.35
            ax.bar(
                x,
                [r["ratio"] for r in rs],
                0.35,
                yerr=[[r["ratio"] - r["lo"] for r in rs], [r["hi"] - r["ratio"] for r in rs]],
                label=label,
                color=colour,
                capsize=2,
            )
        ax.axhline(1.0, color="black", lw=0.8)
        ax.set_xticks(range(len(splits)), [s for _, s in splits])
        ax.set_ylabel("C″-robust ÷ fine-tuned regressor, range")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "lead-by-split.svg")
        plt.close(fig)
        side("lead-by-split", "The regressor's lead over C″-robust on each split, 95% intervals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
