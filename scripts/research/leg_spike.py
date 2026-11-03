"""Leg-detection research spike (docs/research/08): every candidate detector scored on SRD Annex A
§A.3's detection metrics, on validation seed 304 only (test seed 305 stays reserved).

Scenarios are the σ = 1° scenarios of the validation split in file order. The first ``--tune``
(500, the rows note 07's pilot was tuned on) set thresholds; the next ``--score`` (1,000, untouched
so far) are scored. Thresholds for per-row statistics are tuned to a false-alarm fraction over all
held-leg rows (``settled_row``, k ≥ W) of the tuning scenarios.

Stages, each resumable, writing to ``--work`` (scratch) and finally to ``--out``:

    stats    per-row statistics (split, GLR, CUSUM, IMM μ_CT, steady-leg fit ok) for all
             scenarios, and each scored span's detectability (the physics layer's cost drop from
             its true knots, with the other spans' knots in place)
    confirm  nominate-then-confirm knots on the scored scenarios, sharded across processes
    report   detection metrics, matched-false-alarm comparisons, downstream error and intervals
    samples  per-row Steady Leg flags and tracks for a few scored scenarios (for the slides)

    uv run python scripts/research/leg_spike.py stats --validation data/gd-val/validation.f32pack \
        --work <dir>
    uv run python scripts/research/leg_spike.py confirm --validation … --work <dir> \
        --configs split:0.1:13.8,split:0.2:13.8 --workers 4
    uv run python scripts/research/leg_spike.py report --validation … --work <dir> --out <exp dir>
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.cli.controls import held_g5_rows
from tma2.cli.oracle import run_layer
from tma2.data.f32pack import iter_pack_raw
from tma2.detect.confirm import Accepted, confirm_knots, knot_inputs, knots_at, layer_costs
from tma2.detect.controls import (
    CUSUM_DRIFT,
    GLR_WINDOW,
    cusum_ls_stat,
    glr_stat,
    imm_mode_stat,
    ls_states,
    parse_imm_name,
    tune_threshold,
)
from tma2.detect.matching import episodes, score_scenario, summary
from tma2.detect.steady_leg import split_stat, window_fits
from tma2.eval.bootstrap import (
    bootstrap_clustered_quantile_ratio,
    bootstrap_clustered_rate_difference,
)
from tma2.eval.errors import Truth, row_error
from tma2.eval.rows import G5_GATE_MIN, settled_row
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, oracle_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays, classical_predict
from tma2.references.imm import imm_predict

IMM = "imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16"
W = 36
STEP = 3
FARS = (0.01, 0.03, 0.05, 0.1)
G5_FARS = (0.02, 0.05)  # held-leg G5 rows: Gate D's D-false measure (limit 5%)
PER_ROW = ("split", "glr", "cusum", "imm")
TOL_ROWS = 6  # ±60 s at 10 s
LEVEL = 0.975
RESAMPLES = 2000
KT = 3600.0 / 1852.0
DETECTABILITY_BANDS = (13.28, 50.0, 200.0)  # χ²(4) 1% point, then decades-ish
ANGLE_BANDS = (30.0, 60.0, 90.0)


# ---------------------------------------------------------------- data


def sigma1(meta: dict[str, Any]) -> bool:
    return abs(float(meta["parameters"]["noise_sigma_rad"]) - math.pi / 180) <= 1e-6


def iter_selected(path: str, start: int, count: int) -> Iterator[tuple[int, Any, Any, Any, Any]]:
    """(σ = 1° ordinal, meta, own, tgt, obs) for ordinals start … start + count − 1."""
    j = 0
    for _, meta, own, tgt, obs in iter_pack_raw(path):
        if not sigma1(meta):
            continue
        if j >= start + count:
            return
        if j >= start:
            yield j, meta, own, tgt, obs
        j += 1


def held_rows(meta: dict[str, Any], n: int) -> list[int]:
    return [k for k in range(W, n) if settled_row(meta, k)]


def g5_rows(meta: dict[str, Any], n: int) -> list[int]:
    dt = float(meta["parameters"]["dt_s"])
    ks = (int(meta["zig_index"]) + int(round(m * 60 / dt)) for m in G5_GATE_MIN)
    return [k for k in ks if k < n]


def wrap_deg(x: float) -> float:
    return abs(math.degrees(math.atan2(math.sin(x), math.cos(x))))


def span_size(sp: dict[str, Any], tgt: np.ndarray) -> float:
    """Course change (deg) or speed change (kt) across the span."""
    a, b = int(sp["start_index"]) - 1, min(int(sp["end_index"]), tgt.shape[0] - 1)
    if sp["kind"] == "course":
        return wrap_deg(float(tgt[b, 3] - tgt[a, 3]))
    return abs(float(tgt[b, 4] - tgt[a, 4])) * KT


def band(x: float, edges: tuple[float, ...], fmt: str) -> str:
    lo = 0.0
    for e in edges:
        if x < e:
            return f"{fmt.format(lo)}–{fmt.format(e)}"
        lo = e
    return f"≥{fmt.format(lo)}"


# ---------------------------------------------------------------- stats


def cmd_stats(a: argparse.Namespace) -> int:
    torch.set_default_dtype(torch.float64)
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    out = work / "stats.pkl"
    if out.exists():
        print(f"{out} exists")
        return 0
    imm = parse_imm_name(IMM)
    recs: list[dict[str, Any]] = []
    t0 = time.time()
    for j, meta, own, _tgt, obs in iter_selected(a.validation, 0, a.tune + a.score):
        d = bearing_data_from_arrays(meta, own, obs)
        z0 = np.zeros(d.n, dtype=np.int64)
        st, ok, _mis = window_fits(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, W, z0)
        lam, where = split_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, W, z0)
        lst, lok = ls_states(d, classical_predict(d, "per_timestep")["rows"])
        recs.append(
            {
                "ordinal": j,
                "index": int(meta["index"]),
                "set": "tune" if j < a.tune else "score",
                "split": lam,
                "split_row": where,
                "sl_ok": ok,
                "glr": glr_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, lst, lok, GLR_WINDOW),
                "cusum": cusum_ls_stat(
                    d.t, d.ox, d.oy, d.z, d.valid, d.sigma, lst, lok, CUSUM_DRIFT
                ),
                "imm": imm_mode_stat(d, imm),
            }
        )
        if len(recs) % 100 == 0:
            print(f"{len(recs)} scenarios [{time.time() - t0:.0f} s]", flush=True)
    detectability(a.validation, a.tune, a.score, recs)
    with open(out, "wb") as f:
        pickle.dump(recs, f)
    print(f"stats: {len(recs)} scenarios [{time.time() - t0:.0f} s]", flush=True)
    return 0


def detectability(path: str, tune: int, score: int, recs: list[dict[str, Any]]) -> None:
    """Each scored span's cost drop: the layer on [0, k], k = min(end + 30, n − 1), with every
    span's true knots against the same without this span's (χ² with 4 degrees of freedom)."""
    layer = PhysicsLayer()
    by_ord = {r["ordinal"]: r for r in recs}
    items: list[tuple[BearingData, int, LayerInputs]] = []
    tags: list[tuple[int, int, bool]] = []
    data: list[BearingData] = []
    for j, meta, own, _tgt, obs in iter_selected(path, tune, score):
        d = bearing_data_from_arrays(meta, own, obs)
        data.append(d)
        spans = meta.get("manoeuvres") or []
        by_ord[j]["detectability"] = [math.nan] * len(spans)
        for s_i, sp in enumerate(spans):
            k = min(int(sp["end_index"]) + 30, d.n - 1)
            others = [x for x_i, x in enumerate(spans) if x_i != s_i]
            full = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, spans, False)
            less = oracle_inputs(d.t, d.ox, d.oy, d.z, d.valid, k, others, False)
            if full is None or less is None:
                continue
            items += [(d, k, full), (d, k, less)]
            tags += [(j, s_i, True), (j, s_i, False)]
    r_max = max(d.n for d in data)
    costs = layer_costs(layer, items, r_max)
    for i in range(0, len(tags), 2):
        j, s_i, _ = tags[i]
        by_ord[j]["detectability"][s_i] = costs[i + 1] - costs[i]


# ---------------------------------------------------------------- thresholds


def load_stats(work: str) -> list[dict[str, Any]]:
    with open(Path(work) / "stats.pkl", "rb") as f:
        recs: list[dict[str, Any]] = pickle.load(f)
    return recs


def thresholds(recs: list[dict[str, Any]], metas: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Per statistic and target false-alarm fraction, the threshold tuned on the tuning
    scenarios' held-leg rows."""
    out: dict[str, Any] = {}
    for name in PER_ROW:
        vals = np.concatenate(
            [
                r[name][held_rows(metas[r["ordinal"]], r[name].shape[0])]
                for r in recs
                if r["set"] == "tune"
            ]
        )
        out[name] = {}
        for q in FARS:
            h, f = tune_threshold(vals, q)
            out[name][str(q)] = {"threshold": h, "achieved": f}
        g5 = np.concatenate(
            [r[name][held_g5_rows(metas[r["ordinal"]])] for r in recs if r["set"] == "tune"]
        )
        for q in G5_FARS:
            h, f = tune_threshold(g5, q)
            out[name][f"g5:{q}"] = {"threshold": h, "achieved": f}
    return out


