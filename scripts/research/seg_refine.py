"""Spec 005 research R2: segmenter C's coupled refinement, prototype.

The search stage (``seg_search.py``) at a generous penalty nominates transitions. They are
confirmed in time order by the whole-history physics-layer solve on [0, k]: a transition [x, y]
adds knots at x and y + 1 (the chord), and is kept if it lowers the cost by more than the χ²
point with 4 degrees of freedom equivalent to ``tau`` (``tma2.detect.confirm.tau_4dof``); a
transition open at k adds a knot at x only, tested at ``tau``. Scenarios are batched, as in
``confirm_knots``.

    uv run python scripts/research/seg_refine.py --validation data/gd-val/validation.f32pack \\
        --search /tmp/seg-tune300.json --penalty 20 --out /tmp/refine.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import torch

from tma2.detect.confirm import knot_inputs, layer_costs, tau_4dof
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData, bearing_data_from_arrays

sys.path.insert(0, "scripts/research")
import leg_spike as ls  # type: ignore[import-not-found]  # noqa: E402


def transitions(seg: list[int], n: int) -> list[tuple[int, int]]:
    legs = [(seg[i], seg[i + 1]) for i in range(0, len(seg) - len(seg) % 2, 2)]
    tr = [(b + 1, c - 1) for (_a, b), (c, _d) in zip(legs, legs[1:], strict=False)]
    if len(seg) % 2:
        tr.append((seg[-1], n - 1))
    return tr


def refine(
    layer: PhysicsLayer,
    data: list[BearingData],
    cands: list[list[tuple[int, int]]],
    tau: float,
    horizon: int = -1,
) -> list[list[tuple[int, int, float]]]:
    """Accepted transitions per scenario: (start, end, cost drop). With ``horizon`` ≥ 0 each
    transition is tested on the prefix ending ``horizon`` rows after it (its own time), not on
    the whole history, so misfit from later, undetected manoeuvres cannot be absorbed by it."""
    tau4 = tau_4dof(tau)
    k_all = [d.n - 1 for d in data]
    acc: list[list[tuple[int, int, float]]] = [[] for _ in data]
    r_max = max(d.n for d in data)
    for p in range(max((len(c) for c in cands), default=0)):
        items: list[tuple[BearingData, int, LayerInputs]] = []
        tags: list[tuple[int, int, int, bool]] = []
        for i, d in enumerate(data):
            if p >= len(cands[i]):
                continue
            x, y = cands[i][p]
            k = k_all[i] if horizon < 0 else min(k_all[i], y + 1 + horizon)
            cur = [r for s, e, _ in acc[i] for r in (s, e + 1) if 0 < r <= k]
            closed = y + 1 <= k
            new = [x, y + 1] if closed else [x]
            base = knot_inputs(d, k, cur, False)
            cand = knot_inputs(d, k, [*cur, *new], False)
            if base is None or cand is None:
                continue
            items += [(d, k, base), (d, k, cand)]
            tags.append((i, x, y, closed))
        costs = layer_costs(layer, items, r_max)
        for q, (i, x, y, closed) in enumerate(tags):
            drop = costs[2 * q] - costs[2 * q + 1]
            if drop > (tau4 if closed else tau):
                acc[i].append((x, y, drop))
    return acc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validation", required=True)
    ap.add_argument("--search", required=True)
    ap.add_argument("--penalty", default="20")
    ap.add_argument("--tau", type=float, default=13.8)
    ap.add_argument("--horizon", type=int, default=-1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    torch.set_default_dtype(torch.float64)
    recs = {r["ordinal"]: r for r in json.load(open(a.search, encoding="utf-8"))}
    lo, hi = min(recs), max(recs)
    data: list[BearingData] = []
    cands: list[list[tuple[int, int]]] = []
    ords: list[int] = []
    for j, meta, own, _tgt, obs in ls.iter_selected(a.validation, lo, hi - lo + 1):
        if j not in recs:
            continue
        d = bearing_data_from_arrays(meta, own, obs)
        data.append(d)
        cands.append(transitions(recs[j]["by_penalty"][a.penalty]["seg"], d.n))
        ords.append(j)
    t0 = time.time()
    acc = refine(PhysicsLayer(), data, cands, a.tau, a.horizon)
    sec = time.time() - t0
    out: dict[str, Any] = {"penalty": a.penalty, "tau": a.tau, "seconds": sec, "accepted": {}}
    for j, x in zip(ords, acc, strict=True):
        out["accepted"][str(j)] = x
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f)
    print(f"{len(data)} scenarios refined in {sec:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
