"""Scoring segmentations by what they do to the estimate (spec 005 US2, FR-060–FR-063).

Rows are the σ = 1° G5 rows (zig + 5/10/15/20 min) of the selected scenarios, clustered by
scenario. Scenarios are selected as note 08 did: the σ = 1° scenarios of a split in file order,
numbered from 0 (ordinals), ``start`` … ``start + count − 1``.

Every segmenter's estimate comes from the physics layer fed its segmentation in the hand-over
mode (FR-030). The references on the same rows:
* **one leg** (no transitions: batch least squares, P0's physics ≡ LS);
* **oracle** (the truth spans, chord with the speed prior, ``oracle_inputs``);
* **the frozen IMM** (``imm_predict``);
* **GLR + confirm** (note 08's point knots, read from ``leg_spike.py``'s confirm shards and handed
  over as note 08 did, so its numbers reproduce that record exactly).
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.f32pack import iter_pack_raw
from tma2.detect.confirm import Accepted, window_inputs
from tma2.detect.controls import parse_imm_name
from tma2.eval.errors import Truth, row_error
from tma2.eval.rows import G5_GATE_MIN
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, oracle_inputs
from tma2.references.classical import BearingData
from tma2.references.imm import imm_predict
from tma2.types.generated.tma import SegmentParameters

from . import TRANSITION, Interval, to_codes
from . import metrics as mx
from .inputs import segmentation_inputs
from .truth import change_rows, truth_codes

TOL_ROWS = 6  # ± 60 s
TOL3_ROWS = 18  # ± 3 min (diagnostic)
LAYER_BATCH = 256


def sigma1(meta: dict[str, Any]) -> bool:
    return abs(float(meta["parameters"]["noise_sigma_rad"]) - math.pi / 180) <= 1e-6


def iter_selected(
    path: str | Path, start: int, count: int
) -> Iterator[tuple[int, dict[str, Any], np.ndarray, np.ndarray, np.ndarray]]:
    """(σ = 1° ordinal, meta, own, tgt, obs) for ordinals start … start + count − 1 (note 08's
    selection, ``leg_spike.iter_selected``)."""
    j = 0
    for _, meta, own, tgt, obs in iter_pack_raw(path):
        if not sigma1(meta):
            continue
        if j >= start + count:
            return
        if j >= start:
            yield j, meta, own, tgt, obs
        j += 1


def g5_rows(meta: dict[str, Any], n: int) -> list[int]:
    dt = float(meta["parameters"]["dt_s"])
    ks = (int(meta["zig_index"]) + int(round(m * 60 / dt)) for m in G5_GATE_MIN)
    return [k for k in ks if k < n]


@dataclass(frozen=True)
class Row:
    ordinal: int
    k: int
    settled: bool


Errors = np.ndarray  # [rows, 3]: range relative, course deg, speed kt (∞ where none)
MakeInputs = Callable[[int, dict[str, Any], BearingData, int], LayerInputs | None]


def layer_errors(
    layer: PhysicsLayer,
    rows: list[Row],
    data: dict[int, BearingData],
    metas: dict[int, dict[str, Any]],
    truths: dict[int, Truth],
    make: MakeInputs,
) -> Errors:
    """Errors of the physics layer's estimate at each row; a row without inputs or with an
    implausible solution is an infinite error (note 08's rule)."""
    from tma2.cli.oracle import run_layer

    out = np.full((len(rows), 3), np.inf)
    items: list[tuple[BearingData, int, LayerInputs]] = []
    where: list[int] = []
    for q, r in enumerate(rows):
        d = data[r.ordinal]
        inp = make(r.ordinal, metas[r.ordinal], d, r.k)
        if inp is not None:
            items.append((d, r.k, inp))
            where.append(q)
    r_max = max(d.n for d in data.values())
    for s in range(0, len(items), LAYER_BATCH):
        res = run_layer(layer, items[s : s + LAYER_BATCH], r_max)
        for b, q in enumerate(where[s : s + LAYER_BATCH]):
            d, k, _ = items[s + b]
            x = res.state[b].numpy()
            row = {
                "timestamp_s": float(d.t[k]),
                "range_m": float(res.range[b]),
                "course_rad": float(res.course[b]),
                "speed_mps": float(res.speed[b]),
                "x_m": float(x[0]),
                "y_m": float(x[1]),
                "converged": bool(res.plausible[b]),
            }
            e = row_error(truths[rows[q].ordinal], row, "plausible")
            out[q] = (e.range_rel, e.course_deg, e.speed_kt)
    return out


def imm_errors(
    rows: list[Row], data: dict[int, BearingData], truths: dict[int, Truth], imm: str
) -> Errors:
    params = parse_imm_name(imm)
    out = np.full((len(rows), 3), np.inf)
    cache: dict[int, dict[float, dict[str, Any]]] = {}
    for q, r in enumerate(rows):
        d = data[r.ordinal]
        if r.ordinal not in cache:
            cache[r.ordinal] = {
                round(float(x["timestamp_s"]), 3): x for x in imm_predict(d, params)["rows"]
            }
        row = cache[r.ordinal].get(round(float(d.t[r.k]), 3))
        if row is not None:
            e = row_error(truths[r.ordinal], row, "plausible")
            out[q] = (e.range_rel, e.course_deg, e.speed_kt)
    return out


def one_leg(_j: int, _m: dict[str, Any], d: BearingData, k: int) -> LayerInputs | None:
    return segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, [], "chord", False)


