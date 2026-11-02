"""Detection metrics of Annex A §A.3 (spec 004 FR-028; research R8).

Per scenario and detector, from its per-row ``p_change`` (alarm where ≥ the threshold, D1 0.5)
and, for learned detectors, the knots exported at the last row with their kinds:

* **Detection.** A manoeuvre span (start, end) is detected at the first alarm row in
  [start − 1, end + 30] (the manoeuvre begins at row start − 1; 30 rows = 300 s at 10 s); its delay
  is (alarm − (start − 1)) · dt. Without an alarm it is *missed*, unless end + 30 lies beyond the
  window, when it is *unresolved* (reported, not a miss).
* **Held-leg false alarms.** The fraction of σ = 1° held-leg G5 rows (``settled_row``) with an
  alarm, and rising edges per hour of held-leg time: an alarm episode is a run of alarm rows,
  episodes less than 60 s apart are merged, and an episode counts when its first row is held.
* **Kind accuracy.** For each detected span, the last row's exported knot nearest the span's start
  (within the tolerance, D1 ±60 s) is a course change when its p_kind ≥ 0.5; correct when that
  matches the span's kind; no knot within the tolerance: not scored (coverage reported).
* **Segmentation F1.** The last row's exported knots against the span boundaries (start and end,
  adjacent rows merged as the export merges a plateau), matched one-to-one within the tolerance,
  nearest pairs first.
* **Calibration.** Expected calibration error (10 equal-width bins) of p_change against the
  ``now`` label over σ = 1° rows, and of the last row's p_kind at the boundary rows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from tma2.eval.rows import G5_GATE_MIN, G5_SLICE_SIGMA_RAD, settled_row
from tma2.eval.stats import ascending, percentile
from tma2.types.generated.tma import DetectionRecord, SpanDetection

THRESHOLD = 0.5
TOLERANCE_S = 60.0
RESOLVE_ROWS = 30
MERGE_S = 60.0
ECE_BINS = 10


def alarms(p_change: list[float] | np.ndarray, threshold: float = THRESHOLD) -> np.ndarray:
    return np.asarray(p_change, dtype=np.float64) >= threshold


def episodes(alarm: np.ndarray, dt: float, merge_s: float = MERGE_S) -> list[tuple[int, int]]:
    """(first, last) rows of alarm episodes, runs less than ``merge_s`` apart merged."""
    runs: list[tuple[int, int]] = []
    i = 0
    n = alarm.shape[0]
    while i < n:
        if not alarm[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and alarm[j + 1]:
            j += 1
        if runs and (i - runs[-1][1]) * dt < merge_s:
            runs[-1] = (runs[-1][0], j)
        else:
            runs.append((i, j))
        i = j + 1
    return runs


def truth_boundaries(spans: list[dict[str, Any]]) -> list[int]:
    rows = sorted({int(s[k]) for s in spans for k in ("start_index", "end_index")})
    return [r for r in rows if r - 1 not in rows]


def match_one_to_one(pred: list[int], truth: list[int], tol_rows: float) -> int:
    """Matched pairs within ±tol_rows, nearest first (each row used once)."""
    pairs = sorted(
        (abs(p - t), i, j)
        for i, p in enumerate(pred)
        for j, t in enumerate(truth)
        if abs(p - t) <= tol_rows
    )
    used_p: set[int] = set()
    used_t: set[int] = set()
    for _, i, j in pairs:
        if i not in used_p and j not in used_t:
            used_p.add(i)
            used_t.add(j)
    return len(used_p)


@dataclass
class ScenarioDetection:
    record: DetectionRecord
    knots_exported: int = 0
    boundaries: int = 0
    boundaries_matched: int = 0
    kind_scored: int = 0
    kind_correct: int = 0
    calibration_now: list[tuple[float, float]] = field(default_factory=list)
    calibration_kind: list[tuple[float, float]] = field(default_factory=list)


def score_scenario(
    meta: dict[str, Any],
    det: dict[str, Any],
    detector: str,
    threshold: float = THRESHOLD,
    tolerance_s: float = TOLERANCE_S,
    now_labels: np.ndarray | None = None,
) -> ScenarioDetection:
    """One scenario's detections: ``meta`` the truth metadata, ``det`` its DetectorRecord (raw)."""
    n = int(meta["samples"])
    dt = float(meta["parameters"]["dt_s"])
    tol = tolerance_s / dt
    p = np.asarray(det["p_change"], dtype=np.float64)[:n]
    al = alarms(p, threshold)
    spans = meta.get("manoeuvres") or []
    last_sets = [s for s in det.get("knot_sets") or [] if int(s["query_row"]) == n - 1]
    knots = last_sets[0]["knots"] if last_sets else []
    knot_rows = [int(k["row"]) for k in knots]
    out_spans: list[SpanDetection] = []
    kind_scored = kind_correct = 0
    for s in spans:
        a = int(s["start_index"]) - 1
        b = int(s["end_index"]) + RESOLVE_ROWS
        hit = np.flatnonzero(al[max(a, 0) : min(b, n - 1) + 1])
        if hit.size:
            row = max(a, 0) + int(hit[0])
            sd = SpanDetection(
                kind=str(s["kind"]),
                start_index=int(s["start_index"]),
                end_index=int(s["end_index"]),
                outcome="detected",
                alarm_index=row,
                delay_s=(row - a) * dt,
            )
            if knots:
                j = int(np.argmin([abs(r - int(s["start_index"])) for r in knot_rows]))
                if abs(knot_rows[j] - int(s["start_index"])) <= tol:
                    sd.kind_correct = (float(knots[j]["p_kind"]) >= 0.5) == (s["kind"] == "course")
                    kind_scored += 1
                    kind_correct += int(sd.kind_correct)
        else:
            outcome = "unresolved" if b >= n else "missed"
            sd = SpanDetection(
                kind=str(s["kind"]),
                start_index=int(s["start_index"]),
                end_index=int(s["end_index"]),
                outcome=outcome,
            )
        out_spans.append(sd)
    held = np.array([settled_row(meta, k) for k in range(n)], dtype=bool)
    eps = episodes(al, dt)
    sigma1 = abs(float(meta["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) <= 1e-6
    g5 = [int(meta["zig_index"]) + int(round(m * 60 / dt)) for m in G5_GATE_MIN]
    g5_held = [k for k in g5 if k < n and held[k]] if sigma1 else []
    rec = DetectionRecord(
        scenario_index=int(meta["index"]),
        detector=detector,
        spans=out_spans,
        held_leg_seconds=float(held.sum()) * dt,
        held_leg_alarms=sum(1 for e0, _ in eps if held[e0]),
        held_leg_g5_rows=len(g5_held),
        held_leg_g5_flagged=sum(1 for k in g5_held if al[k]),
    )
    bounds = truth_boundaries(spans)
    sc = ScenarioDetection(
        record=rec,
        knots_exported=len(knot_rows),
        boundaries=len(bounds),
        boundaries_matched=match_one_to_one(knot_rows, bounds, tol),
        kind_scored=kind_scored,
        kind_correct=kind_correct,
    )
    if sigma1 and now_labels is not None:
        sc.calibration_now = [(float(p[k]), float(now_labels[k])) for k in range(n)]
    pk = det.get("p_kind_last")
    if sigma1 and pk:
        for s in spans:
            for r in (int(s["start_index"]), int(s["end_index"])):
                if 0 < r < n:
                    sc.calibration_kind.append((float(pk[r]), float(s["kind"] == "course")))
    return sc


def ece(pairs: list[tuple[float, float]], bins: int = ECE_BINS) -> float:
    """Expected calibration error: Σ_b (n_b / n) |mean p − mean y| over equal-width bins."""
    if not pairs:
        return math.nan
    a = np.asarray(pairs, dtype=np.float64)
    idx = np.minimum((a[:, 0] * bins).astype(np.int64), bins - 1)
    total = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            total += m.sum() / a.shape[0] * abs(a[m, 0].mean() - a[m, 1].mean())
    return float(total)


def summary(scores: list[ScenarioDetection]) -> dict[str, Any]:
    """Pooled figures over scenarios (point values; intervals come from ``eval.gd``)."""
    spans = [s for sc in scores for s in sc.record.spans or []]
    det = [s for s in spans if s.outcome == "detected"]
    resolved = [s for s in spans if s.outcome != "unresolved"]
    delays = np.array([s.delay_s for s in det if s.delay_s is not None])
    held_s = sum(sc.record.held_leg_seconds for sc in scores)
    g5 = sum(sc.record.held_leg_g5_rows for sc in scores)
    exported = sum(sc.knots_exported for sc in scores)
    bounds = sum(sc.boundaries for sc in scores)
    matched = sum(sc.boundaries_matched for sc in scores)
    prec = matched / exported if exported else math.nan
    rec = matched / bounds if bounds else math.nan
    kind_n = sum(sc.kind_scored for sc in scores)
    return {
        "spans": len(spans),
        "detected": len(det),
        "missed": sum(1 for s in spans if s.outcome == "missed"),
        "unresolved": len(spans) - len(resolved),
        "miss_rate": (len(resolved) - len(det)) / len(resolved) if resolved else math.nan,
        "delay_median_s": percentile(ascending(delays), 0.5),
        "delay_p90_s": percentile(ascending(delays), 0.9),
        "held_leg_g5_rows": g5,
        "held_leg_g5_false_alarm": sum(sc.record.held_leg_g5_flagged for sc in scores) / g5
        if g5
        else math.nan,
        "held_leg_alarms_per_hour": sum(sc.record.held_leg_alarms for sc in scores)
        / (held_s / 3600.0)
        if held_s
        else math.nan,
        "kind_accuracy": sum(sc.kind_correct for sc in scores) / kind_n if kind_n else math.nan,
        "kind_coverage": kind_n / len(det) if det else math.nan,
        "segmentation_precision": prec,
        "segmentation_recall": rec,
        "segmentation_f1": 2 * prec * rec / (prec + rec)
        if exported and bounds and (prec + rec) > 0
        else math.nan,
        "ece_now": ece([q for sc in scores for q in sc.calibration_now]),
        "ece_kind": ece([q for sc in scores for q in sc.calibration_kind]),
    }
