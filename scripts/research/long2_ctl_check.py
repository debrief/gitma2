"""Spec 024: does ``long.carry``'s ``ctl`` reproduce spec 023's runner (``run4``'s
``ctl-d1-q0.01``)? Window 1 of the 6-hour engagement, both run in this process.

    OMP_NUM_THREADS=1 uv run python scripts/research/long2_ctl_check.py

Result in experiments/20261117-long2/ctl-check.json.
"""

import json

import numpy as np

from tma2.long.carry import solve_window
from tma2.long.sim import generate
from tma2.long.timelate import chain, period_of, run_windows, settings_and_priors

cfg = json.load(open("configs/long/long.json"))
R = json.load(open(cfg["target_ranges"]))
e = generate(348, 0, 6, cfg, R)
s, pr, cp, c2 = settings_and_priors()
ch = chain(e, 7200, 1800)
for j in (1,):
    w = run_windows(e, ch[j : j + 1], s, pr, cp, c2)[0]
    p = period_of(e, ch[j][0], ch[j][1], j)
    mine = solve_window(p, pr, cp, c2, s, None)
    ox, oy = p.meta["window_origin_m"]
    m = mine["tracks"]["ctl-d1-q0.01"][::6].copy()
    m[:, 0] += ox
    m[:, 1] += oy
    print(
        j,
        "run4 ctl vs mine, same machine: max abs",
        np.nanmax(np.abs(w["tracks"]["ctl-d1-q0.01"] - m)),
        "declared",
        len(w["declared"]["ctl-d1-q0.01"]),
        len(mine["declared"]["ctl-d1-q0.01"]),
    )
    zz = np.load("experiments/20261117-long/raw/timelate-0.npz")
    print(
        "run4 here vs CI record",
        np.nanmax(np.abs(w["tracks"]["ctl-d1-q0.01"] - zz[f"w{j}_ctl-d1-q0.01"])),
    )