def config_threshold(nom: str, q: float, recs: list[dict[str, Any]], metas: Any) -> float:
    vals = np.concatenate(
        [
            r[nom][held_rows(metas[r["ordinal"]], r[nom].shape[0])]
            for r in recs
            if r["set"] == "tune"
        ]
    )
    return tune_threshold(vals, q)[0]


def tune_metas(path: str, tune: int) -> dict[int, dict[str, Any]]:
    return {j: meta for j, meta, *_ in iter_selected(path, 0, tune)}


# ---------------------------------------------------------------- confirm


def parse_configs(s: str) -> list[tuple[str, float, float]]:
    out: list[tuple[str, float, float]] = []
    for c in filter(None, s.split(",")):
        nom, q, tau = c.split(":")
        out.append((nom, float(q), float(tau)))
    return out


def config_name(nom: str, q: float, tau: float) -> str:
    return f"{nom}-q{q:g}-t{tau:g}"


def confirm_task(args: tuple[str, str, int, int, str, float, float, float, int, int]) -> str:
    path, work, tune, score, nom, q, tau, h, shard, shards = args
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64)
    out = Path(work) / "confirm" / f"{config_name(nom, q, tau)}-s{shard}of{shards}.json"
    if out.exists():
        return f"{out.name} (cached)"
    recs = {r["ordinal"]: r for r in load_stats(work) if r["set"] == "score"}
    data: list[BearingData] = []
    stats: list[np.ndarray] = []
    ords: list[int] = []
    for j, meta, own, _tgt, obs in iter_selected(path, tune, score):
        if (j - tune) % shards != shard:
            continue
        data.append(bearing_data_from_arrays(meta, own, obs))
        stats.append(recs[j][nom])
        ords.append(j)
    t0 = time.time()
    acc = confirm_knots(PhysicsLayer(), data, stats, h, tau, W, STEP, max(d.n for d in data))
    rec = {
        "config": config_name(nom, q, tau),
        "threshold": h,
        "seconds": time.time() - t0,
        "knots": {
            str(j): [[x.alarm, x.alarm_end, x.row, x.cost_drop] for x in kn]
            for j, kn in zip(ords, acc, strict=True)
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec))
    tmp.rename(out)
    return f"{out.name} [{rec['seconds']:.0f} s]"


