# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261112-tl-search)
"""The evidence-scored search over manoeuvre histories against C″ read as a track.
Tuning seed 329, cut periods.

usage: tl_search.py <data dir> <count> <start> <out dir>
"""

import json, sys, time, numpy as np, torch

torch.set_default_dtype(torch.float64)
from tma2.timelate.arc import fit_arc, solve_arc, start_from_track
from tma2.timelate.bound import period_bound
from tma2.timelate.periods import iter_periods
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.retest import joint_fit, log_evidence
from tma2.timelate.score import row_errors, truth_rows
from tma2.timelate.search import candidate_set, evidence_search
from tma2.timelate.systems import c_parameters, solve_systems

prior = ManoeuvrePrior.from_ranges(json.load(open("configs/timelate/tl-ranges.json")))
p, c2 = c_parameters("configs/gateh/gh-a.json")
first, out = int(sys.argv[3]), sys.argv[4]
ps = list(iter_periods(sys.argv[1] + "/train.f32pack", first, int(sys.argv[2])))
t0 = time.time()
res = solve_systems(ps, ["one-leg", "c2-end-nofade"], p, c2)
print("layer solves", round(time.time() - t0), "s", flush=True)
names = ["chord-c2", "search-c2", "search-none", "search-pick", "cand-best3", "truth-map"]
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
    bound = period_bound(x)
    B.append(bound)
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < 0.5)
    nan = np.full((x.rows, 4), np.nan)
    cc = res["c2-end-nofade"][i]
    E["chord-c2"].append(row_errors(cc.states, tr))
    rec = {"ordinal": x.ordinal, "rows": x.rows, "n_valid": int(v.sum()), "det": int(det.sum())}
    # the true history fitted to the posterior (the reference; the only use of the truth)
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
    fm = joint_fit(
        pb, joint_fit(pb, th, spt, free_changes=kt).theta, spt, free_changes=kt, prior=prior
    )
    E["truth-map"].append(row_errors(fm.states, tr))
    rec["true"] = spt.tolist()
    rec["truth_ev"] = log_evidence(pb, fm, kt, prior)["total"]
    seen_all = []
    found = {}
    # start 1: C″'s transitions
    spc = np.array([[t[max(a_ - 1, 0)], t[b_]] for a_, b_ in cc.transitions if b_ > a_]).reshape(
        -1, 2
    )
    if np.isfinite(cc.states).all():
        f0, _, _ = solve_arc(t, ox, oy, z, v, sig, spc, cc.states)
        best, seen = evidence_search(pb, f0.theta, spc, prior)
        found["search-c2"] = best
        seen_all += seen
    # start 2: nothing (no layer, no truth)
    e = np.zeros((0, 2))
    b0 = None
    for c0 in (0.0, 1.57, 3.14, 4.71):
        q = np.array([ox[0] + 8000 * np.sin(z[v][0]), oy[0] + 8000 * np.cos(z[v][0]), c0, 5.0])
        f = fit_arc(t, ox, oy, z, v, sig, e, q)
        if b0 is None or f.cost < b0.cost:
            b0 = f
    best, seen = evidence_search(pb, b0.theta, e, prior)
    found["search-none"] = best
    seen_all += seen
    for n in ("search-c2", "search-none"):
        E[n].append(row_errors(found[n].fit.states, tr) if n in found else row_errors(nan, tr))
        if n in found:
            rec[n] = {
                "spans": found[n].fit.spans.tolist(),
                "kinds": found[n].kinds.tolist(),
                "evidence": found[n].evidence,
            }
    cands = candidate_set(seen_all, top=5)
    E["search-pick"].append(
        row_errors(cands[0][0].fit.states, tr) if cands else row_errors(nan, tr)
    )
    errs = [row_errors(h.fit.states, tr) for h, _ in cands]
    med = [float(np.median(er[det, 0])) if det.any() else float("nan") for er in errs]
    rec["candidates"] = [
        {
            "p": pr,
            "evidence": h.evidence,
            "manoeuvres": int(h.fit.spans.shape[0]),
            "err": m_,
            "spans": h.fit.spans.tolist(),
        }
        for (h, pr), m_ in zip(cands, med)
    ]
    rec["histories_evaluated"] = len(seen_all)
    k3 = int(np.nanargmin(med[:3])) if cands and det.any() else 0
    E["cand-best3"].append(errs[k3] if cands else row_errors(nan, tr))
    info.append(rec)
    print(
        i + 1,
        round(time.time() - t0),
        "s",
        len(seen_all),
        [round(c["p"], 2) for c in rec["candidates"]],
        flush=True,
    )
B = np.concatenate(B)
per = np.concatenate([np.full(x.rows, i) for i, x in enumerate(ps)])
np.savez_compressed(
    f"{out}/retest-{first}.npz", B=B, per=per, **{n: np.concatenate(E[n]) for n in names}
)
json.dump(info, open(f"{out}/retest-{first}.json", "w"))
print("done")
