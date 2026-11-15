"""Readings of spec 019's diagnostic from ``run7`` shards: every ladder system against the
standing control (declared) and against the true-prior rung, paired per period in range,
course and speed, with the share of each gain carried by its best periods."""

from __future__ import annotations

from typing import Any

import numpy as np

from .study import _log
from .study3 import counts3
from .study4 import study_split4
from .study6 import medians3, pair3

TOP = 10


def concentration(a: np.ndarray, b: np.ndarray, top: int = TOP) -> dict[str, float]:
    """Of Σ log(a ÷ b) over periods: the share in the ``top`` periods with the largest
    log ratio, and the geometric mean ratio with those periods set aside."""
    d = np.sort(_log(a) - _log(b))[::-1]
    total = float(d.sum())
    rest = d[top:]
    return {
        "top": int(min(top, d.size)),
        "share_in_top": float(d[:top].sum() / total) if total != 0.0 else float("nan"),
        "ratio_without_top": float(np.exp(rest.mean())) if rest.size else float("nan"),
    }


def study_split7(
    arr: dict[str, np.ndarray], periods: list[dict[str, Any]], plan: dict[str, Any]
) -> dict[str, Any]:
    out = study_split4(arr, periods, plan)
    st = plan["ladder_study"]
    control, last = st["control"], st["true"]
    _ids, med, _b = medians3(arr)
    systems = sorted(s for s in med if s.startswith(("lad-", "one-", "mem-")))
    rows: dict[str, Any] = {}
    for s in systems:
        row: dict[str, Any] = {
            "vs_control": pair3(med, control, s),
            "vs_true": pair3(med, s, last) if s != last else None,
        }
        ok = np.isfinite(med[control][:, 0]) & np.isfinite(med[s][:, 0])
        ok &= (med[control][:, 0] > 0) & (med[s][:, 0] > 0)
        if int(ok.sum()) > TOP:
            row["concentration"] = concentration(med[control][ok, 0], med[s][ok, 0])
        row["counts"] = counts3(periods, s) if any(s in r["histories"] for r in periods) else None
        row["periods_without_a_track"] = int((~np.isfinite(med[s][:, 0])).sum())
        rows[s] = row
    out["ladder"] = rows
    return out
