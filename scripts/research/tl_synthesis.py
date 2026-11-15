"""Spec 019: the time-late track's figures of record in one place, from the committed test
records of specs 016, 017 and 018 (seeds 341, 344 and 347), and three charts.

    uv run python scripts/research/tl_synthesis.py [--out experiments/20261115-tl-synthesis/tables.md] [--fig-dir <dir>]

Every number is read from a record's ``summary.json``; nothing is typed by hand. The
tables: the old system (C″ read as a track) and the evidence search against the standing
control; the standing control against the fit told the true history; and the three
attempts to beat the control (a learned whole-period model, the search told the true
statistics, a prior adapted to the period). The charts (``gains.svg``, ``remaining.svg``,
``challengers.svg``) show the same, and ``tracks.svg`` shows three stored shifted periods
of spec 017's test (seed 344) chosen by a rule: of the stored periods, those where the
standing control is best, median and worst against C″ (ratio of median range error).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECORDS = [
    ("016", 341, Path("experiments/20261114-tl4")),
    ("017", 344, Path("experiments/20261114-tl5")),
    ("018", 347, Path("experiments/20261115-tl6")),
]
SPLITS = [
    ("man2", "Annex B"),
    ("shift", "Shifted"),
    ("shift2", "Shifted 2"),
    ("quiet", "Held course"),
    ("man2-out", "Outliers 2%"),
    ("man2-out-harsh", "Outliers 5%"),
    ("man2-corr", "Correlated"),
    ("man2-bias", "Bias"),
    ("whole", "Whole engagements"),
]
CTL = "ctl-d1-q0.01"


def ci(v: dict[str, Any] | None) -> str:
    if not v:
        return "–"
    return f"{v['geometric_mean']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}] ({v['periods']})"


def load() -> dict[str, dict[str, Any]]:
    return {
        spec: json.loads((ROOT / d / "summary.json").read_text())["splits"]
        for spec, _seed, d in RECORDS
    }


def get(sp: dict[str, Any], split: str, key: str, three: bool = False) -> dict[str, Any] | None:
    s = sp.get(split)
    if not s:
        return None
    if three:
        return ((s.get("comparisons3") or {}).get(key) or {}).get("range")
    return (s.get("comparisons") or {}).get(key)


def tables(data: dict[str, dict[str, Any]]) -> str:
    out = [
        "# The time-late track: figures of record (generated)",
        "",
        "Paired per-period ratios of period median range error, geometric mean with a 95% period",
        "bootstrap and the number of periods in the pair. Test records only: spec 016 (seed 341),",
        "spec 017 (seed 344), spec 018 (seed 347). `scripts/research/tl_synthesis.py`.",
        "",
        "## What the standing control added (above 1: the control is better)",
        "",
        "| Split | Spec (seed) | C″ as a track ÷ control | Evidence search ÷ control |",
        "| --- | --- | --- | --- |",
    ]
    for k, lab in SPLITS:
        for spec, seed, _d in RECORDS:
            a = get(data[spec], k, f"c2_over_{CTL}")
            b = get(data[spec], k, f"search3_over_{CTL}")
            if a or b:
                out += [f"| {lab} | {spec} ({seed}) | {ci(a)} | {ci(b)} |"]
    out += [
        "",
        "## What the search added to the old system (above 1: the search is better)",
        "",
        "| Split | Spec (seed) | C″ as a track ÷ evidence search |",
        "| --- | --- | --- |",
    ]
    for k, lab in SPLITS:
        for spec, seed, _d in RECORDS:
            v = get(data[spec], k, "search3_over_c2")
            if v:
                inv = {
                    "geometric_mean": 1 / v["geometric_mean"],
                    "lo": 1 / v["hi"],
                    "hi": 1 / v["lo"],
                    "periods": v["periods"],
                }
                out += [f"| {lab} | {spec} ({seed}) | {ci(inv)} |"]
    out += [
        "",
        "## What remains: against fits told the true history (references, not bounds)",
        "",
        "| Split | Spec (seed) | Control (undeclared) ÷ true history, free unless it drifts | Control ÷ true history, times held | C″ ÷ true history, free unless it drifts |",
        "| --- | --- | --- | --- | --- |",
    ]
    for k, lab in SPLITS:
        for spec, seed, _d in RECORDS:
            a = get(data[spec], k, "ctl_over_history-best")
            b = get(data[spec], k, f"{CTL}_over_ref-full")
            c = get(data[spec], k, "c2_over_history-best")
            if a or b or c:
                out += [f"| {lab} | {spec} ({seed}) | {ci(a)} | {ci(b)} | {ci(c)} |"]
    out += [
        "",
        "## The attempts to beat the control (control ÷ challenger; above 1: the challenger is better)",
        "",
        "| Split | Learned model, arc read-out, seed 1 (016) | Learned model, own track, seed 1 (016) | Search told the true statistics (017) | The same (018) | Prior adapted to the period, declared (018) | The same, hedged (018) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for k, lab in SPLITS:
        row = [
            get(data["016"], k, f"{CTL}_over_learned-s1-arc"),
            get(data["016"], k, f"{CTL}_over_learned-s1"),
            get(data["017"], k, f"{CTL}_over_true"),
            get(data["018"], k, f"{CTL}_over_true"),
            get(data["018"], k, f"{CTL}_over_ada-d1-q0.01", three=True),
            get(data["018"], k, f"{CTL}_over_ada-h1", three=True),
        ]
        if any(row):
            out += [f"| {lab} | " + " | ".join(ci(v) for v in row) + " |"]
    return "\n".join(out) + "\n"


def charts(data: dict[str, dict[str, Any]], fig_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.report.plots import ESTIMATORS, STYLE

    g = read_git_provenance()  # before writing anything
    fig_dir.mkdir(parents=True, exist_ok=True)
    green, orange, purple, grey = ESTIMATORS[0], ESTIMATORS[1], ESTIMATORS[2], ESTIMATORS[3]
    cols = {"016": grey, "017": purple, "018": orange}
    used: dict[str, list[Path]] = {}
    summaries = [d / "summary.json" for _s, _seed, d in RECORDS]

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

    def by_split(key_of: Any, title: str, ylabel: str, name: str, splits: list[str]) -> None:
        labs = [(k, lab) for k, lab in SPLITS if k in splits]
        fig, ax = plt.subplots(figsize=(8.8, 3.9))
        seen: set[str] = set()
        for i, (k, _lab) in enumerate(labs):
            for j, (spec, seed, _d) in enumerate(RECORDS):
                v = key_of(spec, k)
                tag = f"spec {spec}, seed {seed}"
                point(ax, i + (j - 1) * 0.2, v, cols[spec], None if tag in seen or not v else tag)
                if v:
                    seen.add(tag)
        ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
        ax.set_xticks(range(len(labs)), [lab.replace(" ", "\n", 1) for _, lab in labs], fontsize=8)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10)
        ax.legend(frameon=False, fontsize=7)
        fig.tight_layout()
        fig.savefig(fig_dir / name)
        plt.close(fig)
        used[name] = summaries

    with plt.rc_context(STYLE):
        every = ["man2", "shift", "shift2", "quiet", "man2-out", "man2-corr"]

        def old(spec: str, k: str) -> dict[str, Any] | None:
            return get(data[spec], k, f"c2_over_{CTL}")  # spec 016's record has no such pair

        by_split(
            old,
            "The old system read as a track ÷ the standing control (three test seeds)",
            "C″ ÷ control, range\n(above 1: the control is better)",
            "gains.svg",
            every,
        )
        by_split(
            lambda spec, k: get(data[spec], k, "ctl_over_history-best"),
            "What remains: the control ÷ a fit told the true history (a reference, not a bound)",
            "control ÷ true-history fit, range",
            "remaining.svg",
            every,
        )
        rows = [
            (
                "learned model,\narc read-out (016)",
                "016",
                f"{CTL}_over_learned-s1-arc",
                False,
                grey,
            ),
            ("learned model,\nown track (016)", "016", f"{CTL}_over_learned-s1", False, "#b0b6b6"),
            ("told the true\nstatistics (017)", "017", f"{CTL}_over_true", False, green),
            ("told the true\nstatistics (018)", "018", f"{CTL}_over_true", False, green),
            ("prior adapted,\ndeclared (018)", "018", f"{CTL}_over_ada-d1-q0.01", True, purple),
            ("prior adapted,\nhedged (018)", "018", f"{CTL}_over_ada-h1", True, orange),
        ]
        fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.0), sharey=True)
        for ax, (k, lab) in zip(
            axes, [("man2", "Annex B targets"), ("shift", "shifted targets")], strict=True
        ):
            for i, (_name, spec, key, three, col) in enumerate(rows):
                point(ax, i, get(data[spec], k, key, three), col, None)
            ax.axhline(1.0, color="0.5", lw=0.8, ls="--")
            ax.set_xticks(range(len(rows)), [r[0] for r in rows], fontsize=6.5)
            ax.set_title(lab, fontsize=9)
        axes[0].set_ylabel("control ÷ challenger, range\n(above 1: the challenger is better)")
        fig.suptitle("The attempts to beat the standing control", fontsize=10)
        fig.tight_layout()
        fig.savefig(fig_dir / "challengers.svg")
        plt.close(fig)
        used["challengers.svg"] = summaries

        tr_path = Path("experiments/20261114-tl5/tracks.npz")
        z = np.load(ROOT / tr_path)

        def med(key: str, pid: int) -> float:
            m = z["shift/period"] == pid
            tr = z["shift/truth"][m].astype(float)
            st = z[f"shift/{key}"][m].astype(float)
            rng = np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])
            est = np.hypot(st[:, 0] - tr[:, 4], st[:, 1] - tr[:, 5])
            return float(np.nanmedian(np.abs(est - rng) / rng))

        ids = [int(i) for i in np.unique(z["shift/period"])]
        ratio = {i: med("c2", i) / med(CTL, i) for i in ids}
        ratio = {i: r for i, r in ratio.items() if np.isfinite(r) and r > 0}
        order = sorted(ratio, key=lambda i: (ratio[i], i))
        picks = [(order[-1], "best"), (order[len(order) // 2], "median"), (order[0], "worst")]
        shown = [
            ("C″ as a track (the old system)", "c2", grey, ":"),
            ("standing control", CTL, purple, "-"),
            ("fit told the true history", "history-best", green, "--"),
        ]
        fig, axes = plt.subplots(1, 3, figsize=(11.6, 4.2))
        for ax, (pid, tag) in zip(axes, picks, strict=True):
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
                f"the control at its {tag} against C″: period {pid}\nC″ ÷ control {ratio[pid]:.2f}",
                fontsize=8,
            )
            ax.set_xlabel("east (km)")
        axes[0].set_ylabel("north (km)")
        axes[0].legend(frameon=False, fontsize=6.5)
        fig.tight_layout()
        fig.savefig(fig_dir / "tracks.svg")
        plt.close(fig)
        used["tracks.svg"] = [tr_path]

    for name, paths in used.items():
        side = {
            "figure": name,
            "script": "scripts/research/tl_synthesis.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        }
        (fig_dir / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out")
    ap.add_argument("--fig-dir")
    a = ap.parse_args(argv)
    data = load()
    text = tables(data)
    if a.fig_dir:
        charts(data, Path(a.fig_dir))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
    elif not a.fig_dir:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
