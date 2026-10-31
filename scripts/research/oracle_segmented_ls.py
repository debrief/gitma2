#!/usr/bin/env python3
"""Upper bound for a "segment, then solve" tracker on gitma's phase-4 data.

Question: if a learned component could tell a batch least-squares solver *when* the target
manoeuvred (and nothing else), how would a piecewise-constant-velocity batch fit compare with
gitma's frozen IMM reference and with plain batch least squares on the G5 rows?

Inputs (produced with gitma's own CLIs, see docs/research/02-oracle-segmentation.md):
  --truth   <split.ndjson>   gitma scenarios (generator 0.5.0)
  --imm     <imm.ndjson>     tma-track --filter imm ... predictions (frozen reference settings)
  --lsq     <lsq.ndjson>     tma-solve --per-timestep predictions

The oracle solver is causal: at gate row k it uses bearings 0..k and the manoeuvre spans whose
start_index <= k. Velocity is constant between knots placed at the start and end of each span
(a rate-limited turn is approximated by its chord). A weak ridge prior ties each new segment's
velocity to the previous one, so a leg that is only a few samples old does not blow up.

Pure numpy/scipy; no gitma code is imported. Run with `python3 -I`.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

GATE_OFFSETS_S = (300, 600, 900, 1200)
SIGMA_1DEG = math.radians(1.0)
GRID_RANGES_M = np.geomspace(1000, 40000, 12)
GRID_COURSES = np.linspace(0, 2 * math.pi, 8, endpoint=False)
GRID_SPEEDS = (2.0, 5.0, 9.0)


def wrap(a: np.ndarray) -> np.ndarray:
    return (a + math.pi) % (2 * math.pi) - math.pi


@dataclass
class Scenario:
    index: int
    t: np.ndarray  # s
    ox: np.ndarray
    oy: np.ndarray
    tx: np.ndarray
    ty: np.ndarray
    tvx: np.ndarray
    tvy: np.ndarray
    z: np.ndarray
    valid: np.ndarray
    sigma: float
    zig_index: int
    spans: list[tuple[int, int, str]]


def load_scenarios(path: str) -> list[Scenario]:
    out: list[Scenario] = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("record") != "scenario":
                continue
            md = rec["metadata"]
            own = rec["ownship"]["states"]
            tgt = rec["target"]["states"]
            obs = rec["observations"]
            tv = np.array(
                [
                    (
                        s["speed_mps"] * math.sin(s["course_rad"]),
                        s["speed_mps"] * math.cos(s["course_rad"]),
                    )
                    for s in tgt
                ]
            )
            out.append(
                Scenario(
                    index=md["index"],
                    t=np.array([s["timestamp_s"] for s in own], dtype=float),
                    ox=np.array([s["x_m"] for s in own]),
                    oy=np.array([s["y_m"] for s in own]),
                    tx=np.array([s["x_m"] for s in tgt]),
                    ty=np.array([s["y_m"] for s in tgt]),
                    tvx=tv[:, 0],
                    tvy=tv[:, 1],
                    z=np.array([o["bearing_rad"] for o in obs]),
                    valid=np.array([o["valid"] for o in obs], dtype=bool),
                    sigma=float(md["parameters"]["noise_sigma_rad"]),
                    zig_index=int(md["zig_index"]),
                    spans=[
                        (int(m["start_index"]), int(m["end_index"]), m["kind"])
                        for m in md.get("manoeuvres", [])
                    ],
                )
            )
    return out


def load_predictions(path: str) -> dict[int, dict[float, dict]]:
    """scenario_index -> timestamp -> row."""
    out: dict[int, dict[float, dict]] = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("record") != "prediction":
                continue
            out[rec["scenario_index"]] = {float(r["timestamp_s"]): r for r in rec["rows"]}
    return out


def segment_matrix(t: np.ndarray, knots: list[float]) -> np.ndarray:
    """A[i, j] = time the target spent in segment j up to t_i (segments split at knots)."""
    edges = [-math.inf] + knots + [math.inf]
    cols = []
    for j in range(len(edges) - 1):
        lo, hi = edges[j], edges[j + 1]
        lo_eff = 0.0 if lo == -math.inf else lo
        cols.append(np.clip(np.minimum(t, hi) - lo_eff, 0.0, None) if hi != -math.inf else t)
    return np.stack(cols, axis=1)


def solve_segments(
    sc: Scenario,
    k: int,
    knots_idx: list[int],
    prior_sd_mps: float,
    speed_prior_sd_mps: float,
    course_spans: list[tuple[int, int]],
) -> tuple[np.ndarray, list[float]] | None:
    sel = np.arange(k + 1)[sc.valid[: k + 1]]
    if sel.size < 6:
        return None
    t, z = sc.t[sel], sc.z[sel]
    ox, oy = sc.ox[sel], sc.oy[sel]
    knots = sorted({float(sc.t[i]) for i in knots_idx if 0 < i <= k})
    A = segment_matrix(t, knots)  # n x S
    S = A.shape[1]
    sigma = max(sc.sigma, 1e-4)
    # Segment pairs (before, after) across a course-only manoeuvre: speed is expected to carry over.
    speed_pairs: list[tuple[int, int]] = []
    if speed_prior_sd_mps > 0:
        for s_idx, e_idx in course_spans:
            if s_idx <= k and 0 < s_idx:
                ts, te = float(sc.t[s_idx]), float(sc.t[min(e_idx, k)])
                a = int(
                    np.searchsorted(np.array(knots), ts, side="left")
                )  # segment ending at the span start
                b = int(np.searchsorted(np.array(knots), te, side="right")) if te > ts else a + 1
                if 0 <= a < S and 0 <= b < S and a != b:
                    speed_pairs.append((a, b))

    def predict(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x0, y0 = p[0], p[1]
        v = p[2:].reshape(S, 2)
        qx = x0 + A @ v[:, 0]
        qy = y0 + A @ v[:, 1]
        return qx - ox, qy - oy

    def residuals(p: np.ndarray) -> np.ndarray:
        dx, dy = predict(p)
        r = wrap(z - np.arctan2(dx, dy)) / sigma
        v = p[2:].reshape(S, 2)
        prior = (v[1:] - v[:-1]).ravel() / prior_sd_mps if S > 1 else np.zeros(0)
        sp = np.array(
            [(np.hypot(*v[b]) - np.hypot(*v[a])) / speed_prior_sd_mps for a, b in speed_pairs]
        )
        return np.concatenate([r, prior, sp])

    def jac(p: np.ndarray) -> np.ndarray:
        dx, dy = predict(p)
        rho2 = dx * dx + dy * dy
        dhx, dhy = dy / rho2, -dx / rho2  # d bearing / d(qx, qy)
        J = np.zeros((z.size + (2 * (S - 1) if S > 1 else 0), 2 + 2 * S))
        J[: z.size, 0] = -dhx / sigma
        J[: z.size, 1] = -dhy / sigma
        for j in range(S):
            J[: z.size, 2 + 2 * j] = -dhx * A[:, j] / sigma
            J[: z.size, 3 + 2 * j] = -dhy * A[:, j] / sigma
        for j in range(S - 1):
            row = z.size + 2 * j
            J[row, 2 + 2 * (j + 1)] = 1 / prior_sd_mps
            J[row, 2 + 2 * j] = -1 / prior_sd_mps
            J[row + 1, 3 + 2 * (j + 1)] = 1 / prior_sd_mps
            J[row + 1, 3 + 2 * j] = -1 / prior_sd_mps
        return J

    # Stage 1: single constant-velocity fit from gitma's grid (best grid point, then LM).
    b0 = z[0]
    best, best_cost = None, math.inf
    for r0 in GRID_RANGES_M:
        for c in GRID_COURSES:
            for s in GRID_SPEEDS:
                p = np.array(
                    [ox[0] + r0 * math.sin(b0), oy[0] + r0 * math.cos(b0)]
                    + [s * math.sin(c), s * math.cos(c)] * S
                )
                cost = float(np.sum(residuals(p) ** 2))
                if cost < best_cost:
                    best, best_cost = p, cost
    assert best is not None
    try:
        res = least_squares(
            residuals, best, jac=(jac if not speed_pairs else "2-point"), method="lm", max_nfev=400
        )
    except Exception:
        return None
    p = res.x
    v = p[2:].reshape(S, 2)
    # Estimate at row k (the last selected sample may be earlier if k was a dropout).
    tk = sc.t[k]
    Ak = segment_matrix(np.array([tk]), knots)[0]
    est_x = p[0] + Ak @ v[:, 0]
    est_y = p[1] + Ak @ v[:, 1]
    seg = int(np.searchsorted(np.array(knots), tk, side="right")) if knots else 0
    return np.array([est_x, est_y, v[seg, 0], v[seg, 1]]), knots


def errors(
    sc: Scenario, k: int, x: float, y: float, vx: float, vy: float
) -> tuple[float, float, float]:
    r_true = math.hypot(sc.tx[k] - sc.ox[k], sc.ty[k] - sc.oy[k])
    r_est = math.hypot(x - sc.ox[k], y - sc.oy[k])
    c_true = math.atan2(sc.tvx[k], sc.tvy[k])
    c_est = math.atan2(vx, vy)
    s_true = math.hypot(sc.tvx[k], sc.tvy[k])
    s_est = math.hypot(vx, vy)
    return (
        abs(r_est - r_true) / r_true,
        abs(wrap(np.array([c_est - c_true]))[0]) * 180 / math.pi,
        abs(s_est - s_true) / 0.514444,
    )


def settled(sc: Scenario, k: int) -> bool:
    dt = sc.t[1] - sc.t[0]
    for s, e, _ in sc.spans:
        if s <= k < e:
            return False
    ended = [e for s, e, _ in sc.spans if e <= k]
    if not ended:
        return True
    return (k - max(ended)) * dt >= 300


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--imm", required=True)
    ap.add_argument("--lsq", required=True)
    ap.add_argument(
        "--prior-sd",
        type=float,
        default=3.0,
        help="ridge sd (m/s) tying a new segment's velocity to the last",
    )
    ap.add_argument(
        "--speed-prior-sd",
        type=float,
        default=0.0,
        help="if > 0, sd (m/s) of a prior that speed is unchanged across a course-only manoeuvre",
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    scenarios = load_scenarios(args.truth)
    if args.limit:
        scenarios = scenarios[: args.limit]
    imm = load_predictions(args.imm)
    lsq = load_predictions(args.lsq)

    rows: list[dict] = []
    for sc in scenarios:
        if abs(sc.sigma - SIGMA_1DEG) > 1e-6:
            continue
        dt = sc.t[1] - sc.t[0]
        for off in GATE_OFFSETS_S:
            k = sc.zig_index + int(round(off / dt))
            if k >= sc.t.size:
                continue
            tk = float(sc.t[k])
            row: dict = {
                "scenario": sc.index,
                "offset_s": off,
                "settled": bool(settled(sc, k)),
                "n_spans_started": sum(1 for s, _, _ in sc.spans if s <= k),
            }
            knots = [i for s, e, _ in sc.spans if s <= k for i in (s, e)]
            o = solve_segments(
                sc,
                k,
                knots,
                args.prior_sd,
                args.speed_prior_sd,
                [(s_, e_) for s_, e_, kind in sc.spans if kind == "course"],
            )
            if o is None:
                row["oracle"] = None
            else:
                est, _ = o
                row["oracle"] = errors(sc, k, *est)
            for name, preds in (("imm", imm), ("lsq", lsq)):
                r = preds.get(sc.index, {}).get(tk)
                if r is None or not r.get("converged", True):
                    row[name] = None
                else:
                    vx = r["speed_mps"] * math.sin(r["course_rad"])
                    vy = r["speed_mps"] * math.cos(r["course_rad"])
                    row[name] = errors(sc, k, r["x_m"], r["y_m"], vx, vy)
            rows.append(row)

    def summarise(subset: list[dict], label: str) -> None:
        print(f"\n{label}: n = {len(subset)}")
        print(
            f"{'estimator':10s} {'range med':>10s} {'range p90':>10s} {'course med':>11s} {'speed med':>10s} {'gross':>7s} {'no est':>7s}"
        )
        for name in ("oracle", "lsq", "imm"):
            vals = np.array([r[name] for r in subset if r[name] is not None])
            missing = sum(1 for r in subset if r[name] is None)
            if vals.size == 0:
                continue
            gross = (np.sum(vals[:, 0] > 0.5) + missing) / len(subset)
            print(
                f"{name:10s} {np.median(vals[:, 0]) * 100:9.2f}% {np.percentile(vals[:, 0], 90) * 100:9.1f}% {np.median(vals[:, 1]):10.2f}° {np.median(vals[:, 2]):8.2f}kt {gross * 100:6.2f}% {missing:7d}"
            )

    summarise(rows, "All G5 rows (σ = 1°)")
    summarise([r for r in rows if r["settled"]], "Settled rows")
    summarise(
        [r for r in rows if not r["settled"]],
        "Unsettled rows (manoeuvre in progress or ended < 5 min ago)",
    )
    for off in GATE_OFFSETS_S:
        summarise([r for r in rows if r["offset_s"] == off], f"zig + {off // 60} min")
    summarise([r for r in rows if r["n_spans_started"] == 0], "Rows before any manoeuvre")
    summarise(
        [r for r in rows if r["n_spans_started"] > 0], "Rows after at least one manoeuvre started"
    )

    # Paired bootstrap of median-range ratios, clustered by scenario.
    rng = np.random.default_rng(20261011)
    by_sc: dict[int, list[dict]] = {}
    for r in rows:
        by_sc.setdefault(r["scenario"], []).append(r)
    keys = list(by_sc)

    def ratio(sample_rows: list[dict], a: str, b: str, which: int) -> float:
        pairs = [
            (r[a][which], r[b][which]) for r in sample_rows if r[a] is not None and r[b] is not None
        ]
        arr = np.array(pairs)
        return float(np.median(arr[:, 0]) / np.median(arr[:, 1]))

    print("\nPaired, scenario-clustered bootstrap (2000 resamples), median ratios oracle / imm:")
    for label, pred in (("all rows", lambda r: True), ("settled", lambda r: r["settled"])):
        for which, qty in ((0, "range"), (1, "course"), (2, "speed")):
            base = [r for r in rows if pred(r)]
            point = ratio(base, "oracle", "imm", which)
            boots = []
            for _ in range(2000):
                pick = rng.choice(keys, size=len(keys), replace=True)
                sample = [r for kk in pick for r in by_sc[kk] if pred(r)]
                boots.append(ratio(sample, "oracle", "imm", which))
            lo, hi = np.percentile(boots, [1.25, 98.75])
            print(f"  {label:9s} {qty:7s} {point:.3f}  97.5% CI [{lo:.3f}, {hi:.3f}]")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(rows, f)


if __name__ == "__main__":
    main()