def cmd_confirm(a: argparse.Namespace) -> int:
    recs = load_stats(a.work)
    metas = tune_metas(a.validation, a.tune)
    tasks = []
    for nom, q, tau in parse_configs(a.configs):
        h = config_threshold(nom, q, recs, metas)
        for s in range(a.shards):
            tasks.append((a.validation, a.work, a.tune, a.score, nom, q, tau, h, s, a.shards))
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for msg in ex.map(confirm_task, tasks):
            print(msg, flush=True)
    return 0


def load_confirmed(work: str, name: str) -> dict[int, list[Accepted]]:
    out: dict[int, list[Accepted]] = {}
    files = sorted((Path(work) / "confirm").glob(f"{name}-s*of*.json"))
    if not files:
        raise FileNotFoundError(f"no confirm shards for {name}")
    shards = int(files[0].stem.split("of")[-1])
    if len(files) != shards:
        raise FileNotFoundError(f"{name}: {len(files)} of {shards} shards")
    for p in files:
        for j, kn in json.loads(p.read_text())["knots"].items():
            out[int(j)] = [Accepted(int(x[0]), int(x[1]), int(x[2]), float(x[3])) for x in kn]
    return out


# ---------------------------------------------------------------- report


def alarm_from_confirmed(n: int, acc: list[Accepted]) -> np.ndarray:
    al = np.zeros(n, dtype=bool)
    for x in acc:
        al[x.alarm : x.alarm_end + 1] = True
    return al


