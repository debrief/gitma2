"""Spec 033 follow-up (owner option 3): the evidence check repeated with everything inside one
job, so histories and errors come from the same machine (the first diagnostic paired a re-run's
histories with another run's errors).

    uv run python scripts/research/tl13_evidence2.py <long config> <ordinal> <scored errors.npz> <out.json>

For one engagement, in one process:
- `ctl`'s declared joint history over the span (gaps' bearings masked) and `ctl` alone on each
  period, both as `run10._solve` without a carried state;
- three more structures fitted with the prior on the same edited joint problem from neutral starts
  (`run2.reference`): the true history (manoeuvres cut by the span's start left out); the declared
  history refitted the same way (so the two compare like with like); and the declared manoeuvres
  outside the gaps plus the true manoeuvres inside them (the panel's "true structure in the gap
  only");
- Laplace log evidence of each under the prior the declared history won;
- per later period, median relative range error of each system on the scored run's rows (every
  sixth row with span bound below 0.5, read from the scored run's ``errors.npz``).
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

from tma2.long.sim import generate
from tma2.long.timelate import period_of
from tma2.timelate.layout import layout, period, span
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.retest import log_evidence
from tma2.timelate.run2 import reference
from tma2.timelate.run8 import layout_options
from tma2.timelate.run9 import _problem
from tma2.timelate.run10 import _solve
from tma2.timelate.score import row_errors, truth_rows
from tma2.timelate.study8 import UNDETERMINED
from tma2.timelate.systems import c_parameters, solve_systems

PLAN = "configs/timelate/tl-q-hold-dev.json"


def _cpu() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def _ctl(p, priors, cp, c2, st):  # type: ignore[no-untyped-def]
    pb, _t = _problem(p)
    t = pb[0]
    cc = solve_systems([p], ["c2-end-nofade"], cp, c2)["c2-end-nofade"][0]
    spc = np.array(
        [[t[max(a - 1, 0)], t[b]] for a, b in cc.transitions if b > a], dtype=np.float64
    ).reshape(-1, 2)
    out = _solve(pb, priors, cc.states, spc, st, None)
    assert out is not None
    return out


def main() -> int:
    cfg_path, ordinal, scored, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    plan = json.loads(Path(PLAN).read_text())
    st = plan["settings"]
    every = int(st["score_every"])
    priors = {
        "v3": ManoeuvrePrior.from_ranges(json.loads(Path(plan["prior"]).read_text()), 3),
        "broad": ManoeuvrePrior.from_ranges(json.loads(Path(plan["prior_broad"]).read_text()), 3),
    }
    cp, c2 = c_parameters(plan["gh_plan"])
    cfg = json.loads(Path(cfg_path).read_text())
    rng = json.loads(Path(cfg["target_ranges"]).read_text())
    e = generate(int(cfg["seed"]), ordinal, float(cfg["hours"][0]), cfg, rng)
    x = period_of(e, 0, e.samples, ordinal)
    lay = layout(np.uint64(int(x.meta["seed"])), x.rows, x.dt, **layout_options(st))
    assert lay is not None
    sp = span(x, lay, masked=True)
    t0 = time.perf_counter()
    h, px, pr = _ctl(sp, priors, cp, c2, st)
    secs_joint = time.perf_counter() - t0
    t = px[0]
    # the true structure (cut-at-start manoeuvres left out) and the gaps in the span's time
    every_true = [s for s in sp.spans() if s["end_index"] > s["start_index"]]
    tsp = [s for s in every_true if not s["began_before"]]
    spt = np.array(
        [[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in tsp], dtype=np.float64
    ).reshape(-1, 2)
    kt = np.array(
        [[s["kind"] in ("course", "both"), s["kind"] in ("speed", "both")] for s in tsp], dtype=bool
    ).reshape(-1, 2)
    gaps_t = [
        (t[a - lay.first], t[min(a + n, lay.first + lay.rows) - 1 - lay.first])
        for a, n in lay.gaps()
    ]

    def in_gap(s0: float, s1: float) -> bool:
        mid = 0.5 * (s0 + s1)
        return any(g0 <= mid <= g1 for g0, g1 in gaps_t)

    dsp, dk = h.fit.spans, h.kinds
    keep = np.array([not in_gap(a, b) for a, b in dsp], dtype=bool)
    tin = np.array([in_gap(a, b) for a, b in spt], dtype=bool)
    gsp = np.concatenate([dsp[keep], spt[tin]]).reshape(-1, 2)
    gk = np.concatenate([dk[keep], kt[tin]]).reshape(-1, 2)
    order = np.argsort(gsp[:, 0], kind="stable")
    gsp, gk = gsp[order], gk[order]

    fits = {}
    for name, s_, k_ in (("true", spt, kt), ("declared_refit", dsp, dk), ("gap_true", gsp, gk)):
        _held, _f, post = reference(px, s_, k_, pr)
        fits[name] = (post, k_, float(log_evidence(px, post, k_, pr)["total"]))
    ev_decl = float(log_evidence(px, h.fit, h.kinds, pr)["total"])

    z = dict(np.load(scored))
    tracks = {"joint": h.fit.states, **{n: f[0].states for n, f in fits.items()}}
    periods_out = []
    for i, (a, n) in enumerate(lay.periods):
        if i == 0:
            continue
        p = period(x, a, n)
        tr = truth_rows(p)
        pick = np.arange(0, n, every)
        sel = (z["eng"] == ordinal) & (z["period"] == i)
        bound = z["bound_span"][sel][:, 0].astype(np.float64)
        if bound.size != pick.size:
            raise ValueError(
                f"engagement {ordinal} period {i}: {bound.size} scored rows against {pick.size}"
            )
        rows = np.isfinite(bound) & (bound < UNDETERMINED)
        if not rows.any():
            continue
        off = a - lay.first
        meds = {}
        for name, states in tracks.items():
            err = row_errors(states[off : off + n], tr)[pick][:, 0]
            meds[name] = float(np.median(err[rows]))
        ha, _pa, _pra = _ctl(p, priors, cp, c2, st)
        meds["alone"] = float(np.median(row_errors(ha.fit.states, tr)[pick][:, 0][rows]))
        gap_s = float(lay.gaps()[i - 1][1] * x.dt)
        periods_out.append(
            {
                "period": i,
                "gap_s": gap_s,
                "own_turn": bool(p.ownship_turns()),
                "scored_rows": int(rows.sum()),
                "median_range_error": meds,
            }
        )
    rec = {
        "ordinal": ordinal,
        "cpu_model": _cpu(),
        "gaps_min": [round(nn * x.dt / 60) for _a, nn in lay.gaps()],
        "cut_at_start": len(every_true) - len(tsp),
        "manoeuvres": {
            "true": int(spt.shape[0]),
            "declared": int(dsp.shape[0]),
            "gap_true": int(gsp.shape[0]),
            "true_in_gaps": int(tin.sum()),
            "declared_in_gaps": int((~keep).sum()),
        },
        "evidence": {"declared": ev_decl, **{n: f[2] for n, f in fits.items()}},
        "periods": periods_out,
        "joint_seconds": round(secs_joint, 1),
    }
    out.write_text(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
