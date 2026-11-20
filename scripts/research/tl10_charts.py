"""Spec 028 slides: SVG figures from the committed test record.

    uv run python scripts/research/tl10_charts.py --record experiments/20261120-tl10 --out-dir <dir>

* ``verdict.svg``: alone ÷ k4 (the decided ratio) and k4 ÷ joint in range on every split, with
  95% engagement intervals (periods after an engagement's first).
* ``kinds.svg``: alone ÷ the carried prior, uninflated and k4, for periods with and without an
  ownship turn of their own (Annex B and busier).
* ``coverage.svg``: the truth's squared Mahalanobis distance from the carried prior at a period's
  first row, as a cumulative distribution against χ² with 4 degrees of freedom (Annex B),
  uninflated and k4.

Reads ``summary.json`` and ``<split>.periods.json``; writes ``<fig>.svg.json`` sidecars with the
inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CHI2_4_95 = 9.488  # χ² with 4 degrees of freedom, 95% point
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
            "script": "scripts/research/tl10_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): _sha(p) for p in inputs},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")

    def bars(
        ax: Any,
        labels: list[str],
        rows: list[tuple[str, list[dict[str, Any]]]],
        colours: tuple[str, ...] = ("#2b8a3e", "#e8590c"),
    ) -> None:
        x = np.arange(len(labels))
        w = 0.8 / len(rows)
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
        ticks = [0.5, 1, 2, 4, 8]
        ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
        ax.minorticks_off()
        ax.set_xticks(x, labels)
        ax.legend(frameon=False, fontsize=8, loc="upper left")

    k4 = {s: sp[s]["cprior"]["variants"]["k4"] for s, _ in SPLITS}
    fig, ax = plt.subplots(figsize=(7, 4))
    bars(
        ax,
        [lab for _s, lab in SPLITS],
        [
            (
                "alone ÷ k4 (above 1: the carried prior helps)",
                [k4[s]["ratios"]["alone/cv-k4"]["range"] for s, _ in SPLITS],
            ),
            (
                "k4 ÷ joint (above 1: joining better)",
                [k4[s]["ratios"]["cv-k4/joint"]["range"] for s, _ in SPLITS],
            ),
        ],
    )
    ax.set_ylim(0.5, 12)
    ax.set_ylabel("ratio of period median range error")
    save(fig, "verdict.svg", [rec / "summary.json"])

    labels, unin, infl = [], [], []
    for s, lab in SPLITS[:2]:
        c = sp[s]["cprior"]
        for kind, kl in (("own_turn", "own turn"), ("no_own_turn", "no own turn")):
            labels.append(f"{lab}\n{kl}")
            unin.append(c["by_kind"][kind]["alone/cprior"]["range"])
            infl.append(k4[s]["by_kind"][kind]["alone/cv-k4"]["range"])
    fig, ax = plt.subplots(figsize=(7, 4))
    bars(ax, labels, [("uninflated", unin), ("k4 (4× in sd)", infl)], ("#1c7ed6", "#2b8a3e"))
    ax.set_ylim(0.5, 4)
    ax.set_ylabel("alone ÷ carried prior (range)")
    save(fig, "kinds.svg", [rec / "summary.json"])

    f = rec / "man2.periods.json"
    periods = json.loads(f.read_text())
    d_un = [q["truth_md2"] for e in periods for q in e.get("cprior", []) if "truth_md2" in q]
    d_k4 = [
        q["truth_md2"]
        for e in periods
        for q in (e.get("cv") or {}).get("k4", [])
        if "truth_md2" in q
    ]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    grid = np.logspace(-2, 3, 400)
    ax.plot(
        grid,
        1.0 - np.exp(-grid / 2.0) * (1.0 + grid / 2.0),
        color="black",
        lw=1.2,
        ls="--",
        label="calibrated (χ², 4 dof)",
    )
    for vals, lab, col in ((d_un, "uninflated", "#1c7ed6"), (d_k4, "k4", "#2b8a3e")):
        v = np.sort(np.asarray(vals))
        ax.step(
            v,
            np.arange(1, v.size + 1) / v.size,
            where="post",
            color=col,
            label=f"{lab} (n {v.size})",
        )
    ax.axvline(CHI2_4_95, color="#adb5bd", lw=0.8)
    ax.text(CHI2_4_95 * 1.08, 0.05, "95%", fontsize=8, color="#868e96")
    ax.set_xscale("log")
    ax.set_xlim(1e-2, 1e3)
    ax.set_ylim(0, 1)
    ax.set_xlabel("truth's squared distance from the carried prior (d²)")
    ax.set_ylabel("share of carried periods")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "coverage.svg", [f])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