def span_table(
    meta: dict[str, Any],
    tgt: np.ndarray,
    al: np.ndarray,
    knots: list[int] | None,
    detect: list[float],
) -> list[dict[str, Any]]:
    """Per span: resolved, detected, delay, kind, size band, detectability band, localisation.

    ``detected`` is Annex A's rule (an alarm row in [start − 1, end + 30]); ``onset`` asks for an
    alarm episode that *begins* there, so a statistic that is already raised (CUSUM after a first
    manoeuvre) does not detect the next manoeuvre with zero delay."""
    n = int(meta["samples"])
    dt = float(meta["parameters"]["dt_s"])
    rows = []
    rising = np.flatnonzero(al & ~np.concatenate([[False], al[:-1]]))
    for s_i, sp in enumerate(meta.get("manoeuvres") or []):
        a, b = int(sp["start_index"]) - 1, int(sp["end_index"]) + 30
        hit = np.flatnonzero(al[max(a, 0) : min(b, n - 1) + 1])
        onset = rising[(rising >= max(a, 0)) & (rising <= min(b, n - 1))]
        loc = None
        if knots:
            near = [r for r in knots if a - TOL_ROWS <= r <= int(sp["end_index"]) + TOL_ROWS]
            if near:
                loc = min(min(abs(r - a), abs(r - int(sp["end_index"]))) for r in near)
        size = span_size(sp, tgt)
        rows.append(
            {
                "resolved": b < n or bool(hit.size),
                "complete": b < n,
                "window_rows": b - a + 1,
                "detected": bool(hit.size),
                "delay_s": float(hit[0]) * dt if hit.size else None,
                "onset": bool(onset.size),
                "onset_delay_s": float(onset[0] - a) * dt if onset.size else None,
                "kind": sp["kind"],
                "size_band": band(size, ANGLE_BANDS, "{:.0f}°")
                if sp["kind"] == "course"
                else "speed",
                "detectability": detect[s_i],
                "detect_band": band(detect[s_i], DETECTABILITY_BANDS, "{:.0f}")
                if math.isfinite(detect[s_i])
                else "n/a",
                "segmented": loc is not None,
                "localisation_rows": loc,
            }
        )
    return rows


def knot_precision(meta: dict[str, Any], knots: list[int]) -> tuple[int, int]:
    spans = meta.get("manoeuvres") or []
    good = sum(
        1
        for r in knots
        if any(
            int(s["start_index"]) - 1 - TOL_ROWS <= r <= int(s["end_index"]) + TOL_ROWS
            for s in spans
        )
    )
    return good, len(knots)