def oracle(_j: int, m: dict[str, Any], d: BearingData, k: int) -> LayerInputs | None:
    return oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, m.get("manoeuvres"), True)


def from_segmentations(
    segs: dict[tuple[int, int], list[Interval]], mode: str, speed_prior: bool = True
) -> MakeInputs:
    def make(j: int, _m: dict[str, Any], d: BearingData, k: int) -> LayerInputs | None:
        ivs = segs.get((j, k))
        if ivs is None:
            return None
        trs = [(iv.start, iv.end) for iv in ivs if iv.kind == TRANSITION]
        return segmentation_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, trs, mode, speed_prior)

    return make


def load_confirmed(work: str | Path, name: str) -> dict[int, list[Accepted]]:
    """GLR + confirm's accepted knots per ordinal (``leg_spike.py confirm`` shards)."""
    out: dict[int, list[Accepted]] = {}
    files = sorted((Path(work) / "confirm").glob(f"{name}-s*of*.json"))
    if not files:
        raise FileNotFoundError(f"no confirm shards for {name} in {work}")
    shards = int(files[0].stem.split("of")[-1])
    if len(files) != shards:
        raise FileNotFoundError(f"{name}: {len(files)} of {shards} shards")
    for p in files:
        for j, kn in json.loads(p.read_text())["knots"].items():
            out[int(j)] = [
                Accepted(
                    int(x[0]), int(x[1]), int(x[2]), float(x[3]), int(x[4]) if len(x) > 4 else -1
                )
                for x in kn
            ]
    return out


def glr_confirm(acc: dict[int, list[Accepted]]) -> MakeInputs:
    def make(j: int, _m: dict[str, Any], d: BearingData, k: int) -> LayerInputs | None:
        return window_inputs(d, k, acc.get(j, []), True)

    return make


def glr_confirm_intervals(acc: list[Accepted], k: int, t_min: int) -> list[tuple[int, int]]:
    """GLR + confirm's knots in use at k as transitions for the segmentation metrics: a turn
    window as itself, a point knot as T_min rows starting at it (its hand-over stays note 08's)."""
    out = []
    for x in acc:
        if x.alarm > k or not 0 < x.row <= k:
            continue
        end = x.end if x.end > 0 else x.row + t_min - 1
        out.append((x.row, min(end, k)))
    return sorted(out)


# --- segmentation metrics per scored prefix -----------------------------------------------


@dataclass
class PrefixMetrics:
    contamination: float
    coverage: float
    changes: int  # truth changes begun by k
    false_split: bool | None
    leg_count_ok: bool | None  # only where every change by k is detectable
    hits60: list[bool]
    hits180: list[bool]


def prefix_metrics(
    pred: list[tuple[int, int]],
    meta: dict[str, Any],
    k: int,
    p: SegmentParameters,
    detectable: list[bool] | None = None,
) -> PrefixMetrics:
    """``pred``: the segmenter's transitions on [0, k]. Truth labels count from the first zig's
    end (R7); changes are the target's spans begun by k."""
    truth = truth_codes(meta, "target", p.l_min_rows, p.t_min_rows, n=k + 1)
    codes = np.full(k + 1, 0, dtype=np.int8)
    for a, b in pred:
        codes[a : b + 1] = TRANSITION
    spans = [(a, min(b, k)) for a, b in change_rows(meta, "target") if a <= k]
    det = detectable if detectable is not None else [True] * len(spans)
    leg_ok: bool | None = None
    if spans and all(det[: len(spans)]):
        leg_ok = len(pred) == len(spans)
    elif not spans:
        leg_ok = len(pred) == 0
    return PrefixMetrics(
        contamination=mx.contamination(codes, truth),
        coverage=mx.coverage(codes, truth),
        changes=len(spans),
        false_split=mx.false_split(pred, len(spans)),
        leg_count_ok=leg_ok,
        hits60=mx.boundary_hits(pred, spans, TOL_ROWS),
        hits180=mx.boundary_hits(pred, spans, TOL3_ROWS),
    )


def gap_recovered_cols(cols: dict[str, np.ndarray], seg: str, col: int) -> float:
    one = float(np.median(cols["one_leg"][:, col]))
    ora = float(np.median(cols["oracle"][:, col]))
    s = float(np.median(cols[seg][:, col]))
    return mx.gap_recovered(one, s, ora)


def codes_of(intervals: list[Interval], k: int) -> np.ndarray:
    return to_codes(intervals, k + 1)
