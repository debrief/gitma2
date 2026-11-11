# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-diagnosis)
"""Spec 013 diagnosis: the reference solve's efficiency against the whole-period bound on
held-course periods (cut and whole) and on MAN2 periods by position and near turns.

    uv run python scripts/research/tl_reference_strata.py <dir with tl329/ and tl329h/>
"""

import sys, json, numpy as np, torch

torch.set_default_dtype(torch.float64)
from tma2.timelate.periods import iter_periods
from tma2.timelate.systems import solve_systems, c_parameters
from tma2.timelate.bound import period_bound
from tma2.timelate.score import truth_rows, row_errors, strata_of, Q

p, c2 = c_parameters("configs/gateh/gh-a.json")


def run(path, n, whole=False, label=""):
    ps = list(iter_periods(path, 0, n, whole=whole))
    res = solve_systems(ps, ["reference"], p, c2)
    E = []
    B = []
    ST = []
    INT = []
    for i, x in enumerate(ps):
        E.append(row_errors(res["reference"][i].states, truth_rows(x)))
        B.append(period_bound(x))
        ST.append(strata_of(x, x.rows))
        t = np.zeros(x.rows, bool)
        for s in x.spans():
            t[max(s["start_index"] - 6, 0) : s["end_index"] + 7] = True
        INT.append(t)
    E = np.concatenate(E)
    B = np.concatenate(B)
    ST = np.concatenate(ST)
    INT = np.concatenate(INT)
    det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)

    def eff(mask):
        ok = det & mask
        return [
            round(float(np.median(E[ok, c] / B[ok, c]) / Q), 2) for c in range(3)
        ] if ok.sum() > 50 else None, int(ok.sum())

    print(label, "periods", len(ps), "rows", E.shape[0], "determined", round(det.mean(), 3))
    print(
        "   all",
        eff(np.ones_like(det)),
        "| first leg",
        eff(ST == 0),
        "| interior",
        eff(ST == 1),
        "| last leg",
        eff(ST == 2),
    )
    print("   in or near a turn", eff(INT), "| away from turns", eff(~INT))


run(sys.argv[1] + "/tl329h/train.f32pack", 60, label="HELD COURSE cut")
run(sys.argv[1] + "/tl329h/train.f32pack", 60, whole=True, label="HELD COURSE whole")
run(sys.argv[1] + "/tl329/train.f32pack", 60, label="MAN2 cut")
