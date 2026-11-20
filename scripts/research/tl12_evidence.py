"""Spec 031 diagnostic: beyond about 70 min the joint solve is worse than ``ctl`` alone. Is that
the search (the true history has more evidence than the history declared) or the evidence (the
declared history has as much or more)? Spec 013's check, per engagement.

    uv run python scripts/research/tl12_evidence.py <long config> <ordinal> <out.json>

For one engagement: the joint problem over its span (the gaps' bearings marked missing), `ctl`'s
declared history and its log evidence (as `run10._solve`, no carried state), and the true
history (structure and kinds from the truth) fitted with the same prior on the same edited
problem from `reference`'s neutral starts, with its log evidence. Both evidences are Laplace
totals under the prior the declared history won under.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from tma2.long.sim import generate
from tma2.long.timelate import period_of
from tma2.timelate.layout import layout, span
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.retest import log_evidence
from tma2.timelate.run2 import reference
from tma2.timelate.run8 import layout_options
from tma2.timelate.run9 import _problem
from tma2.timelate.run10 import _solve
from tma2.timelate.systems import c_parameters, solve_systems

PLAN = "configs/timelate/tl-q-hold-dev.json"


def main() -> int:
    cfg_path, ordinal, out = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])
    plan = json.loads(Path(PLAN).read_text())
    st = plan["settings"]
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
    pb, _t_abs = _problem(sp)
    t = pb[0]
    cc = solve_systems([sp], ["c2-end-nofade"], cp, c2)["c2-end-nofade"][0]
    spc = np.array(
        [[t[max(a - 1, 0)], t[b]] for a, b in cc.transitions if b > a], dtype=np.float64
    ).reshape(-1, 2)
    t0 = time.perf_counter()
    out_ = _solve(pb, priors, cc.states, spc, st, None)
    assert out_ is not None
    h, px, pr = out_
    secs = time.perf_counter() - t0
    tsp = [s for s in sp.spans() if s["end_index"] > s["start_index"]]
    spt = np.array(
        [[t[max(s["start_index"] - 1, 0)], t[s["end_index"]]] for s in tsp], dtype=np.float64
    ).reshape(-1, 2)
    kt = np.array(
        [[s["kind"] in ("course", "both"), s["kind"] in ("speed", "both")] for s in tsp], dtype=bool
    ).reshape(-1, 2)
    _held, _hf, hm = reference(px, spt, kt, pr)
    ev_true = log_evidence(px, hm, kt, pr)
    ev_decl = log_evidence(px, h.fit, h.kinds, pr)
    # a search started from the truth: does the declared history's evidence improve on it?
    rec = {
        "ordinal": ordinal,
        "gaps_min": [round(n * x.dt / 60) for _a, n in lay.gaps()],
        "true_manoeuvres": int(spt.shape[0]),
        "declared_manoeuvres": int(h.fit.spans.shape[0]),
        "evidence_declared": float(ev_decl["total"]),
        "evidence_declared_search": float(h.evidence),
        "evidence_true": float(ev_true["total"]),
        "parts_declared": {k: float(v) for k, v in ev_decl.items()},
        "parts_true": {k: float(v) for k, v in ev_true.items()},
        "true_spans_s": spt.tolist(),
        "true_kinds": kt.tolist(),
        "declared_spans_s": h.fit.spans.tolist(),
        "true_changes": [
            {k: m[k] for k in ("kind", "change", "rate", "change2", "rate2") if k in m}
            for m in sp.meta["parameters"]["target_manoeuvres"]
        ],
        "cost_declared": float(h.fit.cost),
        "cost_true": float(hm.cost),
        "bearings": int(pb[4].sum()),
        "search_seconds": round(secs, 1),
    }
    out.write_text(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
