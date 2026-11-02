"""Per-timestep detector outputs (spec 004 FR-013, contracts/cli.md ``tma2-detect``).

For each scenario of a truth file: ``p_change`` at every row; ``p_kind`` of the last row's
question at every row; and the knots exported (``detector_inputs.export_knots``) by the question
asked at each G5 row (zig + 5/10/15/20 min, where reached) and at the last row. The causal
detector asks each question at its own row; the time-late detector asks its one question at the
last row (its knot set for every scored row is that one).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors.torch import load_file

from tma2.data.canonical import canonical_json
from tma2.data.io import AtomicFile, file_digest
from tma2.eval.rows import G5_GATE_MIN
from tma2.sim.geometry import f32
from tma2.types import SCHEMA_VERSION
from tma2.types.generated.tma import DetectorVariant

from .detector import Detector, features
from .detector_inputs import KNOT_THRESHOLD, export_knots
from .detector_train import detector_from_plan
from .train import batch_from_pack, load_plan, slice_batch


def load_detector(plan_path: str | Path, detector_id: str, checkpoint: str | Path) -> Detector:
    plan, _ = load_plan(plan_path)
    cfg = detector_from_plan(plan, detector_id)
    torch.set_default_dtype(torch.float64)
    model = Detector(cfg)
    weights = Path(checkpoint) / "best.safetensors"
    if not weights.exists():
        raise FileNotFoundError(f"{weights}: no best weights in this checkpoint")
    model.load_state_dict(load_file(str(weights)))
    model.weights_digest = file_digest(weights)
    model.eval()
    return model


def g5_query_rows(zig: int, samples: int, dt: float) -> list[int]:
    ks = [zig + int(round(m * 60 / dt)) for m in G5_GATE_MIN]
    return [k for k in ks if k < samples]


def _knots_json(w: np.ndarray, pk: np.ndarray, k: int, threshold: float, m: int) -> list[Any]:
    return [
        {"row": kn.row, "weight": f32(kn.weight), "p_kind": f32(kn.p_kind)}
        for kn in export_knots(w, pk, k, threshold, m)
    ]


@torch.no_grad()
def detect_split(
    model: Detector,
    truth: str | Path,
    out: str | Path,
    limit: int | None = None,
    chunk: int = 16,
    threshold: float = KNOT_THRESHOLD,
    max_knots: int | None = None,
) -> int:
    truth = Path(truth)
    m = max_knots or model.cfg.knots
    batch_all = batch_from_pack(truth, limit or 10**9)
    header: dict[str, Any] = {
        "record": "header",
        "schema_version": SCHEMA_VERSION,
        "detector": model.cfg.id,
        "variant": DetectorVariant(model.cfg.variant).value,
        "dataset_digest": file_digest(truth),
        "knot_threshold": threshold,
        "max_knots": m,
    }
    if model.weights_digest is not None:
        header["weights_digest"] = model.weights_digest
    f = AtomicFile(Path(out))
    f.write((canonical_json(header) + "\n").encode("utf-8"))
    late = model.cfg.variant == DetectorVariant.time_late
    n = 0
    try:
        for a in range(0, len(batch_all), chunk):
            b = slice_batch(batch_all, a, min(a + chunk, len(batch_all)))
            r = b.t.shape[1]

            def d(x: np.ndarray) -> torch.Tensor:
                return torch.from_numpy(np.ascontiguousarray(x, dtype=np.float64))

            window = d(b.mask)
            valid = d(b.valid) * window
            x = features(d(b.bearing), valid, d(b.own), d(b.t), window)
            last = b.samples.astype(np.int64) - 1
            if late:
                query = torch.from_numpy(last[:, None].copy())
            else:
                idx = np.arange(r)[None, :]
                query = torch.from_numpy(np.where(idx <= last[:, None], idx, -1))
            o = model(x, window, query)
            p_change = o.p_change.numpy()
            w = o.w_change.numpy()
            pk = o.p_kind.numpy()
            for s in range(len(b)):
                ns = int(b.samples[s])
                dt = float(b.t[s, 1] - b.t[s, 0]) if ns > 1 else 10.0
                ls = int(last[s])
                q_last = 0 if late else ls
                sets = []
                for k in g5_query_rows(int(b.zig_index[s]), ns, dt) + [ls]:
                    q = q_last if late else k
                    sets.append(
                        {
                            "query_row": ls if late else k,
                            "knots": _knots_json(
                                w[s, q], pk[s, q], ls if late else k, threshold, m
                            ),
                        }
                    )
                rec = {
                    "record": "detector",
                    "scenario_index": int(b.index[s]),
                    "p_change": [f32(float(v)) for v in p_change[s, :ns]],
                    "p_kind_last": [f32(float(v)) for v in pk[s, q_last, :ns]],
                    "knot_sets": _dedupe(sets),
                }
                f.write((canonical_json(rec) + "\n").encode("utf-8"))
                n += 1
        f.commit()
    except BaseException:
        f.abort()
        raise
    return n


def _dedupe(sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One knot set per query row (the time-late detector asks one question; a window ending on
    a G5 row asks it twice)."""
    seen: dict[int, dict[str, Any]] = {}
    for s in sets:
        seen.setdefault(int(s["query_row"]), s)
    return [seen[k] for k in sorted(seen)]
