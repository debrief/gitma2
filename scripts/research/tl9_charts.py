"""Spec 026 slides: SVG figures from the committed test record.

    uv run python scripts/research/tl9_charts.py --record experiments/20261119-tl9 --out-dir <dir>

* ``verdict.svg``: carry ÷ joint and alone ÷ carry in range on every split, with 95%
  engagement intervals (periods after an engagement's first).
* ``kinds.svg``: alone ÷ carry for periods with and without an ownship turn of their own.
* ``ties.svg``: per split, the share of later periods where the carry ends at ``ctl`` alone's
  answer (|log ratio| < 0.01), is better, or is worse.

Reads ``summary.json`` and ``<split>.errors.npz``; writes ``<fig>.svg.json`` sidecars with the
inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SPLITS = [
    ("man2", "Annex B"),
    ("shift", "busier"),
    ("man2-out", "wild\nbearings"),
    ("quiet", "held\ncourse"),
]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


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
    from tma2.timelate.study8 import UNDETERMINED, period_table

    g = read_git_provenance()
    rec, out = Path(a.record), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sp = json.loads((rec / "summary.json").read_text())["splits"]
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})

    def save(fig: Any, name: str, inputs: list[Path]) -> None:
        fig.savefig(out / name, format="svg", bbox_inches="tight", metadata={"Date": None})
        plt.close(fig)
        side = {
            "figure": name,
            "script": "scripts/research/tl9_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): _sha(p) for p in inputs},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")

    def bars(ax: Any, rows: list[tuple[str, list[dict[str, Any]]]], ylabel: str) -> None:
        x = np.arange(len(SPLITS))
        w = 0.8 / len(rows)
        colours = ["#1c7ed6", "#e8590c"]
        for k, (lab, ds) in enumerate(rows):
            xs = x - 0.4 + w * (k + 0.5)
            v = np.array([d["value"] for d in ds])
            lo = np.array([d["lo"] for d in ds])
            hi = np.array([d["hi"] for d in ds])
            ax.bar(xs, v, w * 0.9, color=colours[k], label=lab)
            ax.errorbar(xs, v, yerr=[v - lo, hi - v], fmt="none", ecolor="black", capsize=3, lw=1)
            for xi, d in zip(xs, ds, strict=True):
                ax.text(xi, 0.55, f"n {d['periods']}", ha="center", fontsize=7, rotation=90)
        ax.axhline(1, color="black", lw=0.8)
        ax.set_yscale("log")
        ax.set_ylim(0.5, 25)
        ax.set_xticks(x, [lab for _s, lab in SPLITS])
        ax.set_ylabel(ylabel)
        ax.legend(frameon=False, fontsize=8, loc="upper left")

    fig, ax = plt.subplots(figsize=(7, 4))
    bars(
        ax,
        [
            (
                "carry ÷ joint (above 1: joining better)",
                [sp[s]["carry"]["ratios"]["carry/joint"]["range"] for s, _ in SPLITS],
            ),
            (
                "alone ÷ carry (above 1: carrying helps)",
                [sp[s]["carry"]["ratios"]["alone/carry"]["range"] for s, _ in SPLITS],
            ),
        ],
        "ratio of period median range error",
    )
    save(fig, "verdict.svg", [rec / "summary.json"])

    fig, ax = plt.subplots(figsize=(7, 4))
    bars(
        ax,
        [
            (
                "no ownship turn of its own",
                [
                    sp[s]["carry"]["by_kind"]["no_own_turn"]["alone/carry"]["range"]
                    for s, _ in SPLITS
                ],
            ),
            (
                "with its own ownship turn",
                [sp[s]["carry"]["by_kind"]["own_turn"]["alone/carry"]["range"] for s, _ in SPLITS],
            ),
        ],
        "alone ÷ carry (range)",
    )
    ax.set_ylim(0.5, 4)
    save(fig, "kinds.svg", [rec / "summary.json"])

    shares = []
    inputs = []
    for s, _lab in SPLITS:
        f = rec / f"{s}.errors.npz"
        inputs.append(f)
        z = dict(np.load(f))
        rows = (
            np.isfinite(z["bound_span"][:, 0])
            & (z["bound_span"][:, 0] < UNDETERMINED)
            & ~z["carry_first"]
        )
        t = period_table(z, rows, ["alone", "carry"])
        lr = np.log(t["alone"][:, 0] / t["carry"][:, 0])
        lr = lr[np.isfinite(lr)]
        tie = np.abs(lr) < 0.01
        shares.append((np.mean(tie), np.mean(~tie & (lr > 0)), np.mean(~tie & (lr < 0))))
    fig, ax = plt.subplots(figsize=(7, 3))
    left = np.zeros(len(SPLITS))
    for k, (lab, col) in enumerate(
        (
            ("within 1% of ctl alone", "#adb5bd"),
            ("carry better", "#2b8a3e"),
            ("carry worse", "#e03131"),
        )
    ):
        v = np.array([sh[k] for sh in shares])
        ax.barh(np.arange(len(SPLITS)), v, left=left, color=col, label=lab)
        left += v
    ax.set_yticks(np.arange(len(SPLITS)), [lab.replace("\n", " ") for _s, lab in SPLITS])
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of later periods")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.25))
    save(fig, "ties.svg", inputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
