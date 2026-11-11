# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261112-tl-prior)
"""Does Annex B's prior prefer the true manoeuvre history to the one the re-test found?
Evidence (Laplace) of both, on the periods of experiments/20261111-tl-retest/structures.json.

usage: tl_prior_test.py <data dir> <structures.json> <first> <count> <out.json>
"""

import json, sys, numpy as np
from tma2.timelate.arc import start_from_track
from tma2.timelate.periods import iter_periods
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.retest import Structure, joint_fit, log_evidence, choose_kinds
from tma2.timelate.score import truth_rows, row_errors
from tma2.timelate.bound import period_bound

prior = ManoeuvrePrior.from_ranges(json.load(open("configs/timelate/tl-ranges.json")))
recs = json.load(open(sys.argv[2]))[int(sys.argv[3]) : int(sys.argv[3]) + int(sys.argv[4])]
out = []
for rec in recs:
    x = list(iter_periods(sys.argv[1] + "/train.f32pack", rec["ordinal"], 1))[0]
    a, b = x.first, x.first + x.rows
    t = x.own[a:b, 0].astype(float) - float(x.own[a, 0])
    ox, oy = x.own[a:b, 1].astype(float), x.own[a:b, 2].astype(float)
    z, v = x.obs[a:b, 1].astype(float), x.obs[a:b, 2] != 0
    pb = (t, ox, oy, z, v, float(x.meta["parameters"]["noise_sigma_rad"]))
    tr = truth_rows(x)
    B = period_bound(x)
    det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)
    tt = np.stack(
        [tr[:, 0], tr[:, 1], tr[:, 3] * np.sin(tr[:, 2]), tr[:, 3] * np.cos(tr[:, 2])], axis=1
    )
    sp = [s for s in x.spans() if s["end_index"] > s["start_index"]]
    spt = np.array([[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in sp]).reshape(
        -1, 2
    )
    kt = np.array(
        [[s["kind"] in ("course", "both"), s["kind"] in ("speed", "both")] for s in sp], dtype=bool
    ).reshape(-1, 2)
    th = start_from_track(tt, t, spt)
    th[4:][~kt.reshape(-1)] = 0.0
    ft = joint_fit(pb, th, spt, free_changes=kt)
    row = {"ordinal": rec["ordinal"], "det": int(det.sum()), "n_true": len(sp)}
    row["truth"] = log_evidence(pb, ft, kt, prior)
    row["truth_err"] = float(np.median(row_errors(ft.states, tr)[det, 0])) if det.any() else None
    for key in ("retest_c2", "retest_none"):
        if key not in rec:
            continue
        spans = np.array(rec[key]["spans"]).reshape(-1, 2)
        # refit from the re-test's own solution is not stored: restart from the truth track on
        # its spans (favours the re-test's history if anything), then choose kinds by evidence
        g = joint_fit(pb, start_from_track(tt, t, spans), spans)
        g, kinds, ev = choose_kinds(pb, g, prior)
        row[key] = ev
        row[key + "_n"] = int(spans.shape[0])
        row[key + "_err"] = (
            float(np.median(row_errors(g.states, tr)[det, 0])) if det.any() else None
        )
    out.append(row)
    print(
        row["ordinal"], row["n_true"], {k: round(v, 1) for k, v in row["truth"].items()}, flush=True
    )
    for key in ("retest_c2", "retest_none"):
        if key in row:
            print(
                "   ",
                key,
                row[key + "_n"],
                {k: round(v, 1) for k, v in row[key].items()},
                "err",
                row[key + "_err"],
                "truth err",
                row["truth_err"],
                flush=True,
            )
json.dump(out, open(sys.argv[5], "w"))
