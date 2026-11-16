"""Demo data for the browser viewer (spec 020 T002).

Per engagement, at every 60 s from the first G5 row (zig + 5 min) to the end of the window:

* E's segmentation (C's confirmation with the carried E-s's evidence) and C's hand-over of it,
  as ``gate2.predict`` builds them; from those, the exported E-w graph's twelve inputs, padded
  to the graph's 720-row window;
* Python onnxruntime's outputs of the exported graph on exactly those inputs (the reference the
  page's browser outputs are checked against);
* the truth, and the comparison estimates computed in Python: one leg (the physics layer with no
  segmentation, SRD §5's plain batch least squares), the frozen IMM, C and C″ (C with the zig
  veto and the fixed fade), as Gate 2 scored them.

Scenarios are processed in the chunks of 16 σ = 1° ordinals that ``tma2-segment`` and
``tma2-g2predict`` used, so each engagement's segmentation is the one Gate 2's runs would make
(a segmentation depends on its chunk through padding; AGENTS.md gotchas).

Inputs that are the same at every row of an engagement are stored once. Binary arrays are
little-endian float64, gzipped with no timestamp, so the files reproduce byte for byte.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from tma2.gate2.export import INPUTS, OUTPUTS, ROWS

STEP_ROWS = 6  # 60 s at MAN2's 10 s sample interval
CHUNK = 16  # as cli.segment / cli.g2predict
IMM = "imm-cv0.03-ct1-w0.01-s0.0003-p4-r2"  # frozen MAN2 IMM (experiments/20261104-man2-refs)
VETO_WINDOW = 6  # C″ (configs/gate2/g2-a-fade.json)
FADE = (0.73, 0.0079)
SYSTEMS = ("one_leg", "imm", "c", "c2")
SYSTEM_LABELS = {
    "e": "E (carried model, computed in your browser)",
    "one_leg": "batch least squares, one leg (Python)",
    "imm": "IMM, frozen tuning (Python)",
    "c": "C, classical segmenter (Python)",
    "c2": "C″, zig veto and fixed fade, nothing learned (Python)",
}
PLAUSIBLE_MAX_RANGE_M = 100_000.0
PLAUSIBLE_MAX_SPEED_MPS = 25.0


def gz(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9, mtime=0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_rows(meta: dict[str, Any], n: int) -> list[int]:
    from tma2.segment.score import g5_rows

    g5 = g5_rows(meta, n)
    return list(range(g5[0], n, STEP_ROWS)) if g5 else []


def eligible(meta: dict[str, Any], n: int) -> bool:
    from tma2.eval.rows import G5_GATE_MIN
    from tma2.segment.score import g5_rows

    return len(g5_rows(meta, n)) == len(G5_GATE_MIN)


def state_fields(state: np.ndarray, own_k: tuple[float, float]) -> dict[str, float]:
    """Range, course and speed of an (x, y, vx, vy) state, as the physics layer defines them."""
    x, y, vx, vy = (float(v) for v in state[:4])
    course = math.atan2(vx, vy) % (2 * math.pi)
    return {
        "x_m": x,
        "y_m": y,
        "range_m": math.hypot(x - own_k[0], y - own_k[1]),
        "course_rad": course,
        "speed_mps": math.hypot(vx, vy),
    }


def answered(row: dict[str, Any] | None) -> bool:
    """``eval.errors.plausible_row``: finite fields, range in (0, 100 km], speed ≤ 25 m/s."""
    if row is None:
        return False
    vals = [float(row[k]) for k in ("range_m", "course_rad", "speed_mps", "x_m", "y_m")]
    if not all(math.isfinite(v) for v in vals):
        return False
    return 0.0 < vals[0] <= PLAUSIBLE_MAX_RANGE_M and vals[2] <= PLAUSIBLE_MAX_SPEED_MPS


def range_error(row: dict[str, Any] | None, tgt: np.ndarray, own: np.ndarray, k: int) -> float:
    if not answered(row):
        return math.inf
    assert row is not None
    rng = math.hypot(float(tgt[k, 1] - own[k, 1]), float(tgt[k, 2] - own[k, 2]))
    return abs(float(row["range_m"]) - rng) / rng


@dataclass
class Engagement:
    ordinal: int
    meta: dict[str, Any]
    own: np.ndarray
    tgt: np.ndarray
    obs: np.ndarray
    rows: list[int]
    inputs: dict[str, np.ndarray] = field(default_factory=dict)  # name → [R, ...]
    outputs: dict[str, np.ndarray] = field(default_factory=dict)  # name → [R, ...]
    have_e: list[bool] = field(default_factory=list)  # E has an input at the row
    open_rows: list[bool] = field(default_factory=list)
    systems: dict[str, list[dict[str, Any] | None]] = field(default_factory=dict)


class Builder:
    """Computes engagements chunk by chunk on demand."""

    def __init__(self, split: Path, export_dir: Path, plan_path: Path, es_weights: Path) -> None:
        import onnxruntime as ort  # type: ignore[import-untyped]
        from safetensors.torch import load_file

        from tma2.gate2.es import ESSettings, make_net
        from tma2.segment.evidence import CHANNELS
        from tma2.types.generated.tma import SegmentParameters

        self.split = split
        self.plan = json.loads(plan_path.read_text())
        root = Path(__file__).resolve().parents[3]
        gs = json.loads((root / self.plan["c"]["parameters_from"]).read_text())
        self.p = SegmentParameters.model_validate(gs["segmenter"]["parameters"])
        self.net = make_net(ESSettings(**self.plan["es"]), CHANNELS)
        self.net.load_state_dict(load_file(str(es_weights)))
        self.net.eval()
        self.sess = ort.InferenceSession(
            str(export_dir / "model.onnx"), providers=["CPUExecutionProvider"]
        )
        self.dtypes = {
            n: s["dtype"]
            for n, s in json.loads((export_dir / "manifest.json").read_text())["inputs"].items()
        }
        self.chunks: dict[int, dict[int, Engagement]] = {}
        self._metas: list[tuple[int, dict[str, Any], int]] | None = None

    def candidates(self, limit: int) -> list[tuple[int, dict[str, Any], int]]:
        from tma2.segment.score import iter_selected

        if self._metas is None:
            self._metas = [
                (j, m, grid_rows(m, obs.shape[0])[0])
                for j, m, _own, _tgt, obs in iter_selected(self.split, 0, limit)
                if eligible(m, obs.shape[0])
            ]
        return self._metas

    def engagement(self, j: int) -> Engagement:
        c = j // CHUNK
        if c not in self.chunks:
            self.chunks[c] = self._chunk(c)
        return self.chunks[c][j]

    def e_loses(self, j: int) -> bool:
        """E's median range error over the G5 rows is worse than C″'s (∞ where no answer)."""
        from tma2.segment.score import g5_rows

        g = self.engagement(j)
        if not any(g.have_e):
            return False
        g5 = set(g5_rows(g.meta, g.obs.shape[0]))
        e, c2 = [], []
        for q, k in enumerate(g.rows):
            if k in g5:
                e.append(range_error(self.e_row(g, q), g.tgt, g.own, k))
                c2.append(range_error(g.systems["c2"][q], g.tgt, g.own, k))
        return bool(np.median(e) > np.median(c2))

    def e_row(self, g: Engagement, q: int) -> dict[str, Any] | None:
        if not g.have_e[q]:
            return None
        k = g.rows[q]
        return state_fields(g.outputs["state"][q], (float(g.own[k, 1]), float(g.own[k, 2])))

    def _chunk(self, c: int) -> dict[int, Engagement]:
        import torch

        from tma2.cli.oracle import run_layer
        from tma2.detect.controls import parse_imm_name
        from tma2.gate2 import KNOTS
        from tma2.gate2.inputs import code_channel, prefix_inputs
        from tma2.gate2.predict import e_rows, es_segmentations, veto_segmentations
        from tma2.physics.layer import PhysicsLayer
        from tma2.references.classical import bearing_data_from_arrays
        from tma2.references.imm import imm_predict
        from tma2.segment import TRANSITION
        from tma2.segment.score import iter_selected, one_leg
        from tma2.segment.segmenter import segment

        torch.set_num_threads(1)
        default = torch.get_default_dtype()
        torch.set_default_dtype(torch.float64)
        try:
            gs: list[Engagement] = []
            data, metas, owns, rows = [], [], [], []
            for j, m, own, tgt, obs in iter_selected(self.split, c * CHUNK, CHUNK):
                d = bearing_data_from_arrays(m, own, obs)
                ks = grid_rows(m, d.n)
                if not ks:
                    continue
                gs.append(Engagement(j, m, own, tgt, obs, ks))
                data.append(d)
                metas.append(m)
                owns.append(own)
                rows.append(ks)
            mode, oh = self.plan["c"]["mode"], self.plan["c"].get("open_handover")
            p = self.p
            e_segs = es_segmentations(self.net, data, owns, rows, p)
            c_raw = segment(PhysicsLayer(), data, metas, rows, p)
            c_segs = [{s.k: s.intervals for s in seg} for seg in c_raw]
            c2_segs = veto_segmentations(data, rows, p, VETO_WINDOW)
            c_rows = e_rows(None, data, rows, c_segs, mode, oh)
            c2_rows = e_rows(None, data, rows, c2_segs, mode, oh, fade=FADE)
            layer = PhysicsLayer(knots=KNOTS)
            imm = parse_imm_name(IMM)
            for i, (g, d) in enumerate(zip(gs, data, strict=True)):
                items, codes, have, opened = [], [], [], []
                for k in g.rows:
                    ivs = e_segs[i].get(k)
                    inp = None if ivs is None else prefix_inputs(d, k, ivs, mode, oh)
                    have.append(inp is not None)
                    opened.append(
                        bool(ivs) and ivs[-1].kind == TRANSITION and bool(ivs[-1].open)
                        if ivs
                        else False
                    )
                    if inp is not None:
                        assert ivs is not None
                        items.append((d, k, inp))
                        codes.append(np.pad(code_channel(ivs, k, d.n), (0, ROWS - d.n)))
                g.have_e, g.open_rows = have, opened
                g.inputs, g.outputs = self._run_graph(items, codes)
                g.systems["c"] = [_plain(r) for r in c_rows[i]]
                g.systems["c2"] = [_plain(r) for r in c2_rows[i]]
                # one leg: the layer with no segmentation (segment.score.one_leg), 12 knots
                ol: list[dict[str, Any] | None] = []
                for k in g.rows:
                    inp = one_leg(g.ordinal, g.meta, d, k)
                    if inp is None:
                        ol.append(None)
                        continue
                    res = run_layer(layer, [(d, k, inp)], ROWS)
                    ol.append(
                        _plain(
                            {
                                "x_m": float(res.state[0, 0]),
                                "y_m": float(res.state[0, 1]),
                                "range_m": float(res.range[0]),
                                "course_rad": float(res.course[0]),
                                "speed_mps": float(res.speed[0]),
                            }
                        )
                    )
                g.systems["one_leg"] = ol
                # one row per sample from zig_index + 1 (references.imm.imm_predict)
                pred = imm_predict(d, imm)["rows"]
                first = d.zig_index + 1
                g.systems["imm"] = [
                    _plain(pred[k - first]) if 0 <= k - first < len(pred) else None for k in g.rows
                ]
            return {g.ordinal: g for g in gs}
        finally:
            torch.set_default_dtype(default)

    def _run_graph(
        self, items: list[Any], codes: list[np.ndarray]
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
        from tma2.cli.oracle import inputs_for

        if not items:
            return {}, {}
        x = inputs_for(items, ROWS)
        ins = {name: getattr(x, name).numpy() for name in INPUTS[:-1]}
        ins["code"] = np.stack(codes).astype(np.float64)
        outs: dict[str, list[np.ndarray]] = {o: [] for o in OUTPUTS}
        for r in range(len(items)):  # one row at a time, as the page runs it
            got = self.sess.run(None, {n: ins[n][r : r + 1] for n in INPUTS})
            for o, a in zip(OUTPUTS, got, strict=True):
                outs[o].append(a[0])
        return ins, {o: np.stack(v) for o, v in outs.items()}


def _plain(row: dict[str, Any] | None) -> dict[str, Any] | None:
    """A comparison row's point fields, or None where the system gives no answer (an empty row,
    an unconverged filter row, or a non-finite solve): ``answered`` decides the rest."""
    if row is None or row.get("converged") is False and not row.get("range_m"):
        return None
    out = {k: float(row[k]) for k in ("x_m", "y_m", "range_m", "course_rad", "speed_mps")}
    return out if all(math.isfinite(v) for v in out.values()) else None


def pack_engagement(g: Engagement, reason: str, dtypes: dict[str, str]) -> tuple[bytes, bytes]:
    """(JSON, binary) for one engagement; both gzipped. The binary is the graph's inputs (shared
    ones once) and Python's outputs, little-endian float64, in the order the JSON's ``layout``
    gives."""
    e_idx = [q for q, h in enumerate(g.have_e) if h]
    parts: list[np.ndarray] = []
    layout: list[dict[str, Any]] = []
    offset = 0
    for name in INPUTS:
        a = np.ascontiguousarray(g.inputs[name], dtype=np.float64)
        per_row = list(a.shape[1:])
        shared = bool(len(a) > 0 and np.array_equal(a, np.broadcast_to(a[0], a.shape)))
        block = a[:1] if shared else a
        layout.append(
            {
                "name": name,
                "kind": "input",
                "dtype": dtypes[name],
                "shape": [1, *per_row],
                "shared": shared,
                "offset": offset,
                "count": int(block.size),
            }
        )
        parts.append(block.ravel())
        offset += int(block.size)
    for name in OUTPUTS:
        a = np.ascontiguousarray(g.outputs[name], dtype=np.float64)
        layout.append(
            {
                "name": name,
                "kind": "output",
                "dtype": "float64",
                "shape": [1, *a.shape[1:]],
                "shared": False,
                "offset": offset,
                "count": int(a.size),
            }
        )
        parts.append(a.ravel())
        offset += int(a.size)
    binary = np.concatenate(parts).astype("<f8").tobytes()
    n = g.obs.shape[0]
    own, tgt = g.own, g.tgt
    doc = {
        "ordinal": g.ordinal,
        "scenario_index": int(g.meta["index"]),
        "reason": reason,
        "manoeuvres": g.meta.get("manoeuvres") or [],
        "samples": n,
        "dt_s": float(g.meta["parameters"]["dt_s"]),
        "zig_index": int(g.meta["zig_index"]),
        "own": [[round(float(own[i, 1]), 3), round(float(own[i, 2]), 3)] for i in range(n)],
        "target": [
            [
                round(float(tgt[i, 1]), 3),
                round(float(tgt[i, 2]), 3),
                float(tgt[i, 3]),
                float(tgt[i, 4]),
            ]
            for i in range(n)
        ],
        "rows": g.rows,
        "times_s": [float(g.own[k, 0]) for k in g.rows],
        "e_rows": e_idx,  # positions in ``rows`` at which E has an input (the binary's rows)
        "open": g.open_rows,
        "systems": {s: g.systems[s] for s in SYSTEMS},
        "layout": layout,
        "binary_values": offset,
    }
    text = json.dumps(doc, separators=(",", ":"), allow_nan=False)
    return gz(text.encode()), gz(binary)
