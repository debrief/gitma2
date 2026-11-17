"""Real-time estimates over a long engagement (spec 023): what each standing system can say *now*,
every ``step_s``, from the bearings it has.

* ``e``: the carried model E (Gate 2) on the last two hours (its exported graph's 720-row window,
  ``site/static/viewer-data/model.onnx``, run by Python onnxruntime): E-s's segmentation of the
  window, C's hand-over, the graph.
* ``c2``: C″ (C with the zig veto and the fixed fade) on the same window, with the veto applied at
  every ownship turn in it (``windows.turns_veto``): C″ as registered vetoes one zig only.
* ``one_leg``: the physics layer with no segmentation on the last ``one_leg_s`` seconds.
* ``imm``: the frozen MAN2 IMM run once over the whole engagement (a filter needs no window).

Each window is re-solved from scratch, as a real system with these components would have to.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np

from .sim import Engagement
from .windows import bearing_data, thinned, turns_veto, window

ROOT = Path(__file__).resolve().parents[3]
PLAN = "configs/gate2/g2-a.json"
ES = "experiments/20261107-g2-val/models/es-s3/best.safetensors"
MODEL = "site/static/viewer-data/model.onnx"
IMM = "imm-cv0.03-ct1-w0.01-s0.0003-p4-r2"
VETO_WINDOW = 6
FADE = (0.73, 0.0079)
CHUNK = 16
WINDOW_ROWS = 720
SYSTEMS = ("e", "c2", "one_leg", "imm")


class RealTime:
    def __init__(self) -> None:
        import onnxruntime as ort  # type: ignore[import-untyped]
        from safetensors.torch import load_file

        from tma2.gate2.es import ESSettings, make_net
        from tma2.segment.evidence import CHANNELS
        from tma2.types.generated.tma import SegmentParameters

        self.plan = json.loads((ROOT / PLAN).read_text())
        gs = json.loads((ROOT / self.plan["c"]["parameters_from"]).read_text())
        self.p = SegmentParameters.model_validate(gs["segmenter"]["parameters"])
        self.net = make_net(ESSettings(**self.plan["es"]), CHANNELS)
        self.net.load_state_dict(load_file(str(ROOT / ES)))
        self.net.eval()
        self.sess = ort.InferenceSession(str(ROOT / MODEL), providers=["CPUExecutionProvider"])

    def run(
        self,
        e5: Engagement,
        step_s: float = 600.0,
        one_leg_s: float = 1800.0,
        limit: int = 0,
        shard: tuple[int, int] = (0, 1),
    ) -> dict[str, Any]:
        """States [T, 4] per system at the evaluation times, truth [T, 6] and timings."""
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
        first_eval = e.meta["ownship_turns"][0][1] + int(round(300 / dt))
        ks = list(range(first_eval, e.samples, stride))
        if limit:
            ks = ks[:limit]
        i_sh, n_sh = shard  # a contiguous share of the evaluations, for CI jobs
        ks = ks[len(ks) * i_sh // n_sh : len(ks) * (i_sh + 1) // n_sh]
        mode, oh = self.plan["c"]["mode"], self.plan["c"].get("open_handover")
        out: dict[str, Any] = {s: np.full((len(ks), 4), np.nan) for s in SYSTEMS}
        took = {s: 0.0 for s in SYSTEMS}
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
            for c0 in range(0, len(ks), CHUNK):
                part = ks[c0 : c0 + CHUNK]
                wins = [
                    window(e, max(0, k - WINDOW_ROWS + 1), min(k + 1, WINDOW_ROWS), "last")
                    for k in part
                ]
                data = [bearing_data(w) for w in wins]
                last = [[d.n - 1] for d in data]
                # C″ on the window, the veto at every ownship turn
                t1 = time.perf_counter()
                ev = [
                    turns_veto(d, w.meta["ownship_turns"], VETO_WINDOW)
                    for d, w in zip(data, wins, strict=True)
                ]
                noms = [nominations_for(d, d.n - 1, self.p) for d in data]
                confs = confirm(
                    PhysicsLayer(), data, noms, self.p, max(d.n for d in data), evidence=ev
                )
                c2 = [intervals_at(c, d.n - 1, self.p) for c, d in zip(confs, data, strict=True)]
                items = []
                where = []
                for i, (d, ivs) in enumerate(zip(data, c2, strict=True)):
                    x = prefix_inputs(d, d.n - 1, ivs, mode, oh)
                    if x is None:
                        continue
                    age = (d.n - 1) - np.arange(len(x.log_weight))
                    add = np.clip(FADE[0] - FADE[1] * age, -2.0, 2.0)
                    add[age < 0] = 0.0
                    x.log_weight = x.log_weight + add
                    items.append((d, d.n - 1, x))
                    where.append(i)
                if items:
                    res = run_layer(layer, items, WINDOW_ROWS)
                    for b, i in enumerate(where):
                        out["c2"][c0 + i] = self._abs(res.state[b].numpy(), wins[i])
                took["c2"] += time.perf_counter() - t1
                # E: E-s's segmentation, C's hand-over, the exported graph
                t1 = time.perf_counter()
                segs = es_segmentations(self.net, data, [w.own for w in wins], last, self.p)
                items, codes, where = [], [], []
                for i, (d, sg) in enumerate(zip(data, segs, strict=True)):
                    eivs = sg.get(d.n - 1)
                    x = None if eivs is None else prefix_inputs(d, d.n - 1, eivs, mode, oh)
                    if x is None or eivs is None:
                        continue
                    items.append((d, d.n - 1, x))
                    codes.append(np.pad(code_channel(eivs, d.n - 1, d.n), (0, WINDOW_ROWS - d.n)))
                    where.append(i)
                if items:
                    xin = inputs_for(items, WINDOW_ROWS)
                    ins = {n: getattr(xin, n).numpy() for n in INPUTS[:-1]}
                    ins["code"] = np.stack(codes).astype(np.float64)
                    for b, i in enumerate(where):
                        got = self.sess.run(None, {n: ins[n][b : b + 1] for n in INPUTS})
                        ok = bool(got[2][0]) if np.ndim(got[2][0]) == 0 else bool(np.all(got[2][0]))
                        if ok:
                            out["e"][c0 + i] = self._abs(np.asarray(got[0][0])[:4], wins[i])
                took["e"] += time.perf_counter() - t1
                # one leg on the last one_leg_s seconds
                t1 = time.perf_counter()
                n1 = int(round(one_leg_s / dt))
                items = []
                where1: list[tuple[int, Engagement]] = []
                for i, k in enumerate(part):
                    w = window(e, max(0, k - n1 + 1), min(k + 1, n1), "last")
                    d = bearing_data(w)
                    x = segmentation_inputs(
                        d.t, d.ox, d.oy, d.z, d.valid, d.n - 1, [], "chord", False
                    )
                    if x is not None:
                        items.append((d, d.n - 1, x))
                        where1.append((i, w))
                if items:
                    res = run_layer(layer, items, max(it[0].n for it in items))
                    for b, (i, w) in enumerate(where1):
                        out["one_leg"][c0 + i] = self._abs(res.state[b].numpy(), w)
                took["one_leg"] += time.perf_counter() - t1
        finally:
            torch.set_default_dtype(default)
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
        }

    @staticmethod
    def _abs(state: np.ndarray, w: Engagement) -> np.ndarray:
        """A window's (x, y, vx, vy) back in the engagement's frame."""
        ox, oy = w.meta["window_origin_m"]
        s = np.asarray(state[:4], dtype=np.float64).copy()
        s[0] += ox
        s[1] += oy
        return s
