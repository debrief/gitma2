# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-diagnosis)
"""Spec 013 diagnosis: what limits the reference on MAN2 periods: the priors, bearings inside
turns, or the pairing into 10-second points.

    uv run python scripts/research/tl_reference_variants.py <dir with tl329/>
"""

import sys, numpy as np, torch

torch.set_default_dtype(torch.float64)
from tma2.cli.oracle import run_layer
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import oracle_inputs
from tma2.timelate.periods import iter_periods
from tma2.timelate.points import fixed_points
from tma2.timelate.bound import period_bound
from tma2.timelate.track import track
from tma2.timelate.score import truth_rows, row_errors, Q
from tma2.timelate.systems import _times

ps = list(iter_periods(sys.argv[1] + "/tl329/train.f32pack", 0, 60))
B = np.concatenate([period_bound(x) for x in ps])
det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)
TR = [truth_rows(x) for x in ps]


def run(label, n=2, speed_prior=True, mask=False, **kw):
    pts = [fixed_points(x, n) for x in ps]
    E = []
    items = []
    for x, pt in zip(ps, pts):
        d = pt.data
        sp = [
            {**s, "start_index": s["start_index"] // n, "end_index": s["end_index"] // n}
            for s in x.spans()
        ]
        items.append(
            (
                d,
                d.n - 1,
                oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, d.n - 1, sp, speed_prior, mask),
            )
        )
    res = run_layer(PhysicsLayer(knots=16, **kw), items, max(pt.data.n for pt in pts))
    for b, (x, pt) in enumerate(zip(ps, pts)):
        st = track(
            res.theta[b].numpy(),
            pt.data.t[res.knots[b].numpy()],
            res.knot_weights[b].numpy(),
            _times(x),
        )
        E.append(row_errors(st, TR[b]))
    E = np.concatenate(E)
    print(
        f"{label:34}",
        [round(float(np.median(E[det, c] / B[det, c]) / Q), 2) for c in range(3)],
        "median range err",
        round(float(np.median(E[det, 0])), 4),
    )


run("baseline (pairs, priors)")
run("no speed prior", speed_prior=False)
run("mask turn bearings", mask=True)
run("weak ridge (tau_r 30)", tau_ridge_mps=30.0)
run("weak ridge + no speed prior", speed_prior=False, tau_ridge_mps=30.0)
run("weak ridge, no speed prior, mask", speed_prior=False, mask=True, tau_ridge_mps=30.0)
run("5-second rows (no pairing)", n=1)
