"""Spec 005 T021 (search penalty on MAN2): the additive search's false transitions and recall
against its per-leg penalty, on the σ = 1° tuning ordinals of seed 314.

MAN2 engagements almost always hold a target change (93.5% hold two or more), so R1's "false
split on engagements without a change" has too few rows to calibrate on. The measure here is per
scored G5 prefix: a *false transition* is a reported transition, after the zig plus L_min, whose
start is not within ± 3 min (18 rows) of a truth change's start; the rate is the share of G5
prefixes with at least one. Recall is the share of truth changes after the zig plus L_min, begun
by row k − L_min, with a reported transition starting within ± 60 s (6 rows).

    uv run python scripts/research/man2_penalty.py --validation data/man2-val/validation.f32pack \\
        --start 0 --count 500 --out experiments/<id>/penalty.json
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np

from tma2.references.classical import bearing_data_from_arrays
from tma2.segment import default_parameters
from tma2.segment.score import g5_rows, iter_selected
from tma2.segment.search import anchored_grid, cost_table, run_search
from tma2.segment.truth import change_rows

PENALTIES = (10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 120.0, 160.0)
TOL3 = 18
TOL = 6
CHUNK = 8


def task(args: tuple[str, int, int]) -> list[dict[str, Any]]:
    path, start, count = args
    p = default_parameters()
    t_max = max(p.t_lengths_rows)
    out = []
    for j, m, own, _tgt, obs in iter_selected(path, start, count):
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if not ks:
            continue
        grid = anchored_grid(max(ks), ks[0], p.search_step_rows)
        table = (grid, cost_table(d, grid, p.l_min_rows))
        zig = int(m["zig_index"])
        truth = change_rows(m, "target")
        for k in ks:
            rec: dict[str, Any] = {"ordinal": j, "k": k, "by_penalty": {}}
            tk = [a for a, _b in truth if zig + p.l_min_rows <= a <= k - p.l_min_rows]
            for pen in PENALTIES:
                _c, _legs, trans = run_search(
                    d, k, pen, p.l_min_rows, p.t_min_rows, t_max, p.search_step_rows,
                    table=table,
                )  # fmt: skip
                starts = [a for a, _b, _o in trans if a >= zig + p.l_min_rows]
                false = sum(1 for a in starts if not any(abs(a - t) <= TOL3 for t, _ in truth))
                hit = sum(1 for t in tk if any(abs(a - t) <= TOL for a in starts))
                rec["by_penalty"][str(pen)] = [false, hit, len(tk)]
            out.append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=500)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    chunks = [
        (a.validation, s, min(CHUNK, a.start + a.count - s))
        for s in range(a.start, a.start + a.count, CHUNK)
    ]
    with ProcessPoolExecutor(a.workers) as ex:
        recs = [r for part in ex.map(task, chunks) for r in part]
    summary = {}
    for pen in PENALTIES:
        v = np.array([r["by_penalty"][str(pen)] for r in recs])
        summary[str(pen)] = {
            "false_transition_prefix_rate": float(np.mean(v[:, 0] > 0)),
            "false_transitions_per_prefix": float(np.mean(v[:, 0])),
            "recall_60s": float(v[:, 1].sum() / max(v[:, 2].sum(), 1)),
        }
    res = {
        "validation": a.validation,
        "ordinals": [a.start, a.start + a.count - 1],
        "prefixes": len(recs),
        "scenarios": len({r["ordinal"] for r in recs}),
        "seconds": time.time() - t0,
        "summary": summary,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
