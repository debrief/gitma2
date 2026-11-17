"""Spec 023 slides: SVG figures from the long-engagement record.

    uv run python scripts/research/long_charts.py \\
        [--raw experiments/20261117-long/raw] \\
        [--out-dir site/static/img/2026-11-17-long-engagements-slides]

* ``windows.svg``: how each system reads a long engagement (sliding 2-hour window; a chain of
  2-hour windows overlapping by 30 minutes; the IMM over everything).
* ``track-<h>h.svg``: the truth, the stitched time-late control and C″ over one engagement.
* ``errors-realtime-<h>h.svg`` and ``errors-timelate-<h>h.svg``: relative range error against
  time, by system.
* ``cost.svg``: the control's run time on one period against its length, and the bound's memory
  against engagement length.

Writes ``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "research"))

from long_report import LABEL, RT, TL, build, plausible  # noqa: E402

COL = {
    "e": "#ff7f0e",
    "c2": "#8c564b",
    "one_leg": "#7f7f7f",
    "imm": "#17becf",
    "ctl-d1-q0.01": "#9467bd",
    "history-best": "#2ca02c",
}


def _sidecar(path: Path, inputs: list[Path], extra: dict[str, Any]) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/long_charts.py",
                "git_commit": g.commit,
                "git_dirty": g.dirty,
                "inputs": {
                    (
                        str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
                    ): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                }
                | extra,
            },
            indent=1,
        )
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="experiments/20261117-long/raw")
    ap.add_argument("--out-dir", default="site/static/img/2026-11-17-long-engagements-slides")
    ap.add_argument("--hours", type=float, default=48.0, help="the engagement drawn")
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from tma2.timelate.score import row_errors

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none", "figure.dpi": 100})
    raw = ROOT / a.raw
    out = ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    inputs = sorted(raw.glob("*.json"))
    summary, full = build(raw)
    pick = next(i for i, g in full.items() if g["e"].meta["hours"] == a.hours)
    e = full[pick]["e"]
    tag = f"{a.hours:g}h"

    # windows diagram
    fig, ax = plt.subplots(figsize=(7.5, 2.4))
    T = 10.0
    ax.add_patch(plt.Rectangle((0, 2.6), T, 0.5, color="#17becf", alpha=0.6))
    ax.text(T + 0.1, 2.85, "IMM: the whole engagement, one filter", va="center")
    for k, t in enumerate(np.arange(2.0, T + 0.01, 1 / 6)):
        if k % 6 == 0:
            ax.add_patch(
                plt.Rectangle((t - 2, 1.55 + 0.1 * (k // 6 % 3)), 2, 0.08, color="#ff7f0e")
            )
    ax.text(T + 0.1, 1.7, "E, C″: the last 2 h, every 10 min,\nre-solved each time", va="center")
    a0 = 0.0
    j = 0
    while a0 < T:
        ax.add_patch(
            plt.Rectangle(
                (a0, 0.3 + 0.35 * (j % 2)), min(2, T - a0), 0.25, color="#9467bd", alpha=0.7
            )
        )
        a0 += 1.5
        j += 1
    ax.text(T + 0.1, 0.6, "ctl: 2-h windows, 30-min overlaps,\nstitched mid-overlap", va="center")
    ax.set_xlim(0, T + 4.2)
    ax.set_ylim(0, 3.3)
    ax.set_yticks([])
    ax.set_xticks(range(0, 11, 2))
    ax.set_xlabel("hours into the engagement")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = out / "windows.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, [], {"what": "schematic"})

    # track plot
    tl = full[pick]["timelate"]
    if tl:
        A = tl["_arrays"]
        fig, ax = plt.subplots(figsize=(6.4, 6.0))
        ax.plot(e.own[:, 1] / 1e3, e.own[:, 2] / 1e3, color="#1f77b4", lw=0.7, label="ownship")
        ax.plot(e.tgt[:, 1] / 1e3, e.tgt[:, 2] / 1e3, color="#d62728", lw=1.2, label="target")
        for s in ("c2", "ctl-d1-q0.01"):
            st = plausible(A["states"][s], A["truth"])
            ax.plot(st[:, 0] / 1e3, st[:, 1] / 1e3, color=COL[s], lw=0.8, label=LABEL[s])
        ax.set_aspect("equal")
        ax.set_xlabel("east, km")
        ax.set_ylabel("north, km")
        ax.legend(loc="best", fontsize=8)
        ax.set_title(f"{a.hours:g}-hour engagement (seed 348): time-late tracks, stitched")
        fig.tight_layout()
        p = out / f"track-{tag}.svg"
        fig.savefig(p)
        plt.close(fig)
        _sidecar(p, inputs, {"engagement_index": pick})

        fig, ax = plt.subplots(figsize=(7.5, 2.8))
        t = A["rows"] * e.dt / 3600
        for s in TL:
            err = row_errors(plausible(A["states"][s], A["truth"]), A["truth"])[:, 0]
            ax.plot(t, np.minimum(err, 1.0), color=COL[s], lw=0.8, label=LABEL[s])
        for w in tl["_windows"][1:]:
            ax.axvline(w["first"] * e.dt / 3600, color="#bbb", lw=0.5, zorder=0)
        ax.set_ylim(0, 1.0)
        ax.set_xlabel("hours")
        ax.set_ylabel("relative range error\n(clipped at 1)")
        ax.legend(fontsize=7, ncol=3, loc="upper right")
        fig.tight_layout()
        p = out / f"errors-timelate-{tag}.svg"
        fig.savefig(p)
        plt.close(fig)
        _sidecar(p, inputs, {"engagement_index": pick})

    rt = full[pick]["realtime"]
    if rt:
        A = rt["_arrays"]
        fig, ax = plt.subplots(figsize=(7.5, 2.8))
        t = A["times"] / 3600
        for s in RT:
            err = row_errors(plausible(A["states"][s], A["truth"]), A["truth"])[:, 0]
            ax.plot(t, np.minimum(err, 1.0), color=COL[s], lw=0.8, marker=".", ms=2, label=LABEL[s])
        ax.set_ylim(0, 1.0)
        ax.set_xlabel("hours")
        ax.set_ylabel("relative range error\n(clipped at 1)")
        ax.legend(fontsize=7, ncol=4, loc="upper right")
        fig.tight_layout()
        p = out / f"errors-realtime-{tag}.svg"
        fig.savefig(p)
        plt.close(fig)
        _sidecar(p, inputs, {"engagement_index": pick})

    # cost
    bc = ROOT / "experiments/20261117-long/bound-cost.jsonl"
    rows = [json.loads(x) for x in bc.read_text().splitlines() if x.strip()]
    sc = summary["scaling"]
    fig, axs = plt.subplots(1, 2, figsize=(7.5, 2.8))
    if sc:
        axs[0].plot(
            [r["seconds_long"] / 3600 for r in sc],
            [r["run_s"] / 60 for r in sc],
            "o-",
            color=COL["ctl-d1-q0.01"],
        )
        for r in sc:
            axs[0].annotate(
                f"{r['true_manoeuvres']}",
                (r["seconds_long"] / 3600, r["run_s"] / 60),
                fontsize=7,
                xytext=(3, 3),
                textcoords="offset points",
            )
    axs[0].set_xlabel("period, hours")
    axs[0].set_ylabel("ctl run time, minutes")
    axs[0].set_title("ctl on one period (labels: true manoeuvres)", fontsize=8)
    axs[1].plot(
        [r["hours"] for r in rows], [r["max_rss_mb"] / 1024 for r in rows], "o-", color="#444"
    )
    axs[1].set_xlabel("engagement, hours")
    axs[1].set_ylabel("peak memory, GB")
    axs[1].set_title("whole-engagement Cramér–Rao bound", fontsize=8)
    fig.tight_layout()
    p = out / "cost.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs + [bc], {})
    print(sorted(x.name for x in out.glob("*.svg")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
