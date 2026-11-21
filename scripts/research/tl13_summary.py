"""Spec 033 follow-up: summary of the one-job evidence re-check (``tl13_evidence2.py``).

    uv run python scripts/research/tl13_summary.py > experiments/20261121-tl13-evidence/summary.txt

Evidence: the true history against the better of the declared history (as searched) and its
refit from neutral starts, counted at margins of 1, 3 and 10 units. Errors (median relative
range error per later period on the scored rows, all computed in one job per engagement):
alone ÷ joint, alone ÷ gap-true, joint ÷ gap-true, declared-refit ÷ gap-true (both refitted
from neutral starts: the like-with-like test of the true gap structure), joint ÷ declared-refit
(what the refit costs) and alone ÷ true, over all later periods, after
gaps of at least 70 min, and by whether the period has its own ownship turn; geometric mean with
an engagement bootstrap (2,000, seed 23), median, share better and twice as good or bad.
"""

from __future__ import annotations

import glob
import json

import numpy as np

REC = "experiments/20261121-tl13-evidence"
PAIRS = (
    ("alone", "joint"),
    ("alone", "gap_true"),
    ("joint", "gap_true"),
    ("declared_refit", "gap_true"),
    ("joint", "declared_refit"),
    ("alone", "true"),
)


def boot(lr: np.ndarray, eng: np.ndarray) -> tuple[float, float, float]:
    rng = np.random.default_rng(23)
    u = np.unique(eng)
    idx = {e: np.flatnonzero(eng == e) for e in u}
    m = []
    for _ in range(2000):
        pick = rng.choice(u, u.size)
        m.append(np.mean(np.concatenate([lr[idx[e]] for e in pick])))
    return (
        float(np.exp(lr.mean())),
        float(np.exp(np.percentile(m, 2.5))),
        float(np.exp(np.percentile(m, 97.5))),
    )


def main() -> int:
    recs = []
    for f in sorted(glob.glob(f"{REC}/*.json")):
        if f.endswith("ci.json"):
            continue
        recs.append(json.loads(open(f).read()))
    recs.sort(key=lambda r: r["ordinal"])
    print("evidence (log): true - best declared (searched or refit); declared searched - refit")
    d = []
    for r in recs:
        ev = r["evidence"]
        best = max(ev["declared"], ev["declared_refit"])
        dd = ev["true"] - best
        d.append(dd)
        m = r["manoeuvres"]
        print(
            f"  {r['ordinal']:3d}  true {m['true']:2d} / declared {m['declared']:2d} (in gaps {m['true_in_gaps']} / {m['declared_in_gaps']})"
            f"  true - best declared {dd:+7.1f}  searched - refit {ev['declared'] - ev['declared_refit']:+6.1f}  gap-true - best {ev['gap_true'] - best:+7.1f}"
        )
    d = np.array(d)
    for mg in (1, 3, 10):
        print(
            f"  margin {mg}: truth better {int((d > mg).sum())}, declared better {int((d < -mg).sum())}, within {int((np.abs(d) <= mg).sum())} of {d.size}"
        )
    rows = []
    for r in recs:
        for p in r["periods"]:
            rows.append((r["ordinal"], p["gap_s"] >= 4200, p["own_turn"], p["median_range_error"]))
    eng = np.array([x[0] for x in rows])
    long_gap = np.array([x[1] for x in rows])
    own = np.array([x[2] for x in rows])
    print(
        f"later periods scored: {len(rows)} in {np.unique(eng).size} engagements (CPU per engagement, all systems in one job)"
    )
    for lab, sel in (
        ("all later periods", np.ones(len(rows), bool)),
        ("after a gap >= 70 min", long_gap),
        ("after a gap >= 70 min, no own turn", long_gap & ~own),
        ("after a gap >= 70 min, own turn", long_gap & own),
    ):
        if sel.sum() == 0:
            continue
        print(f"{lab} ({int(sel.sum())} periods, {np.unique(eng[sel]).size} engagements)")
        for a, b in PAIRS:
            lr = np.log(np.array([x[3][a] / x[3][b] for x in rows]))[sel]
            if np.unique(eng[sel]).size < 5:
                print(
                    f"  {a} / {b}: median {np.exp(np.median(lr)):.2f} (too few engagements for an interval)"
                )
                continue
            g, lo, hi = boot(lr, eng[sel])
            print(
                f"  {a} / {b}: {g:.2f} [{lo:.2f}, {hi:.2f}] median {np.exp(np.median(lr)):.2f}"
                f" better {np.mean(lr > 0):.2f} twice good {np.mean(lr > np.log(2)):.2f} twice bad {np.mean(lr < -np.log(2)):.2f}"
            )
    # does the joint loss after long gaps sit where the evidence prefers the declared history?
    dmap = {r["ordinal"]: dd for r, dd in zip(recs, d, strict=True)}
    for lab, cond in (
        ("evidence prefers declared by > 3", lambda v: v < -3),
        ("within 3", lambda v: abs(v) <= 3),
        ("truth better by > 3", lambda v: v > 3),
    ):
        sel = long_gap & np.array([cond(dmap[e]) for e in eng])
        if sel.sum() == 0:
            print(f"after >= 70 min, {lab}: no periods")
            continue
        lr = np.log(np.array([x[3]["alone"] / x[3]["joint"] for x in rows]))[sel]
        g, lo, hi = boot(lr, eng[sel])
        print(
            f"after >= 70 min, {lab}: alone / joint {g:.2f} [{lo:.2f}, {hi:.2f}] ({int(sel.sum())} periods, {np.unique(eng[sel]).size} engagements)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
