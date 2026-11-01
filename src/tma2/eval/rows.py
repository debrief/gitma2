"""Row selections shared by gates (gitma ``gate-g5.ts``): settled rows and G5 rows."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

G5_SLICE_SIGMA_RAD = math.pi / 180
G5_GATE_MIN = (5, 10, 15, 20)
G5_SETTLE_S = 300.0


def settled_row(m: dict[str, Any], k: int) -> bool:
    """No manoeuvre in progress at row k, and the last one ended ≥ 300 s before (Annex C §C.5)."""
    spans = m.get("manoeuvres") or []
    if any(x["start_index"] <= k < x["end_index"] for x in spans):
        return False
    last = -1
    for x in spans:
        if x["end_index"] <= k:
            last = max(last, int(x["end_index"]))
    if last < 0:
        return True
    return (k - last) * float(m["parameters"]["dt_s"]) >= G5_SETTLE_S


@dataclass
class G5Row:
    index: int
    k: int
    minutes: int
    settled: bool
    cluster: int


def g5_rows(metas: list[dict[str, Any]]) -> list[G5Row]:
    """The G5 rows of a split: σ = 1° scenarios, zig + 5/10/15/20 min where reached; clusters
    numbered over the scenarios that contribute at least one row."""
    rows: list[G5Row] = []
    cluster = 0
    for m in metas:
        if abs(float(m["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) > 1e-6:
            continue
        dt = float(m["parameters"]["dt_s"])
        any_row = False
        for minutes in G5_GATE_MIN:
            k = int(m["zig_index"]) + int(round(minutes * 60 / dt))
            if k >= int(m["samples"]):
                continue
            rows.append(G5Row(int(m["index"]), k, minutes, settled_row(m, k), cluster))
            any_row = True
        if any_row:
            cluster += 1
    return rows
