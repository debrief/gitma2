"""Spec 031: the two development runs (ownship legs 20-40 min and 1-2 h) share engagements,
target tracks and layouts, so their later periods pair. Median errors of each system in each run,
and the share of periods with their own ownship turn.

    uv run python scripts/research/tl12_paired.py > experiments/20261120-tl12-hold-dev/paired.txt
"""

from __future__ import annotations

import json

import numpy as np

from tma2.timelate.study8 import UNDETERMINED, _per_period_facts, period_table

RUNS = {
    "legs 20-40 min": "experiments/20261120-tl12-dev",
    "legs 1-2 h": "experiments/20261120-tl12-hold-dev",
}


def main() -> int:
    tabs = {}
    for name, d in RUNS.items():
        z = dict(np.load(f"{d}/long.errors.npz"))
        span = z["bound_span"][:, 0].astype(np.float64)
        rows = np.isfinite(span) & (span < UNDETERMINED) & ~z["carry_first"].astype(bool)
        t = period_table(z, rows, ["alone", "joint", "cv-k4"])
        facts = _per_period_facts(json.loads(open(f"{d}/long.periods.json").read()))
        own = np.array(
            [
                bool(facts.get((int(e), int(p)))) and facts[(int(e), int(p))]["own_turn"]
                for e, p in zip(t["eng"], t["period"], strict=True)
            ]
        )
        tabs[name] = (t, own)
        med = {s: float(np.median(t[s][:, 0])) for s in ("alone", "joint", "cv-k4")}
        print(
            f"{name}: {t['eng'].size} later periods, own turn {own.mean():.2f};"
            f" median range error alone {med['alone']:.3f} joint {med['joint']:.3f} k4 {med['cv-k4']:.3f}"
        )
    (ta, _oa), (tb, _ob) = tabs.values()
    ka = {(int(e), int(p)): i for i, (e, p) in enumerate(zip(ta["eng"], ta["period"], strict=True))}
    kb = {(int(e), int(p)): i for i, (e, p) in enumerate(zip(tb["eng"], tb["period"], strict=True))}
    common = sorted(set(ka) & set(kb))
    print(f"periods scored in both runs: {len(common)}")
    for s in ("alone", "joint", "cv-k4"):
        r = np.array([np.log(tb[s][kb[k], 0] / ta[s][ka[k], 0]) for k in common])
        r = r[np.isfinite(r)]
        print(
            f"  {s}: error with long legs / with short legs, geometric mean {np.exp(r.mean()):.2f}, median {np.exp(np.median(r)):.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
