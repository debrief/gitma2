"""Spec 033 slides: SVG figures from the committed development records.

    uv run python scripts/research/tl12_charts.py --out-dir <dir>

* ``bands.svg``: alone ÷ joint by the gap before a later period, both runs (ownship legs 20–40
  min and 1–2 h), with 95% engagement intervals.
* ``systems.svg``: median range error of `ctl` alone, the joint solve and k4 on later periods, both
  runs.
* ``evidence.svg``: per engagement with a gap of at least 70 min (legs 1–2 h), the log evidence
  of the true gap history minus the declared one, against alone ÷ joint on its later periods
  after such a gap.

Writes ``<fig>.svg.json`` sidecars with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
from typing import Any

RUNS = {
    "ownship legs 20–40 min": Path("experiments/20261120-tl12-dev"),
    "ownship legs 1–2 h": Path("experiments/20261120-tl12-hold-dev"),
}
BANDS = ((30, 50), (50, 70), (70, 91))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from tma2.data.provenance import read_git_provenance
    from tma2.timelate.study8 import UNDETERMINED, paired, period_table

    g = read_git_provenance()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})

    def save(fig: Any, name: str, inputs: list[Path]) -> None:
        fig.savefig(out / name, format="svg", bbox_inches="tight", metadata={"Date": None})
        plt.close(fig)
        side = {
            "figure": name,
            "script": "scripts/research/tl12_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): _sha(p) for p in inputs},
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")

    tables, gaps, inputs = {}, {}, []
    for name, rec in RUNS.items():
        f, pj = rec / "long.errors.npz", rec / "long.periods.json"
        inputs += [f, pj]
        z = dict(np.load(f))
        P = {e["ordinal"]: e for e in json.loads(pj.read_text())}
        span = z["bound_span"][:, 0].astype(np.float64)
        rows = np.isfinite(span) & (span < UNDETERMINED) & ~z["carry_first"].astype(bool)
        t = period_table(z, rows, ["alone", "joint", "cv-k4"])
        tables[name] = t
        gaps[name] = np.array(
            [
                P[int(e)]["gaps"][int(p) - 1]["length_s"] / 60.0
                for e, p in zip(t["eng"], t["period"], strict=True)
            ]
        )

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(len(BANDS))
    w = 0.38
    for k, (name, t) in enumerate(tables.items()):
        ds = []
        for lo, hi in BANDS:
            sel = (gaps[name] >= lo) & (gaps[name] < hi)
            ds.append(paired(t["alone"][sel], t["joint"][sel], t["eng"][sel], 0))
        v = np.array([d["value"] for d in ds])
        lo_ = np.array([d["lo"] for d in ds])
        hi_ = np.array([d["hi"] for d in ds])
        xs = x - w / 2 + k * w
        ax.bar(xs, v, w * 0.9, color=("#1c7ed6", "#e8590c")[k], label=name)
        ax.errorbar(xs, v, yerr=[v - lo_, hi_ - v], fmt="none", ecolor="black", capsize=3, lw=1)
        for xi, d in zip(xs, ds, strict=True):
            ax.text(xi, 0.42, f"n {d['periods']}", ha="center", fontsize=7, rotation=90)
    ax.axhline(1, color="black", lw=0.8)
    ax.set_yscale("log")
    ticks = [0.5, 1, 2, 4]
    ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.minorticks_off()
    ax.set_ylim(0.4, 7)
    ax.set_xticks(x, [f"gap {lo}–{min(hi, 90)} min" for lo, hi in BANDS])
    ax.set_ylabel("alone ÷ joint (above 1: joining helps)")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    save(fig, "bands.svg", inputs)

    fig, ax = plt.subplots(figsize=(7, 3.6))
    sysl = (("alone", "ctl alone"), ("joint", "joint solve"), ("cv-k4", "carried prior k4"))
    for k, (s, lab) in enumerate(sysl):
        meds = [float(np.median(t[s][:, 0])) for t in tables.values()]
        ax.bar(
            x[:2] - 0.3 + k * 0.3, meds, 0.27, color=("#868e96", "#1c7ed6", "#2b8a3e")[k], label=lab
        )
    ax.set_xticks(x[:2], list(tables))
    ax.set_ylabel("median range error (fraction of range)")
    ax.legend(frameon=False, fontsize=8)
    save(fig, "systems.svg", inputs)

    rec = RUNS["ownship legs 1–2 h"]
    t = tables["ownship legs 1–2 h"]
    G = gaps["ownship legs 1–2 h"]
    lr: dict[int, list[float]] = {}
    for i, (e, _p) in enumerate(zip(t["eng"], t["period"], strict=True)):
        if G[i] >= 70:
            lr.setdefault(int(e), []).append(float(np.log(t["alone"][i, 0] / t["joint"][i, 0])))
    pts, ev_inputs = [], []
    for f in sorted(glob.glob(str(rec / "evidence" / "*.json"))):
        if f.endswith("ci.json"):
            continue
        ev_inputs.append(Path(f))
        r = json.loads(Path(f).read_text())
        if r["ordinal"] in lr:
            pts.append(
                (
                    r["evidence_true"] - r["evidence_declared"],
                    float(np.exp(np.mean(lr[r["ordinal"]]))),
                )
            )
    p = np.array(pts)
    d_plot = np.sign(p[:, 0]) * np.log1p(np.abs(p[:, 0]))
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.scatter(d_plot, p[:, 1], color=np.where(p[:, 0] > 0, "#e03131", "#1c7ed6"), s=28)
    ax.axvline(0, color="black", lw=0.8)
    ax.axhline(1, color="black", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4], ["0.25", "0.5", "1", "2", "4"])
    ax.minorticks_off()
    tk = [-100, -10, -1, 0, 1, 10]
    ax.set_xticks([np.sign(v) * np.log1p(abs(v)) for v in tk], [str(v) for v in tk])
    ax.set_xlabel("log evidence, true gap history − declared (right of 0: the search fell short)")
    ax.set_ylabel("alone ÷ joint after a gap ≥ 70 min")
    save(fig, "evidence.svg", inputs + ev_inputs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
