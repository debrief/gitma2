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


def zig_leg(m: dict[str, Any], before: int = 12, after: int = 30) -> tuple[int, int] | None:
    """The steady target leg that contains the ownship zig, as rows (first, last), or None.

    A target leg runs from the end of one manoeuvre span (or row 0) to two rows before the next
    span starts (or the last row): row ``start_index − 1`` is still on the leg, so this is one row
    conservative. The zig leg is the one containing the ownship's turn, from
    ``turn_start_index`` (or ``zig_index``) to ``zig_index``; it must have at least ``before``
    rows before the turn and ``after`` rows after the zig, so that least squares on the leg alone
    is determined. None when the zig overlaps a target manoeuvre or the leg is too short. Spec 006
    research R3: the MAN2 restatement of gitma's ``beforeManoeuvre``."""
    n = int(m["samples"])
    zig = int(m["zig_index"])
    ts = m.get("turn_start_index")
    turn = zig if ts is None else int(ts)  # an instant turn has no start row
    first, last = 0, n - 1
    for sp in m.get("manoeuvres") or []:
        a, b = int(sp["start_index"]), int(sp["end_index"])
        if a - 1 <= zig and b > turn:
            return None  # the target manoeuvres during the ownship's turn
        if b <= turn:
            first = max(first, b)
        elif a - 1 > zig:
            last = min(last, a - 2)
    if turn - first < before or last - zig < after:
        return None
    return first, last
