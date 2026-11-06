"""E's predictions (spec 007 T020): E-s's decisions, then E-w's weights.

* **Segmentation.** With E-s, C's confirmation is re-run with E-s's evidence shifting its
  thresholds (``segment.confirm``'s evidence path) on C's own nominations, in ``tma2-segment``'s
  chunks, so zero evidence reproduces C's segmentation file. Without E-s, C's segmentation file
  is used as it is.
* **Estimate.** E-w (``gate2.model.EWeights``, the solve without implicit differentiation) on
  C's hand-over of that segmentation at each scored row; without E-w, the physics layer alone
  (C's estimate, the knot cap ``KNOTS``).

Rows are written in the oracle's prediction format (``cli.oracle.row_from_output``), so the
scorers read them as any other estimator's; ``converged`` is the solve's plausibility (and, for
E-w, its covariance flag).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch

from tma2.cli.oracle import inputs_for
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs
from tma2.references.classical import BearingData
from tma2.segment import Interval
from tma2.segment.confirm import confirm
from tma2.segment.evidence import EvidenceNet, evidence_for, scenario_features
from tma2.segment.segmenter import intervals_at, nominations_for
from tma2.sim.geometry import f32
from tma2.types.generated.tma import SegmentParameters

from . import KNOTS
from .inputs import code_channel, prefix_inputs
from .model import EWeights


def es_segmentations(
    net: EvidenceNet,
    data: list[BearingData],
    owns: list[np.ndarray],
    rows: list[list[int]],
    p: SegmentParameters,
) -> list[dict[int, list[Interval]]]:
    """E-s's segmentation of each scenario at its rows: C's confirmation with E-s's evidence."""
    feats = [scenario_features(d, own, p) for d, own in zip(data, owns, strict=True)]
    ev = evidence_for(net, feats)
    noms = [nominations_for(d, ks[0], p) for d, ks in zip(data, rows, strict=True)]
    layer = PhysicsLayer()
    confs = confirm(layer, data, noms, p, max(d.n for d in data), evidence=ev)
    return [{k: intervals_at(c, k, p) for k in ks} for c, ks in zip(confs, rows, strict=True)]


def _row(
    d: BearingData, k: int, state: np.ndarray, rcs: tuple[float, float, float], ok: bool
) -> dict[str, Any]:
    """In double, as ``segment.score.layer_errors`` scores C (float32 rows would give E and C a
    last-bits difference in G2-d's paired comparison); the timestamp as the truth stores it."""
    return {
        "timestamp_s": f32(float(d.t[k])),
        "range_m": rcs[0],
        "course_rad": rcs[1],
        "speed_mps": rcs[2],
        "x_m": float(state[0]),
        "y_m": float(state[1]),
        "converged": ok,
        "iterations": 0,
    }


def e_rows(
    model: EWeights | None,
    data: list[BearingData],
    rows: list[list[int]],
    segs: list[dict[int, list[Interval]]],
    mode: str,
    open_handover: str | None,
    batch: int = 32,
) -> list[list[dict[str, Any]]]:
    """Per scenario, a prediction row at each scored row (an empty row where C's hand-over has
    no input or the solve is implausible)."""
    from tma2.cli.oracle import empty_row

    r_max = max(d.n for d in data)
    layer = None if model is not None else PhysicsLayer(knots=KNOTS)
    items: list[tuple[BearingData, int, LayerInputs]] = []
    codes: list[np.ndarray] = []
    where: list[tuple[int, int]] = []
    out: list[list[dict[str, Any]]] = []
    for i, (d, ks, sg) in enumerate(zip(data, rows, segs, strict=True)):
        out.append([empty_row(d, k) for k in ks])
        for q, k in enumerate(ks):
            ivs = sg.get(k)
            if ivs is None:
                continue
            inp = prefix_inputs(d, k, ivs, mode, open_handover)
            if inp is None:
                continue
            items.append((d, k, inp))
            codes.append(np.pad(code_channel(ivs, k, d.n), (0, r_max - d.n)))
            where.append((i, q))
    if model is not None:
        model.eval()
        model.set_implicit(False)
    for s in range(0, len(items), batch):
        x = inputs_for(items[s : s + batch], r_max)
        with torch.no_grad():
            if model is not None:
                code = torch.tensor(np.stack(codes[s : s + batch]), dtype=torch.float64)
                o = model(x, code)
                state, ok = o.state, o.plausible & o.cov_ok
                rng, crs, spd = o.range, o.course, o.speed
            else:
                assert layer is not None
                lo = layer(x)
                state, ok = lo.state, lo.plausible
                rng, crs, spd = lo.range, lo.course, lo.speed
        for b, (i, q) in enumerate(where[s : s + batch]):
            d, k, _ = items[s + b]
            st = state[b].numpy()
            if np.isfinite(st).all():  # an implausible solve is reported, unconverged
                rcs = (float(rng[b]), float(crs[b]), float(spd[b]))
                out[i][q] = _row(d, k, st, rcs, bool(ok[b]))
    return out
