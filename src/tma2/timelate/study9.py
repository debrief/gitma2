"""Spec 026's readings: the carry against the joint solve and against ``ctl`` alone.

Spec 025's readings (``study8.study_split8``) are kept; the carry's comparisons are taken over
periods after an engagement's first (the first has nothing to carry and is ``ctl`` alone), on
the same rows, with the same engagement bootstrap.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .study8 import QUANTITIES, UNDETERMINED, _per_period_facts, paired, period_table, study_split8

CARRY_COMPARISONS = (("carry", "joint"), ("alone", "carry"), ("alone", "joint"))


def _block(t: dict[str, Any], sel: np.ndarray | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for a, b in CARRY_COMPARISONS:
        na, nb, eng = t[a], t[b], t["eng"]
        if sel is not None:
            na, nb, eng = na[sel], nb[sel], eng[sel]
        out[f"{a}/{b}"] = {q: paired(na, nb, eng, c) for c, q in enumerate(QUANTITIES)}
    return out


def study_split9(arr: dict[str, np.ndarray], periods: list[dict[str, Any]]) -> dict[str, Any]:
    base = {k: v for k, v in arr.items() if k not in ("err_carry", "carry_first")}
    out = study_split8(base, periods)
    later = ~arr["carry_first"].astype(bool)
    span = arr["bound_span"][:, 0].astype(np.float64)
    own = arr["bound_own"][:, 0].astype(np.float64)
    rows = np.isfinite(span) & (span < UNDETERMINED) & later
    rows_own = rows & np.isfinite(own) & (own < UNDETERMINED)
    systems = ["alone", "joint", "carry"]
    t = period_table(arr, rows, systems)
    t_own = period_table(arr, rows_own, systems)
    facts = _per_period_facts(periods)
    keys = list(zip(t["eng"].tolist(), t["period"].tolist(), strict=True))
    f = [facts.get((int(e), int(p)), {}) for e, p in keys]
    own_turn = np.array([bool(x) and x["own_turn"] for x in f], dtype=bool)
    gap_man = np.array([bool(x) and x["gap_manoeuvre"] for x in f], dtype=bool)
    carry_recs = [c for r in periods for c in r.get("carry", [])[1:]]
    out["carry"] = {
        "periods_scored": int(t["eng"].size),
        "periods_scored_own": int(t_own["eng"].size),
        "fell_back": int(sum(c["fell_back"] for c in carry_recs)),
        "later_periods": len(carry_recs),
        "first_period_max_diff": max(
            (float(r.get("carry_first_max_diff", 0.0)) for r in periods if "carry" in r),
            default=0.0,
        ),
        "ratios": _block(t),
        "ratios_own_rows": _block(t_own),
        "by_kind": {
            "own_turn": {"periods": int(own_turn.sum()), **_block(t, own_turn)},
            "no_own_turn": {"periods": int((~own_turn).sum()), **_block(t, ~own_turn)},
            "gap_manoeuvre": {"periods": int(gap_man.sum()), **_block(t, gap_man)},
            "no_gap_manoeuvre": {"periods": int((~gap_man).sum()), **_block(t, ~gap_man)},
        },
    }
    return out


def verdict9(r: dict[str, Any]) -> dict[str, Any]:
    """FR-003: (a) carry ÷ joint: joining better if the range interval is wholly above 1, carry
    better if wholly below 1; (b) alone ÷ carry: carrying helps if the range interval is wholly
    above 1, harms if any of range, course and speed is wholly below 1."""
    c = r["carry"]["ratios"]
    cj = c["carry/joint"]["range"]
    a = (
        "joining better"
        if cj.get("lo", 0) > 1
        else ("carry better" if cj.get("hi", 2) < 1 else "not separated")
    )
    ac = c["alone/carry"]
    harm = any(ac[q].get("hi", np.inf) < 1 for q in QUANTITIES)
    helps = ac["range"].get("lo", 0) > 1
    b = "carrying harms" if harm else ("carrying helps" if helps else "not shown")
    return {"carry_vs_joint": a, "alone_vs_carry": b}
