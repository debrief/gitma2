"""Spec 012 slides: the scaled regressor's test record in three SVG charts, from committed JSON.

    uv run python scripts/research/r_charts.py --out-dir <dir>

* ``held-course.svg``: efficiency against the bound on held course by geometry quartile
  (`experiments/20261111-r-test/test/held/reading.json`).
* ``after-manoeuvres.svg``: median range error by true-range quartile, regressor against C″,
  on the test seed and on the longer-initial-range split (`test/man2`, `heldout/man2`).
* ``control.svg``: C″, C″ combined with a range prior, and the regressor
  (`experiments/20261112-r-control/test.json`).

Writes ``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
T = Path("experiments/20261111-r-test")
HELD = T / "test/held/reading.json"
MAN2 = T / "test/man2/reading.json"
HMAN2 = T / "heldout/man2/reading.json"
EFF = T / "test/man2/headroom.json"
CTL = Path("experiments/20261112-r-control/test.json")


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

    def js(p: Path) -> dict[str, Any]:
        d: dict[str, Any] = json.loads((ROOT / p).read_text())
        return d

    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]
    quart = ["best", "2nd", "3rd", "worst"]
    with plt.rc_context(STYLE):
        # 1. held course by geometry
        h = js(HELD)["held_course"]
        fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.4), sharey=True)
        for ax, (key, lab) in zip(
            axes, (("range", "range"), ("course_deg", "course"), ("speed_kt", "speed")), strict=True
        ):
            x = np.arange(4)
            ax.bar(x - 0.2, h["oracle"][key]["by_geometry_best_to_worst"], 0.4, color=green)
            ax.bar(x + 0.2, h["reg-s1"][key]["by_geometry_best_to_worst"], 0.4, color=purple)
            ax.axhline(1.0, color="k", lw=0.8, ls="--")
            ax.axhline(1.25, color=grey, lw=0.8, ls=":")
            ax.set_xticks(x, quart, fontsize=8)
            ax.set_title(lab, fontsize=10)
        axes[0].set_ylabel("error ÷ Cramér–Rao bound")
        axes[1].set_xlabel("geometry quartile (how well the bearings fix the target)")
        axes[0].legend(
            handles=[
                plt.Rectangle((0, 0), 1, 1, color=green),
                plt.Rectangle((0, 0), 1, 1, color=purple),
            ],
            labels=["least squares", "regressor, seed 1"],
            frameon=False,
            fontsize=8,
        )
        fig.suptitle(
            "Held course, test seed 328: the regressor is furthest from the bound "
            "where the geometry is best",
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(out / "held-course.svg")
        plt.close(fig)
        used["held-course.svg"] = [HELD]

        # 2. after manoeuvres by range quartile, two splits
        fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4), sharey=True)
        for ax, (p, lab) in zip(
            axes,
            ((MAN2, "test seed 328"), (HMAN2, "longer initial ranges (20–30 km)")),
            strict=True,
        ):
            q = js(p)["after_manoeuvres"]["reg-s1"]["c2"]["range_by_true_range_quartile"]
            x = np.arange(4)
            ax.bar(x - 0.2, [r["b_median"] for r in q], 0.4, color=orange, label="C″")
            ax.bar(x + 0.2, [r["a_median"] for r in q], 0.4, color=purple, label="regressor")
            ax.set_xticks(x, ["nearest", "2nd", "3rd", "farthest"], fontsize=8)
            ax.set_title(lab, fontsize=10)
            ax.set_xlabel("true-range quartile")
        axes[0].set_ylabel("median relative range error")
        axes[0].legend(frameon=False, fontsize=8)
        fig.suptitle(
            "After manoeuvres: the margin grows with range on the test seed "
            "and vanishes at the far end of the other split",
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(out / "after-manoeuvres.svg")
        plt.close(fig)
        used["after-manoeuvres.svg"] = [MAN2, HMAN2]

        # 3. efficiency after manoeuvres and the control
        e = js(EFF)["estimators"]
        c = js(CTL)["result"]["median"]
        fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4))
        x = np.arange(3)
        keys = ["efficiency_settled_range", "efficiency_settled_course", "efficiency_settled_speed"]
        for i, (name, lab, col) in enumerate(
            (
                ("oracle", "true-manoeuvre solve", green),
                ("c2", "C″", orange),
                ("reg-s1", "regressor", purple),
            )
        ):
            axes[0].bar(x + (i - 1) * 0.27, [e[name][k] for k in keys], 0.27, color=col, label=lab)
        axes[0].axhline(1.0, color="k", lw=0.8, ls="--")
        axes[0].set_xticks(x, ["range", "course", "speed"])
        axes[0].set_ylabel("error ÷ bound, settled rows")
        axes[0].set_title("Efficiency after manoeuvres", fontsize=10)
        axes[0].legend(frameon=False, fontsize=8)
        rows = [
            ("C″", c["c2"], orange),
            ("C″ + static\nrange prior", c["c2_plus_static_prior"], grey),
            ("C″ + ownship-\nonly prior", c["c2_plus_own_prior"], grey),
            ("regressor", c["regressor_s1"], purple),
        ]
        xs = np.arange(len(rows))
        axes[1].bar(xs, [r[1] for r in rows], 0.6, color=[r[2] for r in rows])
        for xi, r in zip(xs, rows, strict=True):
            axes[1].text(xi, r[1] + 0.002, f"{r[1]:.3f}", ha="center", fontsize=8)
        axes[1].set_xticks(xs, [r[0] for r in rows], fontsize=8)
        axes[1].set_ylabel("median relative range error")
        axes[1].set_title("The range-prior control (registered on validation)", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "control.svg")
        plt.close(fig)
        used["control.svg"] = [EFF, CTL]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/r_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
