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
import re
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
from tma2.references.ekf import ekf_predict
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


def parse_ekf_name(name: str) -> tuple[float, float, float]:
    """(σ_a, P0 scale, R scale) from ``ekf-sa<a>[-p<p>][-r<r>]`` (``ekf_name``'s format)."""
    m = re.fullmatch(r"ekf-sa([0-9.e+-]+?)(?:-p([0-9.e+-]+?))?(?:-r([0-9.e+-]+))?", name)
    if m is None:
        raise ValueError(f"not an EKF name: {name}")
    return float(m.group(1)), float(m.group(2) or 1.0), float(m.group(3) or 1.0)


def imm_errors(
    rows: list[Row], data: dict[int, BearingData], truths: dict[int, Truth], imm: str
) -> Errors:
    params = parse_imm_name(imm)
    return tracker_errors(rows, data, truths, lambda d: imm_predict(d, params))


def ekf_errors(
    rows: list[Row], data: dict[int, BearingData], truths: dict[int, Truth], ekf: str
) -> Errors:
    sa, p0, r = parse_ekf_name(ekf)
    return tracker_errors(rows, data, truths, lambda d: ekf_predict(d, sa, p0, r))


def tracker_errors(
    rows: list[Row],
    data: dict[int, BearingData],
    truths: dict[int, Truth],
    predict: Callable[[BearingData], dict[str, Any]],
) -> Errors:
    """A per-timestep tracker's errors at each row (rows it does not report: ∞)."""
    out = np.full((len(rows), 3), np.inf)
    cache: dict[int, dict[float, dict[str, Any]]] = {}
    for q, r in enumerate(rows):
        d = data[r.ordinal]
        if r.ordinal not in cache:
            cache[r.ordinal] = {round(float(x["timestamp_s"]), 3): x for x in predict(d)["rows"]}
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


def lower_median(x: np.ndarray) -> float:
    """The decision record's median convention (``inverted_cdf``: the lower middle value)."""
    return float(np.quantile(x, 0.5, method="inverted_cdf"))


def gap_recovered_cols(cols: dict[str, np.ndarray], seg: str, col: int) -> float:
    one = lower_median(cols["one_leg"][:, col])
    ora = lower_median(cols["oracle"][:, col])
    s = lower_median(cols[seg][:, col])
    return mx.gap_recovered(one, s, ora)


def codes_of(intervals: list[Interval], k: int) -> np.ndarray:
    return to_codes(intervals, k + 1)


# --- detectability (note 08 §2) and its strata (FR-063, SC-006) --------------------------------

DETECTABILITY_BANDS = (13.28, 50.0, 200.0)  # χ²(4) 1% point, then roughly decades
DETECTABLE = DETECTABILITY_BANDS[0]


def detectability(
    layer: PhysicsLayer, data: dict[int, BearingData], metas: dict[int, dict[str, Any]]
) -> dict[int, list[float]]:
    """Each target change's detectability: the physics layer on [0, k], k = min(end + 30, n − 1),
    with every span's true knots, against the same without this span's (a χ² with 4 degrees of
    freedom; note 08's definition, ``leg_spike.detectability``). Spans in the metadata's order."""
    from tma2.detect.confirm import layer_costs

    items: list[tuple[BearingData, int, LayerInputs]] = []
    tags: list[tuple[int, int]] = []
    out: dict[int, list[float]] = {}
    for j, m in metas.items():
        d = data[j]
        spans = m.get("manoeuvres") or []
        out[j] = [math.nan] * len(spans)
        for s_i, sp in enumerate(spans):
            k = min(int(sp["end_index"]) + 30, d.n - 1)
            others = [x for x_i, x in enumerate(spans) if x_i != s_i]
            full = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, spans, False)
            less = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, others, False)
            if full is None or less is None:
                continue
            items += [(d, k, full), (d, k, less)]
            tags.append((j, s_i))
    r_max = max(d.n for d in data.values())
    costs = layer_costs(layer, items, r_max)
    for q, (j, s_i) in enumerate(tags):
        out[j][s_i] = costs[2 * q + 1] - costs[2 * q]
    return out


def band(x: float) -> str:
    if not math.isfinite(x):
        return "unknown"
    lo = 0.0
    for e in DETECTABILITY_BANDS:
        if x < e:
            return f"{lo:g}-{e:g}"
        lo = e
    return f">={lo:g}"


def row_band(meta: dict[str, Any], k: int, det: list[float]) -> str:
    """A G5 row's stratum: the detectability band of the last target change begun by row k, or
    ``none`` when no change has begun."""
    spans = meta.get("manoeuvres") or []
    last = [i for i, s in enumerate(spans) if int(s["start_index"]) <= k]
    return band(det[last[-1]]) if last else "none"


