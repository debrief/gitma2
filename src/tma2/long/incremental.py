"""An incremental C for long engagements (spec 024, recommendation 2 of note 12).

Spec 023 re-ran C's confirmation (and E-s's) over the whole 2-hour window for every 10-minute
estimate: 27–37 s each. C is causal, so one confirmation over a block of data gives the
segmentation at every row of it (``segmenter.intervals_at``). This module runs one confirmation
per *block* of evaluations, on the block's rows plus the two hours before its first evaluation,
and for each evaluation keeps the confirmed segmentation of the last 720 rows (the graph's
window): older legs are dropped, the confirmed ones inside the window are kept. The final solves
(E's graph, C″'s faded layer solve) are unchanged and see exactly the 720-row window, as before.

With one evaluation per block this is the spec 023 per-window run row for row
(``tests/unit/test_long_incremental.py``). With longer blocks a decision at row k can draw on up
to ``block`` more history than the window holds: C keeps what it confirmed earlier.
"""

from __future__ import annotations

import math
import time
from typing import Any

import numpy as np

from tma2.segment import TRANSITION, Interval, from_codes, to_codes

from .realtime import CHUNK, FADE, IMM, SYSTEMS, VETO_WINDOW, WINDOW_ROWS, RealTime
from .sim import Engagement
from .windows import bearing_data, thinned, turns_veto, window

MIN_BEARINGS = 60  # ten minutes of 10-second bearings: fewer, and a window gives no estimate


def crop(ivs: list[Interval], k: int, first: int) -> list[Interval]:
    """The segmentation of rows ``first`` … ``k`` (re-indexed from 0) from that of 0 … ``k``.
    A leg or transition cut by ``first`` keeps its part inside; the open flag of the last
    interval is kept."""
    codes = to_codes(ivs, k + 1)[first:]
    out = from_codes(codes)
    if ivs and out and ivs[-1].open and out[-1].kind == TRANSITION:
        out[-1] = Interval(TRANSITION, out[-1].start, out[-1].end, True)
    return out


