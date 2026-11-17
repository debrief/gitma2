"""Spec 024 slides: SVG figures from the record of experiments/20261117-long2/.

    uv run python scripts/research/long2_charts.py \\
        [--raw experiments/20261117-long2/raw] [--base experiments/20261117-long/raw] \\
        [--out-dir site/static/img/2026-11-17-long-engagements-2-slides]

* ``carry.svg``: ctl ÷ ctl-carry in median range error, window by window, for each set and length.
* ``cost.svg``: seconds per real-time estimate, spec 023's per-window run against the incremental C;
  and the time-late CPU hours of the searches started from nothing against from the carry.
* ``realistic-<h>h.svg``: the realistic engagement's two contacts, the ownship and ctl-carry.
* ``errors-realistic-<h>h.svg``: contact 1's relative range error against time (real-time E and
  time-late ctl-carry), contact gaps shaded.

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

from long2_report import SET_LABEL, build  # noqa: E402
from long_report import plausible  # noqa: E402

COL = {"base": "#7f7f7f", "real-c1": "#9467bd", "real-c2": "#e377c2"}


def _sidecar(path: Path, inputs: list[Path], extra: dict[str, Any]) -> None:
    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    path.with_suffix(".svg.json").write_text(
        json.dumps(
            {
                "script": "scripts/research/long2_charts.py",
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
    ap.add_argument("--raw", default="experiments/20261117-long2/raw")
    ap.add_argument("--base", default="experiments/20261117-long/raw")
    ap.add_argument("--out-dir", default="site/static/img/2026-11-17-long-engagements-2-slides")
    ap.add_argument("--hours", type=float, default=24.0, help="the realistic engagement drawn")
    a = ap.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from tma2.timelate.score import row_errors

    plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})
    raw, out = ROOT / a.raw, ROOT / a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    inputs = sorted(raw.glob("*.json"))
    summary, full = build(raw, ROOT / a.base)

    # carry against ctl, window by window
    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    xt, xl = [], []
    x = 0
    for name in ("base", "real-c1", "real-c2"):
        for g in summary["sets"][name]:
            t = full[name][g["index"]]["carry"]
            if not t:
                continue
            r = [w["ctl"] / w["carry"] for w in t["_per_window"] if w["ctl"] and w["carry"]]
            jit = (np.arange(len(r)) % 7 - 3) * 0.05
            ax.scatter(x + jit, np.clip(r, 0.2, 5.0), s=8, color=COL[name], alpha=0.8)
            xt.append(x)
            xl.append(f"{g['hours']:g} h")
            x += 1
        x += 0.6
    ax.axhline(1.0, color="#444", lw=0.8)
    ax.set_yscale("log")
    ax.set_yticks([0.25, 0.5, 1, 2, 4], ["0.25", "0.5", "1", "2", "4"])
    ax.set_xticks(xt, xl)
    ax.set_ylabel("ctl ÷ ctl-carry\n(above 1: carry better)")
    for name in ("base", "real-c1", "real-c2"):
        ax.scatter([], [], color=COL[name], s=10, label=SET_LABEL[name])
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    p = out / "carry.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs, {})

    # cost
    fig, axs = plt.subplots(1, 2, figsize=(7.5, 2.8))
    base = summary["sets"]["base"]
    hrs = [g["hours"] for g in base]
    pw = [
        g.get("realtime_per_window", {}).get("seconds_per_evaluation", {}).get("e", np.nan)
        + g.get("realtime_per_window", {}).get("seconds_per_evaluation", {}).get("c2", np.nan)
        for g in base
    ]
    inc = [
        g.get("realtime", {}).get("seconds_per_evaluation", {}).get("e", np.nan)
        + g.get("realtime", {}).get("seconds_per_evaluation", {}).get("c2", np.nan)
        for g in base
    ]
    xx = np.arange(len(hrs))
    axs[0].bar(xx - 0.2, pw, 0.4, color="#bbb", label="per window (spec 023)")
    axs[0].bar(xx + 0.2, inc, 0.4, color="#ff7f0e", label="incremental C")
    axs[0].set_xticks(xx, [f"{h:g} h" for h in hrs])
    axs[0].set_ylabel("s per estimate (E + C″)")
    axs[0].legend(fontsize=7)
    names = ["base", "real-c1", "real-c2"]
    none_h = [
        sum(
            g.get("timelate", {}).get("seconds", {}).get("search_from_none_h", 0)
            for g in summary["sets"][n]
        )
        for n in names
    ]
    carry_h = [
        sum(
            g.get("timelate", {}).get("seconds", {}).get("search_from_carry_h", 0)
            for g in summary["sets"][n]
        )
        for n in names
    ]
    xx = np.arange(3)
    axs[1].bar(xx - 0.2, none_h, 0.4, color="#9467bd", label="search from nothing")
    axs[1].bar(xx + 0.2, carry_h, 0.4, color="#e377c2", label="search from the carry")
    axs[1].set_xticks(xx, ["spec 023's", "realistic c1", "realistic c2"])
    axs[1].set_ylabel("CPU hours, all windows")
    axs[1].legend(fontsize=7)
    fig.tight_layout()
    p = out / "cost.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs, {})

    # realistic engagement: both contacts
    pick = next(i for i, g in enumerate(summary["sets"]["real-c1"]) if g["hours"] == a.hours)
    e1 = full["real-c1"][pick]["e"]
    e2 = full["real-c2"][pick]["e"]
    tag = f"{a.hours:g}h"
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.plot(e1.own[:, 1] / 1e3, e1.own[:, 2] / 1e3, color="#1f77b4", lw=0.7, label="ownship")
    ax.plot(e1.tgt[:, 1] / 1e3, e1.tgt[:, 2] / 1e3, color="#d62728", lw=1.2, label="contact 1")
    ax.plot(e2.tgt[:, 1] / 1e3, e2.tgt[:, 2] / 1e3, color="#ff9896", lw=1.0, label="contact 2")
    for f, lab in (
        (full["real-c1"][pick], "ctl-carry, contact 1"),
        (full["real-c2"][pick], "ctl-carry, contact 2"),
    ):
        t = f["carry"]
        if t:
            st = plausible(t["_arrays"]["states"]["ctl-carry"], t["_arrays"]["truth"])
            ax.plot(
                st[:, 0] / 1e3,
                st[:, 1] / 1e3,
                lw=0.8,
                label=lab,
                color="#9467bd" if "1" in lab else "#e377c2",
            )
    ax.set_aspect("equal")
    ax.set_xlabel("east, km")
    ax.set_ylabel("north, km")
    ax.legend(fontsize=7, loc="best")
    ax.set_title(f"realistic {a.hours:g}-hour engagement (seed 348)")
    fig.tight_layout()
    p = out / f"realistic-{tag}.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs, {"engagement_index": pick})

    # contact 1's error against time, gaps shaded
    fig, ax = plt.subplots(figsize=(7.5, 2.8))
    for a0, b0 in e1.meta["realism"]["gaps_s"]:
        ax.axvspan(a0 / 3600, b0 / 3600, color="#ddd", lw=0)
    f = full["real-c1"][pick]
    if f["realtime"]:
        A = f["realtime"]["_arrays"]
        err = row_errors(plausible(A["states"]["e"], A["truth"]), A["truth"])[:, 0]
        ax.plot(
            A["times"] / 3600, np.minimum(err, 1.0), color="#ff7f0e", lw=0.8, label="real-time E"
        )
    if f["carry"]:
        A = f["carry"]["_arrays"]
        err = row_errors(plausible(A["states"]["ctl-carry"], A["truth"]), A["truth"])[:, 0]
        ax.plot(
            A["rows"] * e1.dt / 3600,
            np.minimum(err, 1.0),
            color="#e377c2",
            lw=0.8,
            label="time-late ctl-carry",
        )
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("hours (grey: contact lost)")
    ax.set_ylabel("relative range error\n(clipped at 1)")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    p = out / f"errors-realistic-{tag}.svg"
    fig.savefig(p)
    plt.close(fig)
    _sidecar(p, inputs, {"engagement_index": pick})
    print(sorted(x.name for x in out.glob("*.svg")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
