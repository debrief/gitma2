"""Spec 025 slides: SVG figures from the committed test record.

    uv run python scripts/research/tl8_charts.py --record experiments/20261118-tl8 --out-dir <dir>

* ``verdict.svg``: `ctl` alone ÷ joint in range on every split, with 95% intervals: on the
  registered rows (span bound below 0.5) and on rows the period determines alone.
* ``kinds.svg``: the same ratio for periods with and without an ownship turn of their own.
* ``gaps.svg``: true manoeuvres in gaps found and missed by the joint solve, and the share of
  quiet gaps in which it invents one.
* ``track.svg``: one stored Annex B engagement as tracks (truth red, ownship blue, `ctl` alone
  per period orange, the joint solve green, dashed through the gaps). Chosen by a rule, not
  by eye: of the stored engagements with three periods (else two), the one whose
  engagement-mean log ratio alone ÷ joint is the median.

Reads ``summary.json``, ``man2.errors.npz`` and ``man2.periods.json``; writes
``<fig>.svg.json`` beside each figure with the inputs' digests and the commit.
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
    rec = Path(a.record)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = json.loads((rec / "summary.json").read_text())
    sp = summary["splits"]
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})

    def save(fig: Any, name: str, inputs: list[Path], extra: dict[str, Any] | None = None) -> None:
        path = out / name
        fig.savefig(path, format="svg", bbox_inches="tight", metadata={"Date": None})
        plt.close(fig)
        side = {
            "figure": name,
            "script": "scripts/research/tl8_charts.py",
            "git_commit": g.commit,
            "git_dirty": g.dirty,
            "inputs": {str(p): _sha(p) for p in inputs},
            **(extra or {}),
        }
        (out / f"{name}.json").write_text(json.dumps(side, indent=1) + "\n")

    def bars(ax: Any, rows: list[tuple[str, list[dict[str, Any]]]], labels: list[str]) -> None:
        x = np.arange(len(SPLITS))
        w = 0.8 / len(rows)
        colours = ["#2b8a3e", "#adb5bd", "#e8590c"]
        for k, (lab, ds) in enumerate(rows):
            xs = x - 0.4 + w * (k + 0.5)
            v = np.array([d.get("value", np.nan) for d in ds])
            lo = np.array([d.get("lo", np.nan) for d in ds])
            hi = np.array([d.get("hi", np.nan) for d in ds])
            ax.bar(xs, v, w * 0.9, color=colours[k], label=lab)
            ax.errorbar(xs, v, yerr=[v - lo, hi - v], fmt="none", ecolor="black", capsize=3, lw=1)
            for xi, d in zip(xs, ds, strict=True):
                if "periods" in d:
                    ax.text(xi, 0.55, f"n {d['periods']}", ha="center", fontsize=7, rotation=90)
        ax.axhline(1, color="black", lw=0.8)
        ax.set_yscale("log")
        ax.set_xticks(x, labels)
        ax.set_ylim(0.5, 40)
        ax.set_ylabel("ctl alone ÷ joint (range; above 1: joining helps)")
        ax.legend(frameon=False, fontsize=8, loc="upper left")

    labels = [lab for _s, lab in SPLITS]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars(
        ax,
        [
            (
                "rows the span determines (registered)",
                [sp[s]["ratios"]["alone/joint"]["range"] for s, _ in SPLITS],
            ),
            (
                "rows the period determines alone",
                [sp[s]["ratios_own_rows"]["alone/joint"]["range"] for s, _ in SPLITS],
            ),
        ],
        labels,
    )
    save(fig, "verdict.svg", [rec / "summary.json"])

    fig, ax = plt.subplots(figsize=(7, 4))
    bars(
        ax,
        [
            (
                "no ownship turn of its own",
                [sp[s]["by_kind"]["no_own_turn"]["alone/joint"]["range"] for s, _ in SPLITS],
            ),
            (
                "with its own ownship turn",
                [sp[s]["by_kind"]["own_turn"]["alone/joint"]["range"] for s, _ in SPLITS],
            ),
        ],
        labels,
    )
    save(fig, "kinds.svg", [rec / "summary.json"])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8, 3.2))
    gs = [(lab, sp[s]["gaps"]) for s, lab in SPLITS if sp[s]["gaps"]["with_true_manoeuvre"]]
    xs = np.arange(len(gs))
    a1.bar(xs, [x["found"] for _l, x in gs], color="#2b8a3e", label="found")
    a1.bar(
        xs,
        [x["missed"] for _l, x in gs],
        bottom=[x["found"] for _l, x in gs],
        color="#e03131",
        label="missed",
    )
    a1.set_xticks(xs, [lab for lab, _x in gs])
    a1.set_ylabel("true manoeuvres inside gaps")
    a1.legend(frameon=False, fontsize=8)
    qs = [(lab, sp[s]["gaps"]["invented_share"]) for s, lab in SPLITS]
    a2.bar(np.arange(len(qs)), [0 if v is None else v for _l, v in qs], color="#e8590c")
    a2.set_xticks(np.arange(len(qs)), [lab for lab, _v in qs])
    a2.set_ylabel("quiet gaps with an invented manoeuvre")
    a2.set_ylim(0, 0.5)
    fig.tight_layout()
    save(fig, "gaps.svg", [rec / "summary.json"])

    # one engagement as tracks, chosen by rule
    z = dict(np.load(rec / "man2.errors.npz"))
    recs = {int(r["ordinal"]): r for r in json.loads((rec / "man2.periods.json").read_text())}
    rows = np.isfinite(z["bound_span"][:, 0]) & (z["bound_span"][:, 0] < UNDETERMINED)
    t = period_table(z, rows, ["alone", "joint"])
    lr = np.log(t["alone"][:, 0] / t["joint"][:, 0])
    stored = sorted(int(e) for e in np.unique(z["fig_eng"]))
    cand = []
    for e in stored:
        m = (t["eng"] == e) & np.isfinite(lr)
        if m.any() and "layout" in recs[e]:
            cand.append((len(recs[e]["layout"]["periods"]), float(lr[m].mean()), e))
    k3 = [c for c in cand if c[0] == 3] or cand
    k3.sort(key=lambda c: c[1])
    _n, mlr, eng = k3[len(k3) // 2]
    r = recs[eng]
    m = z["fig_eng"] == eng
    tr, jo, al = z["fig_truth"][m], z["fig_joint"][m], z["fig_alone"][m]
    every = 6
    first = r["layout"]["first"]
    idx = first + every * np.arange(tr.shape[0])
    in_gap = np.zeros(idx.size, dtype=bool)
    for ga, gn in r["layout"]["gaps"]:
        in_gap |= (idx >= ga) & (idx < ga + gn)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    km = 1e-3
    ax.plot(tr[:, 4] * km, tr[:, 5] * km, color="#1c7ed6", lw=1.2, label="ownship")
    ax.plot(tr[:, 0] * km, tr[:, 1] * km, color="#e03131", lw=1.6, label="target (truth)")
    ax.plot(
        np.where(in_gap, np.nan, jo[:, 0]) * km,
        np.where(in_gap, np.nan, jo[:, 1]) * km,
        color="#2b8a3e",
        lw=1.4,
        label="joint solve",
    )
    ax.plot(
        np.where(in_gap, jo[:, 0], np.nan) * km,
        np.where(in_gap, jo[:, 1], np.nan) * km,
        color="#2b8a3e",
        lw=1.0,
        ls="--",
        label="joint, in a gap",
    )
    ax.plot(al[:, 0] * km, al[:, 1] * km, color="#e8590c", lw=1.4, label="ctl alone (per period)")
    for i in range(tr.shape[0]):
        if in_gap[i] and (i == 0 or not in_gap[i - 1]):
            ax.plot(tr[i, 4] * km, tr[i, 5] * km, "o", color="#1c7ed6", ms=3)
    ax.set_aspect("equal")
    ax.set_xlabel("east (km)")
    ax.set_ylabel("north (km)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(
        f"Annex B engagement {eng}: alone ÷ joint {np.exp(mlr):.2f} (engagement mean)", fontsize=9
    )
    save(
        fig,
        "track.svg",
        [rec / "man2.errors.npz", rec / "man2.periods.json"],
        {
            "engagement": eng,
            "rule": "median engagement-mean log ratio among stored three-period engagements",
        },
    )
    print({"track_engagement": eng})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
