"""Spec 027's registered study: ``ctl`` against ``ctl-prior`` (the previous window as a prior).

    uv run tma2-long study27 --raw <dir> --config configs/long/cp-<split>.json --out <dir>

Reads the ``carry2`` outputs of both contacts (``<config stem>-c<contact>-carry2-<i>``) and
returns ``study.json``'s content:

* **classes** (FR-005), from the engagement's own record, before any estimate is read:
  ``weak`` = every window of contact 2, and a contact-1 window whose hand-over time is within
  30 min of a contact gap or which holds at most one ownship turn; ``other`` = the rest of
  contact 1. Each chain's first window (equal by construction) is excluded everywhere.
* **the rule** (FR-006): the geometric mean over windows of ctl ÷ ctl-prior (window medians of
  range error) with a bootstrap over engagements; gain if the lower limit on ``weak`` is above
  1; harm if an upper limit is below 1 on ``weak``, ``other``, contact 1 or contact 2, in
  range, course or speed.
* **beside** (FR-007), **coverage** of the carried 95% region (FR-008), **soundness** (FR-009).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .carried import CHI2_4
from .sim import Engagement
from .study import _boot, _truth, engagements, plausible, range_error

SYSTEMS2 = ("ctl-d1-q0.01", "ctl-carry", "ctl-prior", "ctl-prior-noguard", "c2", "history-map")
SEED = 27
GAP_NEAR_S = 1800.0
QUANTITIES = ("range", "course", "speed")
SCALES = (1.0, 1.5, 2.0, 3.0, 4.0)
TAILS = (0.0, 600.0, 1200.0)


def _errors(
    states: np.ndarray, truth: np.ndarray, e: Engagement, rows: np.ndarray
) -> dict[str, np.ndarray]:
    s = plausible(states, truth)
    c_est = np.arctan2(s[:, 2], s[:, 3])
    c_err = np.abs((c_est - e.tgt[rows, 3] + np.pi) % (2 * np.pi) - np.pi)
    v_err = np.abs(np.hypot(s[:, 2], s[:, 3]) - e.tgt[rows, 4])
    return {"range": range_error(states, truth), "course": c_err, "speed": v_err}


def _med(x: np.ndarray) -> float:
    return float(np.nanmedian(x)) if np.isfinite(x).any() else math.nan


def classify(e: Engagement, contact: int, first: int, rows: int) -> dict[str, Any]:
    t_o = float(e.own[first, 0])
    gaps = e.meta.get("realism", {}).get("gaps_s", []) or []
    near_gap = any(a < t_o + GAP_NEAR_S and b > t_o - GAP_NEAR_S for a, b in gaps)
    turns = sum(1 for a, _b in e.meta["ownship_turns"] if first <= a < first + rows)
    weak = contact == 2 or near_gap or turns <= 1
    return {"weak": bool(weak), "near_gap": bool(near_gap), "own_turns": int(turns)}


def load27(raw: Path, stem: str, e: Engagement, contact: int) -> dict[str, Any] | None:
    f = raw / f"{stem}-carry2-{e.index}.json"
    if not f.exists():
        return None
    head = json.loads(f.read_text())
    z = np.load(f.with_suffix(".npz"))
    wins = []
    for w in sorted(head["windows"], key=lambda x: x["index"]):
        j = w["index"]
        rows = z[f"w{j}_rows"]
        tr = _truth(e, rows)
        med: dict[str, dict[str, float]] = {}
        for s in SYSTEMS2:
            err = _errors(z[f"w{j}_{s}"], tr, e, rows)
            med[s] = {q: _med(err[q]) for q in QUANTITIES}
        cov = None
        h = w.get("handed", {})
        if "mean" in h:
            a = int(h["row"])
            truth = np.array([e.tgt[a, 1], e.tgt[a, 2], e.tgt[a, 3], e.tgt[a, 4]])
            d = np.array(h["mean"]) - truth
            d[2] = (d[2] + np.pi) % (2 * np.pi) - np.pi
            cov = {"d": d, "raw": np.array(h["cov_raw"]), "cov": np.array(h["cov"]), "h": h}
        wins.append(
            {
                "index": j,
                "first": int(w["first"]),
                "rows": int(w["rows"]),
                "class": classify(e, contact, int(w["first"]), int(w["rows"])),
                "med": med,
                "guard": w.get("guard"),
                "carried": cov,
                "search_s": w.get("search_s", {}),
                "seconds": float(w["seconds"]),
            }
        )
    return {
        "planned": len(head["chain"]),
        "ran": len(wins),
        "hours": float(e.meta["hours"]),
        "contact": contact,
        "settings": head.get("carry_settings", {}),
        "windows": wins,
    }


def _gm(us: list[np.ndarray]) -> float:
    return float(np.exp(np.concatenate(us).mean())) if us else math.nan


def ratio(
    loads: list[dict[str, Any]],
    num: str,
    den: str,
    q: str = "range",
    keep: Any = None,
) -> dict[str, Any]:
    """Geometric mean over windows of ``num`` ÷ ``den`` (window medians of ``q``), first windows
    excluded, with the engagement bootstrap; and the per-window distribution beside."""
    units = []
    for c in loads:
        r = []
        for w in c["windows"]:
            if w["index"] == 0 or (keep is not None and not keep(c, w)):
                continue
            a, b = w["med"][num][q], w["med"][den][q]
            if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
                r.append(math.log(a / b))
        if r:
            units.append(np.array(r))
    est, lo, hi = _boot(units, _gm, SEED)
    allr = np.exp(np.concatenate(units)) if units else np.zeros(0)
    return {
        "engagements": len(units),
        "windows": int(allr.size),
        "gm": est,
        "interval": [lo, hi],
        "median": float(np.median(allr)) if allr.size else None,
        "better": int((allr > 1).sum()),
        "worse": int((allr < 1).sum()),
        "level": int((allr == 1).sum()),
        "twice_better": int((allr >= 2).sum()),
        "twice_worse": int((allr <= 0.5).sum()),
    }


def _splits() -> dict[str, Any]:
    return {
        "weak": lambda c, w: w["class"]["weak"],
        "other": lambda c, w: not w["class"]["weak"],
        "contact1": lambda c, w: c["contact"] == 1,
        "contact2": lambda c, w: c["contact"] == 2,
        "contact1_weak": lambda c, w: c["contact"] == 1 and w["class"]["weak"],
        "near_gap": lambda c, w: w["class"]["near_gap"],
        "few_turns": lambda c, w: c["contact"] == 1 and w["class"]["own_turns"] <= 1,
    }


def rule(loads: list[dict[str, Any]]) -> dict[str, Any]:
    sp = _splits()
    out: dict[str, Any] = {"by_split": {}}
    for name in ("weak", "other", "contact1", "contact2"):
        out["by_split"][name] = {
            q: ratio(loads, "ctl-d1-q0.01", "ctl-prior", q, sp[name]) for q in QUANTITIES
        }
    weak = out["by_split"]["weak"]["range"]
    gain = bool(np.isfinite(weak["interval"][0]) and weak["interval"][0] > 1.0)
    harms = [
        f"{name}/{q}"
        for name, d in out["by_split"].items()
        for q, r in d.items()
        if np.isfinite(r["interval"][1]) and r["interval"][1] < 1.0
    ]
    out["gain"] = gain
    out["harm"] = harms
    out["outcome"] = (
        ("gain" if gain else "") + (" and harm" if gain and harms else "harm" if harms else "")
    ) or "not shown"
    return out


def coverage(loads: list[dict[str, Any]], keep: Any = None) -> dict[str, Any]:
    """Share of hand-overs whose truth lies in the carried 95% region, the engagement interval,
    and the same over the settings grid (raw covariance × scale plus the τ-proportional terms
    recomputed for each tail)."""

    def nees(d: np.ndarray, cov: np.ndarray) -> float:
        try:
            return float(d @ np.linalg.solve(cov, d))
        except np.linalg.LinAlgError:
            return math.inf

    def covered(scale: float | None, tail: float | None) -> list[np.ndarray]:
        units = []
        for c in loads:
            hits = []
            for w in c["windows"]:
                cw = w["carried"]
                if cw is None or (keep is not None and not keep(c, w)):
                    continue
                if scale is None:
                    cov = cw["cov"]
                else:
                    h = cw["h"]
                    gap, tau = float(h["gap_s"]), float(h["tau_s"])
                    k = (gap + float(tail or 0.0)) / tau if tau > 0 else 0.0
                    cov = scale * cw["raw"] + np.diag(
                        [
                            1.0 + k * h["add_pos"],
                            1.0 + k * h["add_pos"],
                            1e-8 + k * h["add_course"],
                            1e-8 + k * h["add_speed"],
                        ]
                    )
                hits.append(1.0 if nees(cw["d"], cov) <= CHI2_4[0.05] else 0.0)
            if hits:
                units.append(np.array(hits))
        return units

    def share(us: list[np.ndarray]) -> float:
        return float(np.concatenate(us).mean()) if us else math.nan

    units = covered(None, None)
    est, lo, hi = _boot(units, share, SEED)
    grid = {f"{s:g}/{t:g}": share(covered(s, t)) for s in SCALES for t in TAILS}
    return {
        "hand_overs": int(sum(u.size for u in units)),
        "coverage": est,
        "interval": [lo, hi],
        "grid_scale_tail": grid,
    }


def guard_summary(loads: list[dict[str, Any]]) -> dict[str, Any]:
    ds = [w["guard"]["D"] for c in loads for w in c["windows"] if w["guard"]]
    back = [w for c in loads for w in c["windows"] if w["guard"] and w["guard"]["fell_back"]]
    d = np.array(ds, dtype=float)
    return {
        "guarded_windows": int(d.size),
        "fell_back": len(back),
        "rate": float(len(back) / d.size) if d.size else None,
        "D_quantiles": {str(p): float(np.quantile(d, p)) for p in (0.5, 0.9, 0.99)}
        if d.size
        else {},
        "rate_at_level": {
            str(a): float((d > q).mean()) if d.size else None for a, q in CHI2_4.items()
        },
    }


def soundness(loads: list[dict[str, Any] | None], n: int) -> dict[str, Any]:
    got = [c for c in loads if c]
    planned = sum(c["planned"] for c in got)
    ran = sum(c["ran"] for c in got)
    missing = n - len(got)
    s1 = (ran / planned if planned else 0.0) >= 0.95 and missing == 0
    units = []
    for c in got:
        r = []
        for w in c["windows"]:
            a, b = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["history-map"]["range"]
            if np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0:
                r.append(math.log(a / b))
        if r:
            units.append(float(np.mean(r)))

    def gm_eng(us: list[float]) -> float:
        return float(np.exp(np.mean(us))) if us else math.nan

    est, lo, hi = _boot(units, gm_eng, SEED)
    return {
        "S1_windows_ran": {"planned": planned, "ran": ran, "missing": missing, "pass": bool(s1)},
        "S2_ctl_over_reference": {
            "value": est,
            "interval": [lo, hi],
            "band": [0.8, 4.0],
            "pass": bool(0.8 <= est <= 4.0),
        },
        "pass": bool(s1 and 0.8 <= est <= 4.0),
    }


def score27(raw: Path, config: Path) -> dict[str, Any]:
    stem = config.stem
    loads: list[dict[str, Any] | None] = []
    hours = []
    for contact in (1, 2):
        for e in engagements(config, contact):
            loads.append(load27(raw, f"{stem}-c{contact}", e, contact))
            hours.append(float(e.meta["hours"]))
    got = [c for c in loads if c]
    sp = _splits()
    out: dict[str, Any] = {
        "config": str(config),
        "seed": json.loads(config.read_text())["seed"],
        "settings": got[0]["settings"] if got else {},
        "soundness": soundness(loads, len(loads)),
        "rule": rule(got),
        "beside": {},
        "coverage": {},
        "guard": guard_summary(got),
    }
    b: dict[str, Any] = out["beside"]
    for name, keep in sp.items():
        b[name] = {
            "ctl/ctl-prior": ratio(got, "ctl-d1-q0.01", "ctl-prior", "range", keep),
            "ctl-carry/ctl-prior": ratio(got, "ctl-carry", "ctl-prior", "range", keep),
            "ctl/ctl-prior-noguard": ratio(got, "ctl-d1-q0.01", "ctl-prior-noguard", "range", keep),
            "ctl/ctl-carry": ratio(got, "ctl-d1-q0.01", "ctl-carry", "range", keep),
            "c2/ctl-prior": ratio(got, "c2", "ctl-prior", "range", keep),
            "history-map/ctl-prior": ratio(got, "history-map", "ctl-prior", "range", keep),
        }
    for h in sorted({c["hours"] for c in got}):
        b[f"{h:g}h"] = ratio(
            got, "ctl-d1-q0.01", "ctl-prior", "range", lambda c, w, h=h: c["hours"] == h
        )
    b["by_position"] = {
        str(k): ratio(got, "ctl-d1-q0.01", "ctl-prior", "range", lambda c, w, k=k: w["index"] == k)
        for k in range(1, 8)
    }
    back = lambda c, w: bool(w["guard"] and w["guard"]["fell_back"])  # noqa: E731
    b["fell_back_windows"] = ratio(got, "ctl-d1-q0.01", "ctl-prior-noguard", "range", back)
    b["classes"] = {
        name: int(sum(1 for c in got for w in c["windows"] if w["index"] > 0 and keep(c, w)))
        for name, keep in sp.items()
    }
    b["class_engagements"] = {
        name: int(sum(1 for c in got if any(w["index"] > 0 and keep(c, w) for w in c["windows"])))
        for name, keep in sp.items()
    }
    b["answered"] = {
        s: float(
            np.mean(
                [np.isfinite(w["med"][s]["range"]) for c in got for w in c["windows"] if w["index"]]
            )
        )
        if got
        else None
        for s in SYSTEMS2
    }
    b["search_h"] = {
        k: float(sum(float(w["search_s"].get(k, 0.0)) for c in got for w in c["windows"]) / 3600)
        for k in ("c2", "none", "carry", "prior-c2", "prior-carry-p")
    }
    b["windows_h"] = float(sum(w["seconds"] for c in got for w in c["windows"]) / 3600)
    b["median_error"] = {
        s: {
            q: float(
                np.nanmedian([w["med"][s][q] for c in got for w in c["windows"] if w["index"]])
            )
            for q in QUANTITIES
        }
        for s in SYSTEMS2
    }
    for name in ("contact1", "contact2", "near_gap", "few_turns"):
        out["coverage"][name] = coverage(got, sp[name])
    return out
