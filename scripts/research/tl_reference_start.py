# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261112-gt-val)
"""Is the true-history fit's efficiency below 1 because it starts at the truth? Tuning seed 329.
The same history (true spans and kinds), fitted to the bearings alone from the truth and from
starts moved off it (range and speed scaled about the ownship), by how well the row is determined.

usage: tl_reference_start.py <data dir> <start> <count>
"""

import sys, numpy as np
from tma2.timelate.arc import start_from_track
from tma2.timelate.bound import period_bound
from tma2.timelate.periods import iter_periods
from tma2.timelate.retest import joint_fit
from tma2.timelate.score import Q, row_errors, truth_rows

ps = list(iter_periods(sys.argv[1] + "/train.f32pack", int(sys.argv[2]), int(sys.argv[3])))
E = {"truth start": [], "start x0.7": [], "start x1.4": [], "best of three by cost": []}
B, moved = [], []
for x in ps:
    a, b = x.first, x.first + x.rows
    t = x.own[a:b, 0].astype(float) - float(x.own[a, 0])
    ox, oy = x.own[a:b, 1].astype(float), x.own[a:b, 2].astype(float)
    z, v = x.obs[a:b, 1].astype(float), x.obs[a:b, 2] != 0
    pb = (t, ox, oy, z, v, float(x.meta["parameters"]["noise_sigma_rad"]))
    tr = truth_rows(x)
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
    fits = {}
    for name, k in (("truth start", 1.0), ("start x0.7", 0.7), ("start x1.4", 1.4)):
        q = th.copy()
        q[0] = ox[0] + k * (th[0] - ox[0])
        q[1] = oy[0] + k * (th[1] - oy[0])
        q[3] = th[3] * k
        q[5::2] = th[5::2] * k
        fits[name] = joint_fit(pb, q, spt, free_changes=kt)
        E[name].append(row_errors(fits[name].states, tr)[::6])
    best = min(fits.values(), key=lambda f: f.cost)
    E["best of three by cost"].append(row_errors(best.states, tr)[::6])
    moved.append([fits[n].cost - fits["truth start"].cost for n in ("start x0.7", "start x1.4")])
    B.append(period_bound(x)[::6])
B = np.concatenate(B)
det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)
print("periods", len(ps), "determined scored rows", int(det.sum()))
for lab, k in (
    ("all determined", det),
    ("bound < 0.05", det & (B[:, 0] < 0.05)),
    ("0.05 to 0.2", det & (B[:, 0] >= 0.05) & (B[:, 0] < 0.2)),
    ("0.2 to 0.5", det & (B[:, 0] >= 0.2)),
):
    print(lab, "rows", int(k.sum()))
    for n, e in E.items():
        e = np.concatenate(e)
        ok = k & np.isfinite(e[:, 0])
        print(
            f"   {n:24s} range efficiency {np.median(e[ok, 0] / B[ok, 0]) / Q:.2f}   median error {np.median(e[ok, 0]):.4f}"
        )
m = np.array(moved)
print(
    "cost of the moved-start fits minus the truth-start fit: median",
    np.median(m).round(2),
    "share within 1:",
    round(float((np.abs(m) < 1).mean()), 2),
    "share above 10:",
    round(float((m > 10).mean()), 2),
)
