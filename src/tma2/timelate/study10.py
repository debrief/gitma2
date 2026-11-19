"""Spec 028's readings: the carried prior against the joint solve, ``ctl`` alone and the
carried start, over periods after an engagement's first (spec 027's rows and bootstrap)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .study8 import QUANTITIES, UNDETERMINED, _per_period_facts, paired, period_table
from .study9 import study_split9

COMPARISONS = (("cprior", "joint"), ("alone", "cprior"), ("carry", "cprior"), ("carry", "joint"))


def _block(
    t: dict[str, Any],
    sel: np.ndarray | None = None,
    comparisons: tuple[tuple[str, str], ...] = COMPARISONS,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for a, b in comparisons:
        na, nb, eng = t[a], t[b], t["eng"]
        if sel is not None:
            na, nb, eng = na[sel], nb[sel], eng[sel]
        out[f"{a}/{b}"] = {q: paired(na, nb, eng, c) for c, q in enumerate(QUANTITIES)}
    return out


def _ties(t: dict[str, Any], a: str, b: str) -> dict[str, float]:
    lr = np.log(t[a][:, 0] / t[b][:, 0])
    lr = lr[np.isfinite(lr)]
    tie = np.abs(lr) < 0.01
    return {
        "within_1pct": float(np.mean(tie)) if lr.size else float("nan"),
        "better": float(np.mean(~tie & (lr > 0))) if lr.size else float("nan"),
        "worse": float(np.mean(~tie & (lr < 0))) if lr.size else float("nan"),
    }


def study_split10(arr: dict[str, np.ndarray], periods: list[dict[str, Any]]) -> dict[str, Any]:
    base = {k: v for k, v in arr.items() if k != "err_cprior" and not k.startswith("err_cv-")}
    out = study_split9(base, periods)
    later = ~arr["carry_first"].astype(bool)
    span = arr["bound_span"][:, 0].astype(np.float64)
    own = arr["bound_own"][:, 0].astype(np.float64)
    rows = np.isfinite(span) & (span < UNDETERMINED) & later
    rows_own = rows & np.isfinite(own) & (own < UNDETERMINED)
    systems = ["alone", "joint", "carry", "cprior"]
    t = period_table(arr, rows, systems)
    t_own = period_table(arr, rows_own, systems)
    facts = _per_period_facts(periods)
    keys = list(zip(t["eng"].tolist(), t["period"].tolist(), strict=True))
    f = [facts.get((int(e), int(p)), {}) for e, p in keys]
    own_turn = np.array([bool(x) and x["own_turn"] for x in f], dtype=bool)
    out["cprior"] = {
        "periods_scored": int(t["eng"].size),
        "periods_scored_own": int(t_own["eng"].size),
        "ratios": _block(t),
        "ratios_own_rows": _block(t_own),
        "by_kind": {
            "own_turn": {"periods": int(own_turn.sum()), **_block(t, own_turn)},
            "no_own_turn": {"periods": int((~own_turn).sum()), **_block(t, ~own_turn)},
        },
        "ties_alone": _ties(t, "alone", "cprior"),
        "ties_joint": _ties(t, "cprior", "joint"),
    }
    variants = [k[4:] for k in arr if k.startswith("err_cv-")]
    if variants:
        systems_v = [*systems, *variants]
        tv = period_table(arr, rows, systems_v)
        tv_own = period_table(arr, rows_own, systems_v)
        keys_v = list(zip(tv["eng"].tolist(), tv["period"].tolist(), strict=True))
        fv = [facts.get((int(e), int(p)), {}) for e, p in keys_v]
        own_v = np.array([bool(x) and x["own_turn"] for x in fv], dtype=bool)
        out["cprior"]["variants"] = {}
        for v in variants:
            cmp = ((v, "joint"), ("alone", v), ("cprior", v))
            out["cprior"]["variants"][v[3:]] = {
                "periods_scored": int(tv["eng"].size),
                "ratios": _block(tv, None, cmp),
                "ratios_own_rows": _block(tv_own, None, cmp),
                "by_kind": {
                    "own_turn": {"periods": int(own_v.sum()), **_block(tv, own_v, cmp)},
                    "no_own_turn": {"periods": int((~own_v).sum()), **_block(tv, ~own_v, cmp)},
                },
                "ties_alone": _ties(tv, "alone", v),
            }
    return out
