# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261112-tl-prior)
"""Does averaging over the histories the bearings cannot rule out help? From the re-test started
at nothing: the fitted history, the highest-evidence member of its neighbourhood, and the
evidence-weighted mean track. Tuning seed 329, cut periods. No C″ run (fast).

usage: tl_ensemble.py <data dir> <count> <start> <out dir>
"""

import json, sys, time, numpy as np
from tma2.timelate.arc import start_from_track, fit_arc
from tma2.timelate.retest import retest, ensemble, joint_fit, log_evidence
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.periods import iter_periods
from tma2.timelate.bound import period_bound
from tma2.timelate.score import truth_rows, row_errors

prior = ManoeuvrePrior.from_ranges(json.load(open("configs/timelate/tl-ranges.json")))
first, out = int(sys.argv[3]), sys.argv[4]
ps = list(iter_periods(sys.argv[1] + "/train.f32pack", first, int(sys.argv[2])))
names = ["retest-none", "ens-map", "ens-mean", "truth-fit"]
E = {n: [] for n in names}
B, info = [], []
t0 = time.time()
for i, x in enumerate(ps):
    a, b = x.first, x.first + x.rows
    t = x.own[a:b, 0].astype(float) - float(x.own[a, 0])
    ox, oy = x.own[a:b, 1].astype(float), x.own[a:b, 2].astype(float)
    z, v = x.obs[a:b, 1].astype(float), x.obs[a:b, 2] != 0
    pb = (t, ox, oy, z, v, float(x.meta["parameters"]["noise_sigma_rad"]))
    tr = truth_rows(x)
    B.append(period_bound(x))
    tt = np.stack(
        [tr[:, 0], tr[:, 1], tr[:, 3] * np.sin(tr[:, 2]), tr[:, 3] * np.cos(tr[:, 2])], axis=1
    )
    sp = [s for s in x.spans() if s["end_index"] > s["start_index"]]
    spt = np.array([[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp]).reshape(
        -1, 2
    )
    kt = np.array(
        [[q["kind"] in ("course", "both"), q["kind"] in ("speed", "both")] for q in sp], dtype=bool
    ).reshape(-1, 2)
    th = start_from_track(tt, t, spt)
    th[4:][~kt.reshape(-1)] = 0.0
    ft = joint_fit(pb, th, spt, free_changes=kt)
    E["truth-fit"].append(row_errors(ft.states, tr))
    # start: a one-leg arc fit from a nominal state on the first bearing (no truth, no layer)
    r0 = 8000.0
    th0 = np.array([ox[0] + r0 * np.sin(z[v][0]), oy[0] + r0 * np.cos(z[v][0]), 0.0, 5.0])
    e = np.zeros((0, 2))
    best = None
    for c0 in (0.0, 1.57, 3.14, 4.71):
        q = th0.copy()
        q[2] = c0
        f = fit_arc(t, ox, oy, z, v, pb[5], e, q)
        if best is None or f.cost < best.cost:
            best = f
    s = retest(pb, best.theta, e, 20.0)
    E["retest-none"].append(row_errors(s.states, tr))
    mem, w, mean = ensemble(pb, s, prior)
    E["ens-map"].append(row_errors(mem[int(np.argmax(w))].states, tr))
    E["ens-mean"].append(row_errors(mean, tr))
    info.append(
        {
            "ordinal": x.ordinal,
            "n_true": len(sp),
            "n_found": int(s.spans.shape[0]),
            "weights": [round(float(q), 4) for q in w],
            "sizes": [int(g.spans.shape[0]) for g in mem],
            "truth_ev": log_evidence(pb, ft, kt, prior)["total"],
        }
    )
    print(i + 1, round(time.time() - t0), "s", info[-1]["sizes"], info[-1]["weights"], flush=True)
B = np.concatenate(B)
per = np.concatenate([np.full(x.rows, i) for i, x in enumerate(ps)])
np.savez_compressed(
    f"{out}/retest-{first}.npz", B=B, per=per, **{n: np.concatenate(E[n]) for n in names}
)
json.dump(info, open(f"{out}/retest-{first}.json", "w"))
print("done")
