"""The oracle-ceiling check (spec 002 FR-008, P0): paired, scenario-clustered median-ratio
intervals of one per-timestep estimator against another on the G5 rows, as docs/research/05."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .bootstrap import RatioInterval, bootstrap_clustered_quantile_ratio
from .errors import Truth, row_error
from .predictions import iter_predictions_raw
from .rows import G5Row, g5_rows


@dataclass
class RatioCheck:
    name: str
    rows: int
    interval: RatioInterval


def load_rows(path: str) -> dict[int, dict[float, dict[str, Any]]]:
    out: dict[int, dict[float, dict[str, Any]]] = {}
    for _, p in iter_predictions_raw(path):
        out[int(p["scenario_index"])] = {float(r["timestamp_s"]): r for r in p["rows"]}
    return out


def g5_errors(
    truths: list[Truth],
    rows: list[G5Row],
    preds: dict[int, dict[float, dict[str, Any]]],
    metric: str,
) -> np.ndarray:
    """One error per G5 row (+∞ when the estimator has no converged row there)."""
    by_index = {t.index: t for t in truths}
    out = np.empty(len(rows))
    for i, g in enumerate(rows):
        t = by_index[g.index]
        r = preds.get(g.index, {}).get(float(t.own[g.k, 0]))
        if r is None or not r["converged"]:
            out[i] = math.inf
        else:
            out[i] = getattr(row_error(t, r), metric)
    return out


def oracle_ratios(
    truths: list[Truth], a_path: str, b_path: str, level: float = 0.975, resamples: int = 2000
) -> list[RatioCheck]:
    """Median ratios a / b (range, course, speed) on all G5 rows and on settled rows."""
    metas = [t.meta for t in truths]
    rows = g5_rows(metas)
    a = load_rows(a_path)
    b = load_rows(b_path)
    checks = []
    for subset_name, pred in (("all", lambda g: True), ("settled", lambda g: g.settled)):
        sub = [g for g in rows if pred(g)]
        cluster = np.array([g.cluster for g in sub], dtype=np.int64)
        for metric, label in (
            ("range_rel", "range"),
            ("course_deg", "course"),
            ("speed_kt", "speed"),
        ):
            ea = g5_errors(truths, sub, a, metric)
            eb = g5_errors(truths, sub, b, metric)
            iv = bootstrap_clustered_quantile_ratio(ea, eb, cluster, 0.5, level, resamples)
            checks.append(RatioCheck(f"{subset_name}-{label}", len(sub), iv))
    return checks


def checks_to_json(checks: list[RatioCheck]) -> str:
    return json.dumps(
        [
            {
                "name": c.name,
                "rows": c.rows,
                "ratio": c.interval.ratio,
                "lo": c.interval.lo,
                "hi": c.interval.hi,
                "clusters": c.interval.clusters,
                "level": c.interval.level,
            }
            for c in checks
        ],
        indent=2,
    )
