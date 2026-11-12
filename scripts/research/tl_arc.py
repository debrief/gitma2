# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-arc)
"""How much of the chord reference's gap to the bound does the arc-model solve recover, and how
much of that survives when the manoeuvre's kind is not told? Tuning seed 329, cut periods.

usage: tl_arc.py <data dir> <count> [whole] [start]
"""

import json, sys, time, numpy as np, torch

torch.set_default_dtype(torch.float64)
from tma2.timelate.arc import solve_arc
from tma2.timelate.periods import iter_periods
from tma2.timelate.bound import period_bound
from tma2.timelate.score import truth_rows, row_errors, Q
from tma2.timelate.systems import solve_systems, c_parameters

p, c2 = c_parameters("configs/gateh/gh-a.json")
whole = len(sys.argv) > 3 and sys.argv[3] == "whole"
start = int(sys.argv[4]) if len(sys.argv) > 4 else 0
ps = list(iter_periods(sys.argv[1] + "/train.f32pack", start, int(sys.argv[2]), whole=whole))
THR = 6.63  # chi-square(1) at 1%


def arrays(x):
    a, b = x.first, x.first + x.rows
    t = x.own[a:b, 0].astype(float) - float(x.own[a, 0])
    return (
        t,
        x.own[a:b, 1].astype(float),
        x.own[a:b, 2].astype(float),
        x.obs[a:b, 1].astype(float),
        x.obs[a:b, 2] != 0,
        float(x.meta["parameters"]["noise_sigma_rad"]),
    )


def spans_true(x, t):
    sp = [s for s in x.spans() if s["end_index"] > s["start_index"]]
    kinds = [s["kind"] for s in sp]
    return np.array([[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp]).reshape(
        -1, 2
    ), kinds


def spans_rows(trs, t):
    return np.array([[t[max(a - 1, 0)], t[b]] for a, b in trs if b > a]).reshape(-1, 2)


t0 = time.time()
res = solve_systems(ps, ["reference", "one-leg", "c2-end-nofade"], p, c2)
print("layer solves", round(time.time() - t0), "s", flush=True)
names = ["chord-true", "arc-kind-true", "arc-true", "chord-c2", "arc-c2", "one-leg"]
E = {n: [] for n in names}
B = []
kind_ok = [0, 0]
nfits = []
for i, x in enumerate(ps):
    tr = truth_rows(x)
    B.append(period_bound(x))
    t, ox, oy, z, v, sig = arrays(x)
    ref = res["reference"][i].states
    E["chord-true"].append(row_errors(ref, tr))
    E["one-leg"].append(row_errors(res["one-leg"][i].states, tr))
    sp, kinds = spans_true(x, t)
    nan = np.full((x.rows, 4), np.nan)
    seed = ref if np.isfinite(ref).all() else res["one-leg"][i].states
    if np.isfinite(seed).all():
        tf = np.array(
            [[k in (0, 2, "course", "both"), k in (1, 2, "speed", "both")] for k in kinds],
            dtype=bool,
        ).reshape(-1, 2)
        told, _, n1 = solve_arc(t, ox, oy, z, v, sig, sp, seed, tf)
        E["arc-kind-true"].append(row_errors(told.states, tr))
        sel, free, n2 = solve_arc(t, ox, oy, z, v, sig, sp, seed)
        E["arc-true"].append(row_errors(sel.states, tr))
        nfits.append(n2)
        for a_, b_ in zip(free, tf):
            kind_ok[1] += 1
            kind_ok[0] += int((a_ == b_).all())
    else:
        E["arc-kind-true"].append(row_errors(nan, tr))
        E["arc-true"].append(row_errors(nan, tr))
    cc = res["c2-end-nofade"][i]
    E["chord-c2"].append(row_errors(cc.states, tr))
    spc = spans_rows(cc.transitions, t)
    if np.isfinite(cc.states).all():
        s2, _, _ = solve_arc(t, ox, oy, z, v, sig, spc, cc.states)
        E["arc-c2"].append(row_errors(s2.states, tr))
    else:
        E["arc-c2"].append(row_errors(nan, tr))
    print(i + 1, round(time.time() - t0), "s", flush=True)

B = np.concatenate(B)
det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)
out = {
    "periods": len(ps),
    "whole": whole,
    "determined_rows": int(det.sum()),
    "threshold": THR,
    "kind_selected_correctly": kind_ok,
    "systems": {},
}
per = np.concatenate([np.full(x.rows, i) for i, x in enumerate(ps)])
for n in names:
    e = np.concatenate(E[n])
    ok = det & np.isfinite(e[:, 0])
    eff = [round(float(np.median(e[ok, c] / B[ok, c]) / Q), 2) for c in range(3)]
    pm = [np.median(e[ok & (per == i), 0]) for i in range(len(ps)) if (ok & (per == i)).any()]
    out["systems"][n] = {
        "efficiency": eff,
        "median_range_error_rows": round(float(np.median(e[ok, 0])), 4),
        "median_of_period_medians": round(float(np.median(pm)), 4),
        "p90_of_period_medians": round(float(np.quantile(pm, 0.9)), 4),
        "rows_answered": round(float(ok.sum() / det.sum()), 3),
    }
    print(n, out["systems"][n], flush=True)
print("kind selected correctly", kind_ok)
np.savez_compressed(
    sys.argv[1] + f"/arc-{'whole' if whole else 'cut'}-{start}.npz",
    B=B,
    per=per,
    **{n: np.concatenate(E[n]) for n in names},
)
json.dump(
    out, open(sys.argv[1] + f"/arc-{'whole' if whole else 'cut'}-{start}.json", "w"), indent=1
)
