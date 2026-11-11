# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-retest)
"""The full-period re-test on the arc cost, from C″'s transitions and from nothing, against the
arc solve on the true times. Tuning seed 329, cut periods.

usage: tl_retest.py <data dir> <count> <start> <threshold> <out dir>
"""

import json, sys, time, numpy as np, torch

torch.set_default_dtype(torch.float64)
from tma2.timelate.arc import solve_arc, start_from_track, fit_arc
from tma2.timelate.retest import retest, joint_fit, log_evidence, choose_kinds
from tma2.timelate.prior import ManoeuvrePrior

prior = ManoeuvrePrior.from_ranges(json.load(open("configs/timelate/tl-ranges.json")))
from tma2.timelate.periods import iter_periods
from tma2.timelate.bound import period_bound
from tma2.timelate.score import truth_rows, row_errors
from tma2.timelate.systems import solve_systems, c_parameters

p, c2 = c_parameters("configs/gateh/gh-a.json")
first, thr, out = int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
ps = list(iter_periods(sys.argv[1] + "/train.f32pack", first, int(sys.argv[2])))
t0 = time.time()
res = solve_systems(ps, ["reference", "one-leg", "c2-end-nofade"], p, c2)
names = [
    "chord-true",
    "arc-true",
    "chord-c2",
    "retest-c2",
    "retest-none",
    "truth-fit",
    "retest-c2-k",
    "retest-none-k",
]
E = {n: [] for n in names}
B, info = [], []
for i, x in enumerate(ps):
    a, b = x.first, x.first + x.rows
    t = x.own[a:b, 0].astype(float) - float(x.own[a, 0])
    ox, oy = x.own[a:b, 1].astype(float), x.own[a:b, 2].astype(float)
    z, v = x.obs[a:b, 1].astype(float), x.obs[a:b, 2] != 0
    sig = float(x.meta["parameters"]["noise_sigma_rad"])
    pb = (t, ox, oy, z, v, sig)
    tr = truth_rows(x)
    B.append(period_bound(x))
    nan = np.full((x.rows, 4), np.nan)
    ref, one, cc = res["reference"][i].states, res["one-leg"][i].states, res["c2-end-nofade"][i]
    E["chord-true"].append(row_errors(ref, tr))
    E["chord-c2"].append(row_errors(cc.states, tr))
    sp_true = [s for s in x.spans() if s["end_index"] > s["start_index"]]
    spt = np.array([[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp_true]).reshape(
        -1, 2
    )
    seed = ref if np.isfinite(ref).all() else one
    structs = {}
    rec = {"ordinal": x.ordinal, "rows": x.rows, "true": spt.tolist(), "n_valid": int(v.sum())}
    if np.isfinite(seed).all():
        at, _, _ = solve_arc(t, ox, oy, z, v, sig, spt, seed)
        E["arc-true"].append(row_errors(at.states, tr))
        rec["cost_true"] = at.cost
    else:
        E["arc-true"].append(row_errors(nan, tr))
    spc = np.array([[t[max(a_ - 1, 0)], t[b_]] for a_, b_ in cc.transitions if b_ > a_]).reshape(
        -1, 2
    )
    rec["c2"] = spc.tolist()
    if np.isfinite(cc.states).all():
        f0, _, _ = solve_arc(t, ox, oy, z, v, sig, spc, cc.states)
        s = retest(pb, f0.theta, spc, thr)
        E["retest-c2"].append(row_errors(s.states, tr))
        structs["retest_c2"] = s
        rec["retest_c2"] = {
            "spans": s.spans.tolist(),
            "cost": s.cost,
            "log": s.log,
            "cost_start": f0.cost,
        }
    else:
        E["retest-c2"].append(row_errors(nan, tr))
    if np.isfinite(one).all():
        e = np.zeros((0, 2))
        f0 = fit_arc(t, ox, oy, z, v, sig, e, start_from_track(one, t, e))
        s = retest(pb, f0.theta, e, thr)
        E["retest-none"].append(row_errors(s.states, tr))
        structs["retest_none"] = s
        rec["retest_none"] = {
            "spans": s.spans.tolist(),
            "cost": s.cost,
            "log": s.log,
            "cost_start": f0.cost,
        }
    else:
        E["retest-none"].append(row_errors(nan, tr))
    # evidence under Annex B's prior: the true history (fitted from the truth, times free) and
    # each re-test history with its kinds chosen by evidence
    tt = np.stack(
        [tr[:, 0], tr[:, 1], tr[:, 3] * np.sin(tr[:, 2]), tr[:, 3] * np.cos(tr[:, 2])], axis=1
    )
    kt = np.array(
        [[q["kind"] in ("course", "both"), q["kind"] in ("speed", "both")] for q in sp_true],
        dtype=bool,
    ).reshape(-1, 2)
    th = start_from_track(tt, t, spt)
    th[4:][~kt.reshape(-1)] = 0.0
    ft = joint_fit(pb, th, spt, free_changes=kt)
    rec["truth_ev"] = log_evidence(pb, ft, kt, prior)
    E["truth-fit"].append(row_errors(ft.states, tr))
    for key, name in (("retest_c2", "retest-c2-k"), ("retest_none", "retest-none-k")):
        if key in rec:
            g, kinds, ev = choose_kinds(pb, structs[key], prior)
            rec[key]["ev"] = ev
            rec[key]["kinds"] = kinds.tolist()
            E[name].append(row_errors(g.states, tr))
        else:
            E[name].append(row_errors(nan, tr))
    info.append(rec)
    print(i + 1, round(time.time() - t0), "s", flush=True)
B = np.concatenate(B)
per = np.concatenate([np.full(x.rows, i) for i, x in enumerate(ps)])
np.savez_compressed(
    f"{out}/retest-{first}.npz", B=B, per=per, **{n: np.concatenate(E[n]) for n in names}
)
json.dump(info, open(f"{out}/retest-{first}.json", "w"))
print("done")
