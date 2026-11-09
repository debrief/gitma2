"""Spec 010 FR-023: the references given the same classical statement as E (reported, not gated).

    uv run python scripts/research/g5_refs.py --scoring <score dir with errors.npz> [--names oracle,imm]

For each reference estimator, the sd^β per-cell temperature (spec 010 research R6.1: the truncated
form, cells of G5 minute × open at k, β per quantity from the grid) is fitted on its own stored
errors and sds and cross-fitted on the scoring rows: fitted on even-ordinal scenarios and applied
to odd ones, then the reverse. That is a fair comparison, not an in-sample one. The scoring rows
are not the tuning rows FR-023 names: spec 010 has no reference files on tuning rows. The
reference rows with no estimate state nothing (P = 0).

Prints JSON per reference: reliability, calibration slope, AUC of P, course log gain, coverage, the
share of rows stated, and P against the hit rate on the truth's settled and not-settled rows.
"""

from __future__ import annotations

import argparse
import json
import math

import numpy as np

GRID = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
XMAX = math.radians(45.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--names", default="oracle,imm")
    a = ap.parse_args()

    from tma2.calib import statement5 as s5
    from tma2.calib.statement import truncated_log_score
    from tma2.eval import calibration as ec

    z = np.load(f"{a.scoring}/errors.npz")
    minute = np.array([int(x) if x else 0 for x in z["slice_g5_minutes"]])
    open_ = z["slice_open_at_k"] == "open"
    settled = z["settled"]
    out = {}
    for name in a.names.split(","):
        c = z[f"cal_{name}"]
        n = c.shape[0]
        ok = (c[:, 7] > 0) & (c[:, 8] > 0) & np.isfinite(c[:, :6]).all(axis=1)
        inp = s5.Inputs(
            log_sd=np.nan_to_num(np.log(c[:, 3:6])),
            design=np.zeros((n, 1)),
            h=np.zeros((n, 1)),
            code=np.zeros((n, 1)),
            err=np.nan_to_num(c[:, 0:3]),
            sd=np.where(np.isfinite(c[:, 3:6]), c[:, 3:6], 1.0),
            ok=ok,
            minute=minute,
            open=open_,
        )
        stated = np.zeros((n, 4))  # x, p, q_r, q_s
        kappa = np.ones(n)
        for fold in (0, 1):
            fit = inp.select(z["ordinal"] % 2 == fold)
            app = z["ordinal"] % 2 != fold
            t = s5.fit_temperature5(fit, ["minute", "open"], GRID, XMAX)
            t["platt"] = list(s5.fit_platt(s5.apply_temperature5(t, fit), fit, XMAX))
            sub = inp.select(app)
            o = s5.apply_temperature5(t, sub).stated(sub.sd, XMAX, tuple(t["platt"]))
            stated[app] = np.stack([o["x"], o["p"], o["q_r"], o["q_s"]], axis=1)
            kappa[app] = o["kappa"]
        cal = c.copy()
        cal[:, 9:13] = np.where(ok[:, None], stated, 0.0)
        ls = truncated_log_score(c[:, 1], stated[:, 0], stated[:, 1], kappa)
        cal[:, 13] = np.where(ok, ls, -math.log(2 * math.pi))
        meas = {m.name: m.stat({"c": cal}) for m in ec.measures()}
        hit = ec._st_hit(cal)
        out[name] = {
            "stated_share": float(ok.mean()),
            "reliability": meas["statement_reliability"],
            "slope": meas["statement_slope"],
            "auc": meas["statement_auc"],
            "log_gain": meas["statement_course_log_gain"],
            "coverage95_log_range": meas["statement_coverage95_log_range"],
            "coverage95_speed": meas["statement_coverage95_speed"],
            "settled_p_hit": [float(cal[settled, 10].mean()), float(hit[settled].mean())],
            "not_settled_p_hit": [float(cal[~settled, 10].mean()), float(hit[~settled].mean())],
        }
        print(name, json.dumps(out[name]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