def describe(
    name: str,
    scen: list[tuple[int, dict[str, Any], np.ndarray, np.ndarray]],
    alarms: dict[int, np.ndarray],
    knots: dict[int, list[int]] | None,
    recs: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    scored = []
    spans: list[dict[str, Any]] = []
    held_n = held_hit = held_onsets = 0
    good = total = 0
    for j, meta, tgt, _own in scen:
        n = int(meta["samples"])
        al = alarms[j]
        kn = knots[j] if knots is not None else None
        det = {
            "p_change": al.astype(float).tolist(),
            "knot_sets": [{"query_row": n - 1, "knots": [{"row": r, "p_kind": 1.0} for r in kn]}]
            if kn
            else [],
        }
        scored.append(score_scenario(meta, det, name))
        for row in span_table(meta, tgt, al, kn, recs[j]["detectability"]):
            row["ordinal"] = j
            spans.append(row)
        hr = held_rows(meta, n)
        held_n += len(hr)
        held_hit += int(al[hr].sum())
        held_set = set(hr)
        prev = np.concatenate([[False], al[:-1]])
        held_onsets += sum(1 for k in np.flatnonzero(al & ~prev) if int(k) in held_set)
        if kn is not None:
            g, t = knot_precision(meta, kn)
            good += g
            total += t
    s = summary(scored)
    out = {
        k: s[k]
        for k in (
            "spans",
            "miss_rate",
            "delay_median_s",
            "delay_p90_s",
            "held_leg_g5_false_alarm",
            "held_leg_alarms_per_hour",
            "segmentation_precision",
            "segmentation_recall",
            "segmentation_f1",
        )
    }
    out["held_row_false_alarm"] = held_hit / held_n if held_n else math.nan
    res = [r for r in spans if r["resolved"]]
    # Chance floor: the probability that an alarm episode begins somewhere in a detection window
    # of the mean length by chance, at the held-leg onset rate (Poisson approximation).
    rate = held_onsets / held_n if held_n else math.nan
    length = float(np.mean([r["window_rows"] for r in spans if r["complete"]] or [math.nan]))
    out["held_onsets_per_row"] = rate
    out["window_rows_mean"] = length
    out["chance_onset_recall"] = 1.0 - math.exp(-rate * length)
    out["recall"] = sum(r["detected"] for r in res) / len(res) if res else math.nan
    out["onset_recall"] = sum(r["onset"] for r in res) / len(res) if res else math.nan
    od = [r["onset_delay_s"] for r in res if r["onset"]]
    out["onset_delay_median_s"] = float(np.median(od)) if od else math.nan
    for key, field in (("by_kind", "kind"), ("by_size", "size_band"), ("by_detect", "detect_band")):
        groups: dict[str, list[dict[str, Any]]] = {}
        for r in res:
            groups.setdefault(r[field], []).append(r)
        out[key] = {
            g: {
                "spans": len(v),
                "recall": sum(r["detected"] for r in v) / len(v),
                "onset_recall": sum(r["onset"] for r in v) / len(v),
                "delay_median_s": float(np.median([r["delay_s"] for r in v if r["detected"]]))
                if any(r["detected"] for r in v)
                else math.nan,
            }
            for g, v in sorted(groups.items())
        }
    if knots is not None:
        locs = [r["localisation_rows"] for r in res if r["localisation_rows"] is not None]
        seg = sum(r["segmented"] for r in res) / len(res) if res else math.nan
        prec = good / total if total else math.nan
        out["knots_per_scenario"] = total / len(scen)
        out["span_recall"] = seg
        out["knot_precision"] = prec
        out["span_f1"] = 2 * seg * prec / (seg + prec) if seg + prec > 0 else math.nan
        out["localisation_median_s"] = float(np.median(locs)) * 10.0 if locs else math.nan
    out["_spans"] = spans
    return out


def downstream(
    scen: list[tuple[int, dict[str, Any], np.ndarray, np.ndarray]],
    data: dict[int, BearingData],
    truths: dict[int, Truth],
    make: Any,
) -> list[tuple[int, int, float, float, float, bool]]:
    """(ordinal, row, range rel, course deg, speed kt, settled) on every G5 row; a row without
    inputs or with an implausible solution counts as an infinite error."""
    layer = PhysicsLayer()
    items: list[tuple[BearingData, int, LayerInputs]] = []
    keys: list[tuple[int, int, bool]] = []
    out: list[tuple[int, int, float, float, float, bool]] = []
    for j, meta, _tgt, _own in scen:
        d = data[j]
        for k in g5_rows(meta, d.n):
            st = settled_row(meta, k)
            inp = make(j, meta, d, k)
            if inp is None:
                out.append((j, k, math.inf, math.inf, math.inf, st))
                continue
            items.append((d, k, inp))
            keys.append((j, k, st))
    r_max = max(d.n for d in data.values())
    for s in range(0, len(items), 256):
        res = run_layer(layer, items[s : s + 256], r_max)
        for b, (j, k, st) in enumerate(keys[s : s + 256]):
            x = res.state[b].numpy()
            row = {
                "timestamp_s": float(data[j].t[k]),
                "range_m": float(res.range[b]),
                "course_rad": float(res.course[b]),
                "speed_mps": float(res.speed[b]),
                "x_m": float(x[0]),
                "y_m": float(x[1]),
                "converged": bool(res.plausible[b]),
            }
            e = row_error(truths[j], row, "plausible")
            out.append((j, k, e.range_rel, e.course_deg, e.speed_kt, st))
    return sorted(out)


def imm_downstream(
    scen: list[tuple[int, dict[str, Any], np.ndarray, np.ndarray]],
    data: dict[int, BearingData],
    truths: dict[int, Truth],
) -> list[tuple[int, int, float, float, float, bool]]:
    imm = parse_imm_name(IMM)
    out = []
    for j, meta, _tgt, _own in scen:
        d = data[j]
        rows = {round(float(r["timestamp_s"]), 3): r for r in imm_predict(d, imm)["rows"]}
        for k in g5_rows(meta, d.n):
            r = rows.get(round(float(d.t[k]), 3))
            e = row_error(truths[j], r, "plausible") if r else None
            st = settled_row(meta, k)
            out.append(
                (j, k, e.range_rel, e.course_deg, e.speed_kt, st)
                if e
                else (j, k, math.inf, math.inf, math.inf, st)
            )
    return sorted(out)


def med(rows: list[tuple[int, int, float, float, float, bool]], col: int, settled: bool) -> float:
    v = [r[col] for r in rows if r[5] or not settled]
    return float(np.median(v)) if v else math.nan


def ratio(
    a: list[tuple[int, int, float, float, float, bool]],
    b: list[tuple[int, int, float, float, float, bool]],
    col: int,
    settled: bool,
) -> dict[str, float]:
    if [r[:2] for r in a] != [r[:2] for r in b]:
        raise ValueError("downstream rows differ")
    keep = [i for i, r in enumerate(a) if r[5] or not settled]
    x = np.array([a[i][col] for i in keep])
    y = np.array([b[i][col] for i in keep])
    cl = np.array([a[i][0] for i in keep], dtype=np.int64)
    ri = bootstrap_clustered_quantile_ratio(x, y, cl, 0.5, LEVEL, RESAMPLES)
    return {"ratio": ri.ratio, "lo": ri.lo, "hi": ri.hi, "rows": ri.n, "clusters": ri.clusters}


def miss_difference(a: dict[str, Any], b: dict[str, Any], field: str) -> dict[str, float]:
    """Paired, scenario-clustered difference of miss rates (a − b) over the spans whose
    detection window lies inside the scenario, ``field`` the detection rule."""
    pairs = [(x, y) for x, y in zip(a["_spans"], b["_spans"], strict=True) if x["complete"]]
    x = np.array([not p[0][field] for p in pairs], dtype=float)
    y = np.array([not p[1][field] for p in pairs], dtype=float)
    cl = np.array([p[0]["ordinal"] for p in pairs], dtype=np.int64)
    di = bootstrap_clustered_rate_difference(x, y, cl, LEVEL, RESAMPLES)
    return {"difference": di.difference, "lo": di.lo, "hi": di.hi}


def cmd_report(a: argparse.Namespace) -> int:
    torch.set_default_dtype(torch.float64)
    t0 = time.time()
    recs_all = load_stats(a.work)
    metas_t = tune_metas(a.validation, a.tune)
    recs = {r["ordinal"]: r for r in recs_all if r["set"] == "score"}
    scen: list[tuple[int, dict[str, Any], np.ndarray, np.ndarray]] = []
    data: dict[int, BearingData] = {}
    truths: dict[int, Truth] = {}
    for j, meta, own, tgt, obs in iter_selected(a.validation, a.tune, a.score):
        scen.append((j, meta, tgt.astype(np.float64), own))
        data[j] = bearing_data_from_arrays(meta, own, obs)
        truths[j] = Truth.from_block(meta, own, tgt)
    th = thresholds(recs_all, metas_t)
    result: dict[str, Any] = {
        "validation": a.validation,
        "tune_scenarios": a.tune,
        "score_scenarios": len(scen),
        "window": W,
        "level": LEVEL,
        "resamples": RESAMPLES,
        "thresholds": th,
        "detectors": {},
    }
    det = result["detectors"]
    for name in PER_ROW:
        for q in FARS:
            h = th[name][str(q)]["threshold"]
            al = {j: recs[j][name] > h for j, *_ in scen}
            kn = None
            if name == "split":
                kn = {
                    j: [int(recs[j]["split_row"][e0]) for e0, _e1 in episodes(al[j], 10.0, 0.0)]
                    for j, *_ in scen
                }
            det[f"{name}@{q:g}"] = describe(name, scen, al, kn, recs)
        for q in G5_FARS:
            h = th[name][f"g5:{q}"]["threshold"]
            al = {j: recs[j][name] > h for j, *_ in scen}
            det[f"{name}@g5:{q:g}"] = describe(name, scen, al, None, recs)
        print(f"{name} scored [{time.time() - t0:.0f} s]", flush=True)
    confirmed = parse_configs(a.configs)
    for nom, q, tau in confirmed:
        nm = config_name(nom, q, tau)
        acc = load_confirmed(a.work, nm)
        al = {j: alarm_from_confirmed(int(m["samples"]), acc[j]) for j, m, *_ in scen}
        kn = {j: [x.row for x in acc[j]] for j, *_ in scen}
        det[nm] = describe(nm, scen, al, kn, recs)
        # Matched false alarms: each per-row control at the confirmed detector's own false-alarm
        # fraction, on all held-leg rows and on held-leg G5 rows (Gate D's D-false measure),
        # tuned on the scored rows (in the controls' favour, as Annex A §A.2 tunes controls to
        # the detector's rate).
        det[nm]["matched"] = {}
        for measure, key in (
            ("held_row", "held_row_false_alarm"),
            ("g5", "held_leg_g5_false_alarm"),
        ):
            f = det[nm][key]
            for ctrl in PER_ROW:
                vals = np.concatenate(
                    [
                        recs[j][ctrl][
                            held_rows(m, int(m["samples"]))
                            if measure == "held_row"
                            else held_g5_rows(m)
                        ]
                        for j, m, *_ in scen
                    ]
                )
                h, got = tune_threshold(vals, f)
                alc = {j: recs[j][ctrl] > h for j, *_ in scen}
                dc = describe(ctrl, scen, alc, None, recs)
                det[nm]["matched"][f"{ctrl}@{measure}"] = {
                    "threshold": h,
                    "false_alarm": got,
                    "recall": dc["recall"],
                    "onset_recall": dc["onset_recall"],
                    "chance_onset_recall": dc["chance_onset_recall"],
                    "delay_median_s": dc["delay_median_s"],
                    "onset_delay_median_s": dc["onset_delay_median_s"],
                    "miss_difference": miss_difference(det[nm], dc, "detected"),
                    "onset_miss_difference": miss_difference(det[nm], dc, "onset"),
                }
        print(f"{nm} scored [{time.time() - t0:.0f} s]", flush=True)
    # Downstream on the scored G5 rows.
    ds: dict[str, Any] = {}
    ds["least_squares"] = downstream(
        scen, data, truths, lambda j, m, d, k: knot_inputs(d, k, [], False)
    )
    ds["oracle"] = downstream(
        scen,
        data,
        truths,
        lambda j, m, d, k: oracle_inputs(
            d.t, d.ox, d.oy, d.z, d.valid, k, m.get("manoeuvres"), True
        ),
    )
    ds["imm"] = imm_downstream(scen, data, truths)
    for nom, q, tau in confirmed:
        nm = config_name(nom, q, tau)
        acc = load_confirmed(a.work, nm)
        ds[nm] = downstream(
            scen,
            data,
            truths,
            lambda j, m, d, k, acc=acc: knot_inputs(d, k, knots_at(acc[j], k), True),
        )
        print(f"{nm} downstream [{time.time() - t0:.0f} s]", flush=True)
    result["downstream"] = {
        name: {
            "rows": len(v),
            "settled_rows": sum(1 for r in v if r[5]),
            "range": med(v, 2, False),
            "course_deg": med(v, 3, False),
            "speed_kt": med(v, 4, False),
            "settled_range": med(v, 2, True),
            "settled_course_deg": med(v, 3, True),
            "settled_speed_kt": med(v, 4, True),
        }
        for name, v in ds.items()
    }
    result["intervals"] = {}
    for nom, q, tau in confirmed:
        nm = config_name(nom, q, tau)
        result["intervals"][nm] = {
            "range_vs_imm": ratio(ds[nm], ds["imm"], 2, False),
            "course_vs_imm": ratio(ds[nm], ds["imm"], 3, False),
            "speed_vs_imm": ratio(ds[nm], ds["imm"], 4, False),
            "range_vs_ls": ratio(ds[nm], ds["least_squares"], 2, False),
            "settled_range_vs_ls": ratio(ds[nm], ds["least_squares"], 2, True),
            "settled_course_vs_ls": ratio(ds[nm], ds["least_squares"], 3, True),
            "settled_speed_vs_ls": ratio(ds[nm], ds["least_squares"], 4, True),
        }
    result["seconds"] = time.time() - t0
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    spans = {k: v.pop("_spans") for k, v in det.items()}
    (out / "spike.json").write_text(json.dumps(result, indent=1, default=float))
    with open(Path(a.work) / "spans.pkl", "wb") as f:
        pickle.dump(spans, f)
    print(f"report written [{time.time() - t0:.0f} s]", flush=True)
    return 0


# ---------------------------------------------------------------- samples


def flags(rec: dict[str, Any], acc: list[Accepted], h_nom: float, n: int) -> list[str]:
    """Note 07 §5's Steady Leg flag per row."""
    out = []
    for k in range(n):
        if not rec["sl_ok"][k]:
            out.append("unknown")
        elif any(x.alarm <= k < x.alarm + W for x in acc):
            out.append("changed")
        elif rec["split"][k] > h_nom:
            out.append("suspect")
        else:
            out.append("steady")
    return out


def cmd_samples(a: argparse.Namespace) -> int:
    recs_all = load_stats(a.work)
    metas_t = tune_metas(a.validation, a.tune)
    nom, q, tau = parse_configs(a.config)[0]
    h = config_threshold(nom, q, recs_all, metas_t)
    acc = load_confirmed(a.work, config_name(nom, q, tau))
    recs = {r["ordinal"]: r for r in recs_all}
    want = [int(x) for x in a.ordinals.split(",")]
    out = []
    for j, meta, own, tgt, _obs in iter_selected(a.validation, a.tune, a.score):
        if j not in want:
            continue
        n = int(meta["samples"])
        out.append(
            {
                "ordinal": j,
                "index": int(meta["index"]),
                "dt_s": float(meta["parameters"]["dt_s"]),
                "zig_index": int(meta["zig_index"]),
                "manoeuvres": meta.get("manoeuvres") or [],
                "own": np.round(own.astype(np.float64), 2).tolist(),
                "tgt": np.round(tgt.astype(np.float64), 2).tolist(),
                "flag": flags(recs[j], acc[j], h, n),
                "knots": [[x.alarm, x.row] for x in acc[j]],
                "split": np.round(recs[j]["split"], 2).tolist(),
                "threshold": h,
            }
        )
    Path(a.out).write_text(json.dumps({"config": config_name(nom, q, tau), "scenarios": out}))
    print(f"{len(out)} samples")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("stats", "confirm", "report", "samples"):
        p = sub.add_parser(name)
        p.add_argument("--validation", required=True)
        p.add_argument("--work", required=True)
        p.add_argument("--tune", type=int, default=500)
        p.add_argument("--score", type=int, default=1000)
        if name == "confirm":
            p.add_argument("--configs", required=True)
            p.add_argument("--shards", type=int, default=8)
            p.add_argument("--workers", type=int, default=4)
        if name == "report":
            p.add_argument("--configs", default="")
            p.add_argument("--out", required=True)
        if name == "samples":
            p.add_argument("--config", required=True)
            p.add_argument("--ordinals", required=True)
            p.add_argument("--out", required=True)
    a = ap.parse_args()
    fn = {"stats": cmd_stats, "confirm": cmd_confirm, "report": cmd_report, "samples": cmd_samples}
    return fn[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