class Incremental(RealTime):
    def run_incremental(
        self,
        e5: Engagement,
        step_s: float = 600.0,
        block_s: float = 7200.0,
        one_leg_s: float = 1800.0,
        limit: int = 0,
        shard: tuple[int, int] = (0, 1),
    ) -> dict[str, Any]:
        """As ``RealTime.run``, with C and E-s confirmed once per block of ``block_s``."""
        import torch

        from tma2.cli.oracle import inputs_for, run_layer
        from tma2.detect.controls import parse_imm_name
        from tma2.gate2 import KNOTS
        from tma2.gate2.export import INPUTS
        from tma2.gate2.inputs import code_channel, prefix_inputs
        from tma2.gate2.predict import es_segmentations
        from tma2.physics.layer import PhysicsLayer
        from tma2.references.imm import imm_predict
        from tma2.segment.confirm import confirm
        from tma2.segment.inputs import segmentation_inputs
        from tma2.segment.segmenter import intervals_at, nominations_for

        torch.set_num_threads(1)
        default = torch.get_default_dtype()
        torch.set_default_dtype(torch.float64)
        e = thinned(e5, int(round(10.0 / e5.dt)))
        dt = e.dt
        stride = int(round(step_s / dt))
        per_block = max(1, int(round(block_s / step_s)))
        first_eval = e.meta["ownship_turns"][0][1] + int(round(300 / dt))
        ks = list(range(first_eval, e.samples, stride))
        if limit:
            ks = ks[:limit]
        i_sh, n_sh = shard
        ks = ks[len(ks) * i_sh // n_sh : len(ks) * (i_sh + 1) // n_sh]
        mode, oh = self.plan["c"]["mode"], self.plan["c"].get("open_handover")
        out: dict[str, Any] = {s: np.full((len(ks), 4), np.nan) for s in SYSTEMS}
        took = {s: 0.0 for s in SYSTEMS}
        took["segment_c2"] = took["segment_e"] = 0.0
        blocks = [list(range(b, min(b + per_block, len(ks)))) for b in range(0, len(ks), per_block)]
        try:
            t1 = time.perf_counter()
            dfull = bearing_data(e)
            pred = imm_predict(dfull, parse_imm_name(IMM))["rows"]
            first = dfull.zig_index + 1
            for q, k in enumerate(ks):
                r = pred[k - first] if 0 <= k - first < len(pred) else None
                if r is not None and r.get("converged") is not False and r.get("range_m"):
                    c, v = float(r["course_rad"]), float(r["speed_mps"])
                    out["imm"][q] = [r["x_m"], r["y_m"], v * math.sin(c), v * math.cos(c)]
            took["imm"] = time.perf_counter() - t1
            layer = PhysicsLayer(knots=KNOTS)

            def held(b: list[int]) -> bool:
                w0 = max(0, ks[b[0]] - WINDOW_ROWS + 1)
                return int((e.obs[w0 : ks[b[-1]] + 1, 2] != 0).sum()) >= MIN_BEARINGS

            blocks = [b for b in blocks if held(b)]  # a contact not held has no estimate
            for c0 in range(0, len(blocks), CHUNK):
                bl = blocks[c0 : c0 + CHUNK]
                # one data block per block of evaluations: two hours before its first, to its last
                w0s = [max(0, ks[b[0]] - WINDOW_ROWS + 1) for b in bl]
                bws = [
                    window(e, w0, ks[b[-1]] - w0 + 1, "last") for w0, b in zip(w0s, bl, strict=True)
                ]
                bds = [bearing_data(w) for w in bws]
                rows = [[ks[q] - w0 for q in b] for w0, b in zip(w0s, bl, strict=True)]
                # C″'s segmentation, the veto at every ownship turn in the block
                t1 = time.perf_counter()
                ev = [
                    turns_veto(d, w.meta["ownship_turns"], VETO_WINDOW)
                    for d, w in zip(bds, bws, strict=True)
                ]
                noms = [nominations_for(d, r[0], self.p) for d, r in zip(bds, rows, strict=True)]
                confs = confirm(
                    PhysicsLayer(), bds, noms, self.p, max(d.n for d in bds), evidence=ev
                )
                c2segs = [
                    {k: intervals_at(c, k, self.p) for k in r}
                    for c, r in zip(confs, rows, strict=True)
                ]
                took["segment_c2"] += time.perf_counter() - t1
                t1 = time.perf_counter()
                esegs = es_segmentations(self.net, bds, [w.own for w in bws], rows, self.p)
                took["segment_e"] += time.perf_counter() - t1
                # per evaluation: the last 720 rows and the confirmed segmentation inside them
                ev_items: list[
                    tuple[int, Engagement, list[Interval] | None, list[Interval] | None]
                ] = []
                for bi, b in enumerate(bl):
                    for j, q in enumerate(b):
                        kb = rows[bi][j]
                        cw0 = max(0, kb - WINDOW_ROWS + 1)
                        w = window(e, w0s[bi] + cw0, kb - cw0 + 1, "last")
                        if int((w.obs[:, 2] != 0).sum()) < MIN_BEARINGS:
                            continue
                        c2iv = c2segs[bi].get(kb)
                        eiv = esegs[bi].get(kb)
                        ev_items.append(
                            (
                                q,
                                w,
                                None if c2iv is None else crop(c2iv, kb, cw0),
                                None if eiv is None else crop(eiv, kb, cw0),
                            )
                        )
                t1 = time.perf_counter()
                items, where = [], []
                for q, w, c2iv, _eiv in ev_items:
                    d = bearing_data(w)
                    x = None if c2iv is None else prefix_inputs(d, d.n - 1, c2iv, mode, oh)
                    if x is None:
                        continue
                    age = (d.n - 1) - np.arange(len(x.log_weight))
                    add = np.clip(FADE[0] - FADE[1] * age, -2.0, 2.0)
                    add[age < 0] = 0.0
                    x.log_weight = x.log_weight + add
                    items.append((d, d.n - 1, x))
                    where.append((q, w))
                if items:
                    res = run_layer(layer, items, WINDOW_ROWS)
                    for b_, (q, w) in enumerate(where):
                        out["c2"][q] = self._abs(res.state[b_].numpy(), w)
                took["c2"] += time.perf_counter() - t1
                t1 = time.perf_counter()
                items, codes, where = [], [], []
                for q, w, _c2iv, eiv in ev_items:
                    d = bearing_data(w)
                    x = None if eiv is None else prefix_inputs(d, d.n - 1, eiv, mode, oh)
                    if x is None or eiv is None:
                        continue
                    items.append((d, d.n - 1, x))
                    codes.append(np.pad(code_channel(eiv, d.n - 1, d.n), (0, WINDOW_ROWS - d.n)))
                    where.append((q, w))
                if items:
                    xin = inputs_for(items, WINDOW_ROWS)
                    ins = {n: getattr(xin, n).numpy() for n in INPUTS[:-1]}
                    ins["code"] = np.stack(codes).astype(np.float64)
                    for b_, (q, w) in enumerate(where):
                        got = self.sess.run(None, {n: ins[n][b_ : b_ + 1] for n in INPUTS})
                        ok = bool(got[2][0]) if np.ndim(got[2][0]) == 0 else bool(np.all(got[2][0]))
                        if ok:
                            out["e"][q] = self._abs(np.asarray(got[0][0])[:4], w)
                took["e"] += time.perf_counter() - t1
                t1 = time.perf_counter()
                n1 = int(round(one_leg_s / dt))
                items = []
                where1: list[tuple[int, Engagement]] = []
                for q, _w, _a, _b in ev_items:
                    k = ks[q]
                    w = window(e, max(0, k - n1 + 1), min(k + 1, n1), "last")
                    if int((w.obs[:, 2] != 0).sum()) < MIN_BEARINGS // 3:
                        continue
                    d = bearing_data(w)
                    x = segmentation_inputs(
                        d.t, d.ox, d.oy, d.z, d.valid, d.n - 1, [], "chord", False
                    )
                    if x is not None:
                        items.append((d, d.n - 1, x))
                        where1.append((q, w))
                if items:
                    res = run_layer(layer, items, max(it[0].n for it in items))
                    for b_, (q, w) in enumerate(where1):
                        out["one_leg"][q] = self._abs(res.state[b_].numpy(), w)
                took["one_leg"] += time.perf_counter() - t1
        finally:
            torch.set_default_dtype(default)
        # the segmentation's cost belongs to the systems that use it
        took["c2"] += took.pop("segment_c2")
        took["e"] += took.pop("segment_e")
        truth = np.stack(
            [e.tgt[ks, 1], e.tgt[ks, 2], e.tgt[ks, 3], e.tgt[ks, 4], e.own[ks, 1], e.own[ks, 2]],
            axis=1,
        )
        return {
            "rows": np.array(ks),
            "times_s": e.own[ks, 0].copy(),
            "truth": truth,
            "states": {s: out[s] for s in SYSTEMS},
            "seconds": took,
            "imm_name": IMM,
        }
