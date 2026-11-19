"""Spec 029's registered study: the carried prior where the ownship holds course.

    uv run tma2-long study29 --raw <dir> --config configs/long/hold-<split>.json --out <dir>

Reads spec 028's ``carry2`` outputs of contact 1 (1-hour windows overlapping 15 min) and returns
``study.json``'s content:

* **classes** (FR-003), from the engagement's own record: ``held`` (no ownship turn overlaps the
  window's rows), ``one`` (exactly one does), ``more``; each chain's first window and every window
  with no hand-over (nothing carried, so ``ctl-prior`` is ``ctl`` by construction) are excluded.
* **the rule** (FR-004): geometric mean over windows of ctl ÷ ctl-prior (window medians of range
  error), bootstrap over engagements; gain if the lower limit on ``held`` is above 1; harm if an
  upper limit is below 1 on any class, in range, course or speed.
* **beside** (FR-005), **coverage** by class and **soundness** (FR-006).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .carried import CHI2_4
from .sim import Engagement
from .study import _boot, engagements
from .study27 import QUANTITIES, load27

SEED = 29
CLASSES = ("held", "one", "more")


def turns_in(e: Engagement, first: int, rows: int) -> int:
    """Ownship turns overlapping rows ``first`` … ``first + rows − 1``."""
    return sum(1 for a, b in e.meta["ownship_turns"] if b >= first and a < first + rows)


def klass(n: int) -> str:
    return "held" if n == 0 else ("one" if n == 1 else "more")


def _scored(w: dict[str, Any]) -> bool:
    return bool(w["index"] > 0 and w["carried"] is not None)


def ratio(
    loads: list[dict[str, Any]], num: str, den: str, q: str = "range", keep: Any = None
) -> dict[str, Any]:
    units = []
    for c in loads:
        r = []
        for w in c["windows"]:
            if not _scored(w) or (keep is not None and not keep(w)):
                continue
            a, b = w["med"][num][q], w["med"][den][q]
            if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
                r.append(math.log(a / b))
        if r:
            units.append(np.array(r))

    def gm(us: list[np.ndarray]) -> float:
        return float(np.exp(np.concatenate(us).mean())) if us else math.nan

    def trimmed(us: list[np.ndarray]) -> float:
        if not us:
            return math.nan
        x = np.sort(np.concatenate(us))
        k = int(0.1 * x.size)
        return float(np.exp(x[k : x.size - k].mean())) if x.size > 2 * k else math.nan

    est, lo, hi = _boot(units, gm, SEED)
    t_est, t_lo, t_hi = _boot(units, trimmed, SEED)
    allr = np.exp(np.concatenate(units)) if units else np.zeros(0)
    return {
        "engagements": len(units),
        "windows": int(allr.size),
        "gm": est,
        "interval": [lo, hi],
        "trimmed_10pc": t_est,
        "trimmed_interval": [t_lo, t_hi],
        "median": float(np.median(allr)) if allr.size else None,
        "share_better": float((allr > 1).mean()) if allr.size else None,
        "share_twice_better": float((allr >= 2).mean()) if allr.size else None,
        "share_twice_worse": float((allr <= 0.5).mean()) if allr.size else None,
    }


def coverage(loads: list[dict[str, Any]], keep: Any = None) -> dict[str, Any]:
    units = []
    for c in loads:
        hits = []
        for w in c["windows"]:
            cw = w["carried"]
            if cw is None or w["index"] == 0 or (keep is not None and not keep(w)):
                continue
            try:
                nees = float(cw["d"] @ np.linalg.solve(cw["cov"], cw["d"]))
            except np.linalg.LinAlgError:
                nees = math.inf
            hits.append(1.0 if nees <= CHI2_4[0.05] else 0.0)
        if hits:
            units.append(np.array(hits))

    def share(us: list[np.ndarray]) -> float:
        return float(np.concatenate(us).mean()) if us else math.nan

    est, lo, hi = _boot(units, share, SEED)
    return {"hand_overs": int(sum(u.size for u in units)), "coverage": est, "interval": [lo, hi]}


def score29(raw: Path, config: Path) -> dict[str, Any]:
    stem = config.stem
    engs = engagements(config, 1)
    loads: list[dict[str, Any]] = []
    missing = 0
    for e in engs:
        c = load27(raw, f"{stem}-c1", e, 1)
        if c is None:
            missing += 1
            continue
        for w in c["windows"]:
            n = turns_in(e, int(w["first"]), int(w["rows"]))
            w["turns"], w["klass"] = n, klass(n)
        loads.append(c)
    by = {k: (lambda w, k=k: w["klass"] == k) for k in CLASSES}
    out: dict[str, Any] = {
        "config": str(config),
        "seed": json.loads(config.read_text())["seed"],
        "settings": loads[0]["settings"] if loads else {},
    }
    # counts
    counts: dict[str, Any] = {}
    for k in CLASSES:
        ws = [w for c in loads for w in c["windows"] if w["index"] > 0 and w["klass"] == k]
        counts[k] = {
            "windows": len(ws),
            "handed": sum(1 for w in ws if w["carried"] is not None),
            "answered_both": sum(
                1
                for w in ws
                if w["carried"] is not None
                and np.isfinite(w["med"]["ctl-d1-q0.01"]["range"])
                and np.isfinite(w["med"]["ctl-prior"]["range"])
            ),
            "engagements": sum(
                1 for c in loads if any(w["index"] > 0 and w["klass"] == k for w in c["windows"])
            ),
        }
    out["classes"] = counts
    # rule
    rule: dict[str, Any] = {
        k: {q: ratio(loads, "ctl-d1-q0.01", "ctl-prior", q, by[k]) for q in QUANTITIES}
        for k in CLASSES
    }
    held = rule["held"]["range"]
    gain = bool(np.isfinite(held["interval"][0]) and held["interval"][0] > 1.0)
    harm = [
        f"{k}/{q}"
        for k, d in rule.items()
        for q, r in d.items()
        if np.isfinite(r["interval"][1]) and r["interval"][1] < 1.0
    ]
    out["rule"] = {
        "by_class": rule,
        "gain": gain,
        "harm": harm,
        "outcome": (
            ("gain" if gain else "") + (" and harm" if gain and harm else "harm" if harm else "")
        )
        or "not shown",
    }
    # beside
    b: dict[str, Any] = {}
    for k in CLASSES + ("all",):
        keep = by.get(k)
        b[k] = {
            "ctl-carry/ctl-prior": ratio(loads, "ctl-carry", "ctl-prior", "range", keep),
            "ctl/ctl-carry": ratio(loads, "ctl-d1-q0.01", "ctl-carry", "range", keep),
            "ctl/ctl-prior-noguard": ratio(
                loads, "ctl-d1-q0.01", "ctl-prior-noguard", "range", keep
            ),
            "c2/ctl-prior": ratio(loads, "c2", "ctl-prior", "range", keep),
            "history-map/ctl-prior": ratio(loads, "history-map", "ctl-prior", "range", keep),
            "ctl/ctl-prior": ratio(loads, "ctl-d1-q0.01", "ctl-prior", "range", keep),
        }
    for h in sorted({c["hours"] for c in loads}):
        b[f"held_{h:g}h"] = ratio(
            [c for c in loads if c["hours"] == h], "ctl-d1-q0.01", "ctl-prior", "range", by["held"]
        )
    ds = [w["guard"]["D"] for c in loads for w in c["windows"] if w["guard"]]
    back = sum(1 for c in loads for w in c["windows"] if w["guard"] and w["guard"]["fell_back"])
    b["guard"] = {"guarded": len(ds), "fell_back": back, "rate": back / len(ds) if ds else None}
    b["median_error"] = {
        k: {
            s: float(
                np.nanmedian(
                    [
                        w["med"][s]["range"]
                        for c in loads
                        for w in c["windows"]
                        if _scored(w) and w["klass"] == k
                    ]
                    or [math.nan]
                )
            )
            for s in ("ctl-d1-q0.01", "ctl-carry", "ctl-prior", "c2", "history-map")
        }
        for k in CLASSES
    }
    b["answered"] = {
        s: float(
            np.mean(
                [
                    np.isfinite(w["med"][s]["range"])
                    for c in loads
                    for w in c["windows"]
                    if w["index"] > 0
                ]
            )
        )
        if loads
        else None
        for s in ("ctl-d1-q0.01", "ctl-prior")
    }
    b["search_h"] = {
        k: float(sum(float(w["search_s"].get(k, 0.0)) for c in loads for w in c["windows"]) / 3600)
        for k in ("c2", "none", "carry", "prior-c2", "prior-carry-p")
    }
    b["windows_h"] = float(sum(w["seconds"] for c in loads for w in c["windows"]) / 3600)
    out["beside"] = b
    out["coverage"] = {k: coverage(loads, by[k]) for k in CLASSES}
    out["coverage"]["all"] = coverage(loads)
    # soundness
    planned = sum(c["planned"] for c in loads)
    ran = sum(c["ran"] for c in loads)
    units = []
    for c in loads:
        r = []
        for w in c["windows"]:
            a, bb = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["history-map"]["range"]
            if np.isfinite(a) and np.isfinite(bb) and a > 0 and bb > 0:
                r.append(math.log(a / bb))
        if r:
            units.append(float(np.mean(r)))

    def gm_eng(us: list[float]) -> float:
        return float(np.exp(np.mean(us))) if us else math.nan

    est, lo, hi = _boot(units, gm_eng, SEED)
    cov = out["coverage"]["held"]["coverage"]
    s1 = (ran / planned if planned else 0.0) >= 0.95 and missing == 0
    s2 = bool(0.8 <= est <= 4.0)
    s3 = bool(np.isfinite(cov) and 0.80 <= cov <= 0.99)
    out["soundness"] = {
        "S1_windows_ran": {"planned": planned, "ran": ran, "missing": missing, "pass": bool(s1)},
        "S2_ctl_over_reference": {
            "value": est,
            "interval": [lo, hi],
            "band": [0.8, 4.0],
            "pass": s2,
        },
        "S3_held_coverage": {"value": cov, "band": [0.80, 0.99], "pass": s3},
        "pass": bool(s1 and s2 and s3),
    }
    return out
