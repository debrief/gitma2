# ruff: noqa  (a diagnostic script kept as run; spec 013, experiments/20261111-tl-diagnosis)
"""Is the reference's gap to the bound the price of its freer manoeuvre model? Fit the bound's
own model (initial state + one change per manoeuvre, generator kinematics) by Gauss-Newton on
whole MAN2 engagements and compare its efficiency with the chord reference's."""

import sys, numpy as np, torch

torch.set_default_dtype(torch.float64)
from tma2.references.crb import manoeuvre_model, _pos_vel, param_kinds
from tma2.timelate.periods import iter_periods
from tma2.timelate.bound import period_bound
from tma2.timelate.score import truth_rows, row_errors, Q
from tma2.timelate.systems import solve_systems, c_parameters

p, c2 = c_parameters("configs/gateh/gh-a.json")
ps = list(iter_periods(sys.argv[1] + "/tl329/train.f32pack", 0, int(sys.argv[2]), whole=True))


def states(theta, t, mans):
    return np.array([_pos_vel(theta, float(ti), mans) for ti in t])


def fit(x):
    m = x.meta
    t = x.own[:, 0].astype(float)
    ox = x.own[:, 1].astype(float)
    oy = x.own[:, 2].astype(float)
    z = x.obs[:, 1].astype(float)
    v = x.obs[:, 2] != 0
    sig = float(m["parameters"]["noise_sigma_rad"])
    c = x.tgt[0, 3]
    s = x.tgt[0, 4]
    theta, mans = manoeuvre_model(
        list(m["parameters"].get("target_manoeuvres") or []),
        float(x.tgt[0, 1]),
        float(x.tgt[0, 2]),
        float(s * np.sin(c)),
        float(s * np.cos(c)),
    )
    kinds = param_kinds(mans)
    steps = [1.0, 1.0, 1e-3, 1e-3] + [1e-6 if k == "course" else 1e-4 for k in kinds]

    def resid(th):
        st = states(th, t, mans)
        b = np.arctan2(st[:, 0] - ox, st[:, 1] - oy)
        return ((z - b + np.pi) % (2 * np.pi) - np.pi)[v] / sig

    lam = 1e-3
    r = resid(theta)
    cost = r @ r
    for it in range(12):
        J = np.empty((r.size, theta.size))
        for q in range(theta.size):
            up = theta.copy()
            up[q] += steps[q]
            dn = theta.copy()
            dn[q] -= steps[q]
            J[:, q] = (resid(up) - resid(dn)) / (2 * steps[q])
        A = J.T @ J
        g = -J.T @ r
        for _ in range(6):
            step = np.linalg.solve(A + lam * np.diag(np.diag(A)), g)
            r2 = resid(theta + step)
            c2_ = r2 @ r2
            if c2_ <= cost:
                theta = theta + step
                r = r2
                d = cost - c2_
                cost = c2_
                lam = max(lam / 10, 1e-12)
                break
            lam *= 10
        else:
            break
        if d < 1e-9 * max(cost, 1):
            break
    return states(theta, t, mans)


res = solve_systems(ps, ["reference"], p, c2)
Ek = []
Ec = []
B = []
for i, x in enumerate(ps):
    tr = truth_rows(x)
    B.append(period_bound(x))
    Ek.append(row_errors(fit(x), tr))
    Ec.append(row_errors(res["reference"][i].states, tr))
Ek = np.concatenate(Ek)
Ec = np.concatenate(Ec)
B = np.concatenate(B)
det = np.isfinite(B[:, 0]) & (B[:, 0] < 0.5)
eff = lambda E: [round(float(np.median(E[det, c] / B[det, c]) / Q), 2) for c in range(3)]
print("whole MAN2 engagements", len(ps), "rows", int(det.sum()))
print(
    "chord reference (times known, free velocity changes):",
    eff(Ec),
    "median range err",
    round(float(np.median(Ec[det, 0])), 4),
)
print(
    "kinematic fit (the bound's own model, started at the truth):",
    eff(Ek),
    "median range err",
    round(float(np.median(Ek[det, 0])), 4),
)