def ownship_contamination(
    own: np.ndarray, meta: dict[str, Any], k: int, p: SegmentParameters
) -> float:
    """S1's measure on one prefix: O's contamination against the ownship truth labels on rows
    0 … k (``own`` columns 3 and 4 are course and speed)."""
    from . import to_codes
    from .metrics import contamination
    from .ownship import segment_ownship

    pred = to_codes(segment_ownship(own[:, 3], own[:, 4], k, p), k + 1)
    truth = truth_codes(meta, "ownship", p.l_min_rows, p.t_min_rows, n=k + 1)
    return contamination(pred, truth)


# --- Reporting beside the gate (constitution IV, FR-063; Gate S panel round 1) ---------------


def naive_errors(
    rows: list[Row],
    owns: dict[int, np.ndarray],
    obss: dict[int, np.ndarray],
    truths: dict[int, Truth],
    model: dict[str, Any],
) -> Errors:
    """The naive baseline (training-set means, ``tma2-naive``'s per-timestep model) at each row."""
    from tma2.references.naive import _row as naive_row

    out = np.full((len(rows), 3), np.inf)
    for q, r in enumerate(rows):
        row = naive_row(owns[r.ordinal], obss[r.ordinal], model["per_timestep"], r.k)
        e = row_error(truths[r.ordinal], row, "plausible")
        out[q] = (e.range_rel, e.course_deg, e.speed_kt)
    return out


def bounds(
    rows: list[Row],
    metas: dict[int, dict[str, Any]],
    owns: dict[int, np.ndarray],
    tgts: dict[int, np.ndarray],
    obss: dict[int, np.ndarray],
) -> np.ndarray:
    """Known-manoeuvres Cramér–Rao bounds [rows, 3] (relative range, course °, speed kt) at each
    row: the bound for manoeuvring rows (AGENTS.md); NaN where the information is singular."""
    from tma2.references.crb import crb_rows

    out = np.full((len(rows), 3), np.nan)
    by: dict[int, list[int]] = {}
    for q, r in enumerate(rows):
        by.setdefault(r.ordinal, []).append(q)
    for j, qs in by.items():
        m = metas[j]
        crb = crb_rows(
            owns[j],
            tgts[j],
            obss[j],
            float(m["parameters"]["noise_sigma_rad"]),
            int(m["zig_index"]),
            m.get("manoeuvres") or [],
            [rows[q].k for q in qs],
            model="known_manoeuvres",
            target_manoeuvres=m["parameters"].get("target_manoeuvres") or [],
            fast=True,
        )
        for q, c in zip(qs, crb, strict=True):
            if not c.singular:
                out[q] = (c.sd_range_rel, c.sd_course_deg, c.sd_speed_kt)
    return out


def efficiency_of(e: np.ndarray, sd: np.ndarray) -> float:
    """median(|e| / σ) / 0.6745 over rows with a positive finite bound (``eval.metrics``)."""
    ok = np.isfinite(sd) & (sd > 0)
    if not ok.any():
        return math.nan
    z = np.sort(e[ok] / sd[ok])
    return float(z[(z.size - 1) // 2]) / 0.6744897501960817  # lower median, as _q's inverted_cdf


def _changes_by(meta: dict[str, Any], k: int) -> list[dict[str, Any]]:
    return [s for s in meta.get("manoeuvres") or [] if int(s["start_index"]) <= k]


def strata(meta: dict[str, Any], own: np.ndarray, tgt: np.ndarray, k: int) -> dict[str, str]:
    """FR-063's row strata: range band at k, number of target changes begun by k, and the kind,
    speed-only flag and duration of the latest one."""
    from tma2.eval.slices import RANGE_BANDS_KM
    from tma2.eval.slices import band as slice_band

    rng_km = math.hypot(float(tgt[k, 1] - own[k, 1]), float(tgt[k, 2] - own[k, 2])) / 1000.0
    ch = _changes_by(meta, k)
    n = len(ch)
    bands = ((0, "0"), (5, "1-5"), (10, "6-10"), (20, "11-20"))
    count = next((lab for lim, lab in bands if n <= lim), ">20")
    last = max(ch, key=lambda s: int(s["start_index"])) if ch else None
    kind = "none" if last is None else str(last["kind"])
    if last is None:
        dur = "none"
    else:
        rows_ = int(last["end_index"]) - int(last["start_index"])
        dur = "<10 rows" if rows_ < 10 else "10-20 rows" if rows_ <= 20 else ">20 rows"
    return {
        "range_band": slice_band(rng_km, RANGE_BANDS_KM, "km"),
        "changes": count,
        "latest_kind": kind,
        "speed_only": "yes" if kind == "speed" else "no",
        "latest_duration": dur,
    }
