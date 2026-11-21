"""Spec 030 follow-on, development look (no new run, no seed): can a per-period consistency flag
find the periods the carried prior makes twice as bad as ``ctl`` alone?

    uv run python scripts/research/tl11_flag_look.py > experiments/20261120-tl11-flag-look/readings.txt

Reads the committed records of spec 030 (refinement seeds 360/361, validation 362, test 363).
Three readings, per seed and split, over periods after an engagement's first (spec 025's rows):

1. The evidence flag: the mixture variants' log Bayes factor of the carried prior against the
   standing prior (``log_odds_carried``; inflation 1 and 2), as a detector of twice-as-bad
   periods (AUC), what flagging at a factor below 1 catches, and the system that falls back to
   ``ctl`` alone where flagged.
2. Its ceiling: the truth's squared distance from the carried prior (an oracle a consistency
   flag can only approximate) as the same detector.
3. What the twice-as-bad periods are: median errors of alone, k4 and the joint solve there and
   elsewhere, and the share with an ownship turn of their own.
"""

from __future__ import annotations

import json

import numpy as np

from tma2.timelate.study8 import UNDETERMINED, _per_period_facts, period_table

REFINE = {
    360: "experiments/20261119-tl10-refine/seed360",
    361: "experiments/20261119-tl10-refine/seed361",
}
ALL = [
    ("refine 360", REFINE[360]),
    ("refine 361", REFINE[361]),
    ("val 362", "experiments/20261119-tl10-val"),
    ("test 363", "experiments/20261120-tl10"),
]
LOG2 = float(np.log(2.0))


def _auc(score: np.ndarray, pos: np.ndarray) -> float:
    """P(a positive scores lower than a negative), ties half."""
    sp, sn = score[pos], score[~pos]
    if sp.size == 0 or sn.size == 0:
        return float("nan")
    return float(np.mean(sp[:, None] < sn[None, :]) + 0.5 * np.mean(sp[:, None] == sn[None, :]))


def _table(d: str, split: str, systems: list[str]) -> tuple[dict, dict] | None:
    try:
        z = dict(np.load(f"{d}/{split}.errors.npz"))
    except FileNotFoundError:
        return None
    span = z["bound_span"][:, 0].astype(np.float64)
    rows = np.isfinite(span) & (span < UNDETERMINED) & ~z["carry_first"].astype(bool)
    periods = {e["ordinal"]: e for e in json.loads(open(f"{d}/{split}.periods.json").read())}
    return period_table(z, rows, systems), periods


def main() -> int:
    gm = lambda x: float(np.exp(np.mean(x)))  # noqa: E731
    print("1. evidence flag (log Bayes factor of the carried prior < 0 -> use ctl alone)")
    for seed, d in REFINE.items():
        for split in ("man2", "shift"):
            r = _table(d, split, ["alone", "cprior", "cv-k2"])
            if r is None:
                continue
            t, P = r
            for var, mix in (("cprior", "m50"), ("cv-k2", "k2m50")):
                lo = np.array(
                    [
                        P[int(e)]["cv"][mix][int(p)].get("log_odds_carried", np.nan)
                        for e, p in zip(t["eng"], t["period"], strict=True)
                    ]
                )
                lr = np.log(t["alone"][:, 0] / t[var][:, 0])
                ok = np.isfinite(lo) & np.isfinite(lr)
                lo, lr = lo[ok], lr[ok]
                bad, good, flag = lr < -LOG2, lr > LOG2, lo < 0
                print(
                    f"  seed {seed} {split:5s} {var:6s} n {lr.size:3d} twice-bad {int(bad.sum()):2d} AUC {_auc(lo, bad):.2f}"
                    f" flagged {flag.mean():.2f} bad caught {flag[bad].mean():.2f} twice-good lost {flag[good].mean():.2f}"
                    f" | alone/var {gm(lr):.2f} alone/flagged {gm(np.where(flag, 0.0, lr)):.2f}"
                )
    print("2. ceiling: the truth's d2 from the carried prior as the detector")
    for name, d in ALL:
        for split in ("man2", "shift"):
            r = _table(d, split, ["alone", "cprior", "cv-k4"])
            if r is None:
                continue
            t, P = r
            for var, src in (("cprior", None), ("cv-k4", "k4")):
                md = np.array(
                    [
                        (P[int(e)]["cprior"] if src is None else P[int(e)]["cv"][src])[int(p)].get(
                            "truth_md2", np.nan
                        )
                        for e, p in zip(t["eng"], t["period"], strict=True)
                    ]
                )
                lr = np.log(t["alone"][:, 0] / t[var][:, 0])
                ok = np.isfinite(md) & np.isfinite(lr)
                md, lr = md[ok], lr[ok]
                bad = lr < -LOG2
                print(
                    f"  {name:10s} {split:5s} {var:6s} n {lr.size:3d} twice-bad {int(bad.sum()):2d} AUC {_auc(-md, bad):.2f}"
                    f" median d2 bad {np.median(md[bad]):.1f} rest {np.median(md[~bad]):.1f}"
                )
    print("3. what the periods where k4 is twice as bad as alone are")
    for name, d in ALL:
        for split in ("man2", "shift"):
            r = _table(d, split, ["alone", "cv-k4", "joint"])
            if r is None:
                continue
            t, _P = r
            facts = _per_period_facts(json.loads(open(f"{d}/{split}.periods.json").read()))
            f = [
                facts.get((int(e), int(p)), {}) for e, p in zip(t["eng"], t["period"], strict=True)
            ]
            own = np.array([bool(x) and x["own_turn"] for x in f])
            ea, ek, ej = t["alone"][:, 0], t["cv-k4"][:, 0], t["joint"][:, 0]
            lr = np.log(ea / ek)
            bad = lr < -LOG2
            print(
                f"  {name:10s} {split:5s} n {lr.size:3d} twice-bad {int(bad.sum()):2d} (own turn {own[bad].mean():.2f}, all {own.mean():.2f})"
                f" | median error there: alone {np.median(ea[bad]):.3f} k4 {np.median(ek[bad]):.3f} joint {np.median(ej[bad]):.3f}"
                f" | elsewhere: alone {np.median(ea[~bad]):.3f} k4 {np.median(ek[~bad]):.3f} joint {np.median(ej[~bad]):.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
