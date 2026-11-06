"""Truth labels for steady-leg segmentation (spec 005 FR-051, research R4).

The rows where a vessel's true course or speed changes are exactly its manoeuvre rows: for the
target, each span's rows [start_index, end_index]; for ownship, each planned turn's rows
[turn_start_index, zig_index] (and the second turn's). Helm wander and autopilot oscillation
(generator 0.6.0) stay inside ± C and are not transitions.

* **Transitions** are those rows, widened symmetrically to at least T_min and merged where they
  touch.
* **Steady legs** are the rows between, if at least L_min long; a shorter piece is unknown.
* **Target prior.** For the target, rows up to the end of the first ownship zig are unknown when
  ``prior_unknown`` (the scoring default): there the target's range is undetermined, and a
  segmenter must not be scored on what it cannot see.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from . import STEADY, TRANSITION, UNKNOWN, Interval, from_codes


def _ownship_turns(m: dict[str, Any]) -> list[tuple[int, int]]:
    zig = int(m["zig_index"])
    ts = m.get("turn_start_index")
    out = [(zig if ts is None else int(ts), zig)]
    if m.get("zig2_index") is not None:
        z2 = int(m["zig2_index"])
        t2 = m.get("turn2_start_index")
        out.append((z2 if t2 is None else int(t2), z2))
    return out


def change_rows(m: dict[str, Any], vessel: str) -> list[tuple[int, int]]:
    """The vessel's manoeuvre rows as inclusive (first, last) pairs, in order."""
    if vessel == "target":
        spans = [(int(s["start_index"]), int(s["end_index"])) for s in m.get("manoeuvres") or []]
    elif vessel == "ownship":
        spans = _ownship_turns(m)
    else:
        raise ValueError(f"vessel must be target or ownship, not {vessel!r}")
    return sorted(spans)


def widen(spans: list[tuple[int, int]], t_min: int, n: int) -> list[tuple[int, int]]:
    """Each span widened symmetrically to at least ``t_min`` rows (the extra row of an odd
    shortfall goes after it), clipped to [0, n − 1], then merged where they overlap or touch."""
    out: list[tuple[int, int]] = []
    for a, b in spans:
        short = t_min - (b - a + 1)
        if short > 0:
            a -= short // 2
            b += short - short // 2
        a, b = max(a, 0), min(b, n - 1)
        if b < a:
            continue
        if out and a <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def truth_codes(
    m: dict[str, Any],
    vessel: str,
    l_min: int,
    t_min: int,
    n: int | None = None,
    prior_unknown: bool = True,
) -> np.ndarray:
    """Per-row truth codes (``STEADY``, ``TRANSITION``, ``UNKNOWN``) for rows 0 … n − 1."""
    n = int(m["samples"]) if n is None else n
    codes = np.full(n, STEADY, dtype=np.int8)
    for a, b in widen(change_rows(m, vessel), t_min, n):
        codes[a : b + 1] = TRANSITION
    for iv in from_codes(codes):
        if iv.kind == STEADY and iv.end - iv.start + 1 < l_min:
            codes[iv.start : iv.end + 1] = UNKNOWN
    if vessel == "target" and prior_unknown:
        codes[: min(int(m["zig_index"]) + 1, n)] = UNKNOWN
    return codes


def truth_intervals(
    m: dict[str, Any], vessel: str, l_min: int, t_min: int, prior_unknown: bool = True
) -> list[Interval]:
    return from_codes(truth_codes(m, vessel, l_min, t_min, prior_unknown=prior_unknown))
