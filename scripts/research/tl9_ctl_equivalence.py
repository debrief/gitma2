"""Spec 026 FR-001: carry.solve_ctl with no carried start reproduces run4's ctl-d1-q0.01.

    uv run python scripts/research/tl9_ctl_equivalence.py <split f32pack>

Run 2026-11-18 on two periods of spent seed 348 (time-late ranges): max |difference| 0.0 m,
identical declared spans.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

from tma2.timelate.carry import solve_ctl
from tma2.timelate.periods import iter_periods
from tma2.timelate.prior import ManoeuvrePrior
from tma2.timelate.run4 import run_shard4
from tma2.timelate.run8 import CTL, control_settings
from tma2.timelate.run9 import _problem
from tma2.timelate.systems import c_parameters, solve_systems

plan = json.loads(Path("configs/timelate/tl-k.json").read_text())
priors = {
    "v3": ManoeuvrePrior.from_ranges(json.loads(Path(plan["prior"]).read_text()), 3),
    "broad": ManoeuvrePrior.from_ranges(json.loads(Path(plan["prior_broad"]).read_text()), 3),
}
cp, c2 = c_parameters(plan["gh_plan"])
ps = list(iter_periods(sys.argv[1], 0, 4))
ps = sorted(ps, key=lambda p: p.rows)[:2]
for p in ps:
    t0 = time.time()
    arr, recs = run_shard4([p], priors, cp, c2, control_settings(plan["settings"]))
    t1 = time.time()
    ref = arr["trk_" + CTL].astype(float)
    pb, _ = _problem(p)
    cc = solve_systems([p], ["c2-end-nofade"], cp, c2)["c2-end-nofade"][0]
    t = pb[0]
    spc = np.array(
        [[t[max(a - 1, 0)], t[b]] for a, b in cc.transitions if b > a], dtype=float
    ).reshape(-1, 2)
    st, sp = solve_ctl(pb, priors, cc.states, spc, control_settings(plan["settings"]), None)
    t2 = time.time()
    print(
        p.ordinal,
        p.rows,
        f"run4 {t1 - t0:.0f}s mine {t2 - t1:.0f}s",
        "max|diff| m",
        float(np.nanmax(np.abs(st.astype(np.float32) - ref))),
        recs[0]["histories"][CTL]["spans"],
        (sp).tolist(),
    )
