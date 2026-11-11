"""Spec 011 slides: the robust-segmenter study in three SVG charts, from committed records.

    uv run python scripts/research/gr_charts.py --out-dir <dir>

* ``diagnosis.svg``: the frozen C's unmatched (false) transitions and misses under each mismatch
  kind, tuning seed 323 (`experiments/20261110-gr-diagnosis/transitions.json`).
* ``yield.svg``: median range error of the reference, the baseline and C″'s clean-data
  segmentation applied to the mismatched bearings (`.../yield/summary.json`).
* ``choice.svg``: every confirmation test on 150 engagements: share of the gap closed with its
  95% interval, and false transitions against misses
  (`experiments/20261111-gr-choice/summary.json`, `transitions.json`).

Writes ``<fig>.svg.json`` beside each figure naming the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DIAG = Path("experiments/20261110-gr-diagnosis")
CHOICE = Path("experiments/20261111-gr-choice")
KINDS = [
    ("off", "none"),
    ("bias-central", "bias"),
    ("sigma-central", "untold σ"),
    ("corr-central", "correlated"),
    ("out-central", "outliers"),
    ("all-central", "all four"),
]
VARIANTS = [
    ("robust@c2", "C″ as frozen"),
    ("cr-k2", "Huber 2.0"),
    ("cr-k1.345", "Huber 1.345"),
    ("c-tau2", "threshold × 2"),
    ("c-tau3", "threshold × 3"),
    ("cr-k2-tau2", "Huber 2.0, × 2"),
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

    def js(p: Path) -> dict[str, Any]:
        d: dict[str, Any] = json.loads((ROOT / p).read_text())
        return d

    blue, red, green, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]
    with plt.rc_context(STYLE):
        # 1. diagnosis
        tr = js(DIAG / "transitions.json")
        x = np.arange(len(KINDS))
        fig, ax = plt.subplots(figsize=(8.0, 3.8))
        ax.bar(
            x - 0.2,
            [tr[c]["C"]["false"] for c, _ in KINDS],
            0.4,
            color=red,
            label="false transitions",
        )
        ax.bar(
            x + 0.2,
            [tr[c]["C"]["missed"] for c, _ in KINDS],
            0.4,
            color=grey,
            label="missed changes",
        )
        ax.set_xticks(x, [lab for _, lab in KINDS])
        ax.set_ylabel("count over 593 scored prefixes")
        ax.set_xlabel("bearing-error mismatch (central severity)")
        ax.set_title(
            "What breaks the frozen segmenter C (tuning seed 323, 1,223 true changes)", fontsize=10
        )
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(out / "diagnosis.svg")
        plt.close(fig)
        used["diagnosis.svg"] = [DIAG / "transitions.json"]

        # 2. the most a segmenter can yield
        y = js(DIAG / "yield" / "summary.json")
        rows = [
            (
                "true manoeuvre times\n(reference)",
                y["off"]["robust@truth"],
                y["all-central"]["robust@truth"],
                green,
            ),
            (
                "C″ clean-data segmentation\napplied to the mismatch",
                None,
                y["all-central"]["robust@c2<off"],
                blue,
            ),
            (
                "C″ on the bearings\nit is given (baseline)",
                y["off"]["robust@c2"],
                y["all-central"]["robust@c2"],
                red,
            ),
        ]
        fig, ax = plt.subplots(figsize=(8.0, 3.6))
        for i, (_lab, clean, mm, col) in enumerate(rows):
            if clean is not None:
                ax.barh(i + 0.2, clean, 0.38, color=col, alpha=0.45)
                ax.text(clean + 0.004, i + 0.2, f"{clean:.3f} clean", va="center", fontsize=8)
            ax.barh(i - 0.2, mm, 0.38, color=col)
            ax.text(mm + 0.004, i - 0.2, f"{mm:.3f} all four", va="center", fontsize=8)
        ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=8)
        ax.set_xlim(0, 0.32)
        ax.set_xlabel("median relative range error (robust final solve, 593 rows)")
        ax.set_title("The most a better segmenter could yield (tuning seed 323)", fontsize=10)
        fig.tight_layout()
        fig.savefig(out / "yield.svg")
        plt.close(fig)
        used["yield.svg"] = [DIAG / "yield" / "summary.json"]

        # 3. the settings choice
        s = js(CHOICE / "summary.json")["primary"]
        t = js(CHOICE / "transitions.json")["all-central"]
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.0, 3.9))
        names = [n for n, _ in VARIANTS[1:]]
        sh = [s[n]["share"] for n in names]
        yy = np.arange(len(names))
        a1.errorbar(
            [v[0] for v in sh], yy, xerr=[[v[0] - v[1] for v in sh], [v[2] - v[0] for v in sh]],
            fmt="o", color=blue, capsize=3,
        )  # fmt: skip
        a1.axvline(0.0, color="#888888", lw=0.8)
        a1.axvline(0.63, color=green, lw=0.8, ls="--")
        a1.text(
            0.63,
            len(names) - 0.45,
            "clean-data\nsegmentation",
            fontsize=7,
            ha="center",
            color=green,
        )
        a1.set_yticks(yy, [lab for _, lab in VARIANTS[1:]], fontsize=8)
        a1.set_ylim(-0.6, len(names) - 0.1)
        a1.set_xlabel("share of the baseline-to-reference gap closed (95%)")
        a1.set_title("Downstream: nothing separates the variants", fontsize=10)
        for n, lab in VARIANTS:
            a2.scatter(t[n]["false"], t[n]["missed"], color=red if n == "robust@c2" else blue, s=28)
            a2.annotate(
                lab,
                (t[n]["false"], t[n]["missed"]),
                textcoords="offset points",
                xytext=(5, 4),
                fontsize=7,
            )
        a2.set_xlabel("false transitions")
        a2.set_ylabel("missed changes")
        a2.set_title("Segmentation: fewer false transitions, more misses", fontsize=10)
        fig.suptitle(
            "Confirmation tests under the primary mismatch (150 engagements, tuning seed 323)",
            fontsize=10,
        )
        fig.tight_layout()
        fig.savefig(out / "choice.svg")
        plt.close(fig)
        used["choice.svg"] = [CHOICE / "summary.json", CHOICE / "transitions.json"]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/gr_charts.py",
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
            "code_git_commit": g.commit,
            "code_git_dirty": g.dirty,
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
