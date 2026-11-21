"""Spec 031 development readings beyond the generated tables: per later period, alone ÷ joint
and alone ÷ k4 by the length of the gap before it; the joint solve's cost and manoeuvre counts
against `ctl`'s cap of ten; gap manoeuvres found.

    uv run python scripts/research/tl12_readings.py experiments/<record> > <record>/readings.txt
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from tma2.timelate.study8 import UNDETERMINED, paired, period_table


def main() -> int:
    rec = Path(sys.argv[1])
    z = dict(np.load(rec / "long.errors.npz"))
    P = {e["ordinal"]: e for e in json.loads((rec / "long.periods.json").read_text())}
    span = z["bound_span"][:, 0].astype(np.float64)
    rows = np.isfinite(span) & (span < UNDETERMINED) & ~z["carry_first"].astype(bool)
    t = period_table(z, rows, ["alone", "joint", "cv-k4"])
    gap = np.array(
        [
            P[int(e)]["gaps"][int(p) - 1]["length_s"] / 60.0
            for e, p in zip(t["eng"], t["period"], strict=True)
        ]
    )
    print(
        "later periods by the gap before them (range; geometric mean [95% engagement interval], periods)"
    )
    for lo, hi in ((30, 50), (50, 70), (70, 91)):
        sel = (gap >= lo) & (gap < hi)
        for a, b in (("alone", "joint"), ("alone", "cv-k4"), ("cv-k4", "joint")):
            d = paired(t[a][sel], t[b][sel], t["eng"][sel], 0)
            print(
                f"  gap {lo}-{hi} min  {a}/{b}: {d['value']:.2f} [{d['lo']:.2f}, {d['hi']:.2f}] n {d['periods']}"
            )
    js = np.array([e["seconds"]["joint"] for e in P.values()])
    al = np.array([e["seconds"]["alone"] for e in P.values()])
    nman = np.array([len(e["joint"]) for e in P.values()])
    ntrue = np.array([len(e["true"]) for e in P.values()])
    print(
        f"joint solve seconds per engagement: median {np.median(js):.0f}, max {js.max():.0f};"
        f" alone (all periods) median {np.median(al):.0f}"
    )
    print(
        f"joint manoeuvres declared: median {np.median(nman):.0f}, at the cap of 10 in {int((nman >= 10).sum())}"
        f" of {nman.size} engagements; true in the span: median {np.median(ntrue):.0f}, over 10 in {int((ntrue > 10).sum())}"
    )
    g_true = sum(g["true"] for e in P.values() for g in e["gaps"])
    g_decl = sum(g["declared"] for e in P.values() for g in e["gaps"])
    print(f"gap manoeuvres: true {g_true}, declared by the joint solve {g_decl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
