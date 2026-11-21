"""Spec 031: summary of the evidence diagnostic (``tl12_evidence.py`` on CI, one engagement a
job) against how the joint solve did on each engagement's later periods after a gap of at least
70 min (alone ÷ joint, geometric mean over those periods).

    uv run python scripts/research/tl12_evidence_summary.py > experiments/20261120-tl12-hold-dev/evidence/summary.txt
"""

from __future__ import annotations

import glob
import json

import numpy as np

from tma2.timelate.study8 import UNDETERMINED, period_table

REC = "experiments/20261120-tl12-hold-dev"


def main() -> int:
    z = dict(np.load(f"{REC}/long.errors.npz"))
    P = {e["ordinal"]: e for e in json.loads(open(f"{REC}/long.periods.json").read())}
    span = z["bound_span"][:, 0].astype(np.float64)
    rows = np.isfinite(span) & (span < UNDETERMINED) & ~z["carry_first"].astype(bool)
    t = period_table(z, rows, ["alone", "joint"])
    lr: dict[int, list[float]] = {}
    for i, (e, p) in enumerate(zip(t["eng"], t["period"], strict=True)):
        if P[int(e)]["gaps"][int(p) - 1]["length_s"] >= 4200:
            lr.setdefault(int(e), []).append(float(np.log(t["alone"][i, 0] / t["joint"][i, 0])))
    recs = []
    for f in sorted(glob.glob(f"{REC}/evidence/*.json")):
        if f.endswith("ci.json"):
            continue
        recs.append(json.loads(open(f).read()))
    recs.sort(key=lambda r: r["ordinal"])
    parts = ("fit", "legs", "changes", "state", "occam")
    print(
        "ordinal | true / declared manoeuvres | cut | evidence true - declared | parts (true - declared) | alone/joint, >=70 min periods"
    )
    d_all, g_all = [], []
    for r in recs:
        d = r["evidence_true"] - r["evidence_declared"]
        pp = " ".join(f"{k} {r['parts_true'][k] - r['parts_declared'][k]:+.1f}" for k in parts)
        g = lr.get(r["ordinal"])
        gs = f"{np.exp(np.mean(g)):.2f} (n {len(g)})" if g else "-"
        print(
            f"{r['ordinal']:3d} | {r['true_manoeuvres']:2d} / {r['declared_manoeuvres']:2d} | {r['cut_at_start']} | {d:+8.1f} | {pp} | {gs}"
        )
        if g:
            d_all.append(d)
            g_all.append(np.mean(g))
    d = np.array([r["evidence_true"] - r["evidence_declared"] for r in recs])
    print(
        f"engagements {d.size}: truth has more evidence (search failure) in {int((d > 0).sum())},"
        f" by more than 10 in {int((d > 10).sum())}; declared at least as good in {int((d <= 0).sum())}; median {np.median(d):+.1f}"
    )
    tm = np.array([r["true_manoeuvres"] for r in recs])
    dm = np.array([r["declared_manoeuvres"] for r in recs])
    print(
        f"manoeuvres in the span: true {tm.sum()}, declared {dm.sum()} (declared fewer in {int((dm < tm).sum())} of {d.size})"
    )
    for k in parts:
        v = np.array([r["parts_true"][k] - r["parts_declared"][k] for r in recs])
        print(f"  part {k}: true - declared median {np.median(v):+.1f}")
    da, ga = np.array(d_all), np.array(g_all)
    for lab, m in (
        ("search failure (d > 0)", da > 0),
        ("evidence prefers declared (d <= 0)", da <= 0),
    ):
        if m.any():
            print(
                f"alone/joint on >=70 min periods where {lab}: {np.exp(ga[m].mean()):.2f} over {int(m.sum())} engagements"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
