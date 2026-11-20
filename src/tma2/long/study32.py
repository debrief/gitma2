"""Spec 032's registered study: the carried prior where ownship legs outlast the 2-hour window.

    uv run tma2-long study32 --raw <dir> --config configs/long/legs-<split>.json --out <dir>

Reads, per engagement of contact 1 (``<stem>`` the config's stem):

* (a) ``<stem>-c1-carry2-<i>``: spec 028's ``carry2`` on 2-hour windows overlapping 30 min
  (``ctl``, ``ctl-carry``, ``ctl-prior``, ``ctl-prior-noguard``, ``history-map``);
* (c) ``<stem>-c1-jointheld-<i>``: ``ctl`` on the union of each turn-free 2-hour window and the
  one before it, on the window's rows, with the true-history fit over the union (``history-best``).

On every held 2-hour window (no ownship turn overlaps it; not a chain's first; handed on in (a);
answered by ``ctl``, ``ctl-prior`` and (c)) it takes each system's median error over that
window's rows and returns ``study.json``'s content: the decided estimands E1 = ``ctl`` ÷
``ctl-prior`` and E2 = (c) ÷ ``ctl-prior`` with a bootstrap over engagements, each read
"ctl-prior better" (lower limit above 1), "ctl-prior worse" (upper limit below 1) or "not
separated"; harm if E1 on one-turn windows has its upper limit below 1; readings beside;
soundness S1–S3.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .carried import CHI2_4
from .study import _boot, _truth, engagements
from .study27 import QUANTITIES, load27
from .study29 import klass, turns_in
from .study30 import _load_joint

SEED = 32
CTL, PRIOR = "ctl-d1-q0.01", "ctl-prior"


def _ratio(units: list[np.ndarray]) -> dict[str, Any]:
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
        "share_prior_better": float((allr > 1).mean()) if allr.size else None,
        "share_twice_prior_better": float((allr >= 2).mean()) if allr.size else None,
        "share_twice_prior_worse": float((allr <= 0.5).mean()) if allr.size else None,
    }


def _read(r: dict[str, Any]) -> str:
    lo, hi = r["interval"]
    if np.isfinite(lo) and lo > 1.0:
        return "ctl-prior better"
    if np.isfinite(hi) and hi < 1.0:
        return "ctl-prior worse"
    return "not separated"


def _nees(cw: dict[str, Any]) -> float:
    try:
        return float(cw["d"] @ np.linalg.solve(cw["cov"], cw["d"]))
    except np.linalg.LinAlgError:
        return math.inf


def score32(raw: Path, config: Path) -> dict[str, Any]:
    stem = config.stem
    engs = engagements(config, 1)
    recs: list[dict[str, Any]] = []
    missing = {"a": 0, "c": 0}
    planned = ran = 0
    s2_units: list[float] = []
    cost = {"a_s": 0.0, "c_s": 0.0, "hours": 0.0}
    for e in engs:
        a = load27(raw, f"{stem}-c1", e, 1)
        c = _load_joint(raw, stem, e)
        if a is None:
            missing["a"] += 1
        if c is None:
            missing["c"] += 1
        if a is None:
            continue
        planned += a["planned"]
        ran += a["ran"]
        cost["hours"] += float(e.meta["hours"])
        cost["a_s"] += sum(w["seconds"] for w in a["windows"])
        if c is not None:
            cost["c_s"] += sum(x["seconds"] for x in c.values())
        r = []
        for w in a["windows"]:
            x, y = w["med"][CTL]["range"], w["med"]["history-map"]["range"]
            if np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0:
                r.append(math.log(x / y))
        if r:
            s2_units.append(float(np.mean(r)))
        for w in a["windows"]:
            if w["index"] == 0:
                continue
            first, nrows = int(w["first"]), int(w["rows"])
            j = int(w["index"])
            tr = _truth(e, np.arange(first, first + nrows, 12))
            rec: dict[str, Any] = {
                "engagement": e.index,
                "hours": float(e.meta["hours"]),
                "index": j,
                "klass": klass(turns_in(e, first, nrows)),
                "handed": w["carried"] is not None,
                "prior": w["med"][PRIOR],
                "ctl": w["med"][CTL],
                "carry": w["med"]["ctl-carry"],
                "noguard": w["med"]["ctl-prior-noguard"],
                "fell_back": bool(w["guard"] and w["guard"]["fell_back"]),
                "carried": w["carried"],
                "detected": float(e.obs[first : first + nrows, 2].mean()),
                "range_km": float(
                    np.median(np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])) / 1e3
                ),
            }
            if c is not None and j in c:
                rec["joint"] = c[j]["ctl"]
                rec["ref"] = c[j]["ref"]
            recs.append(rec)

    def ok(x: Any, q: str = "range") -> bool:
        return x is not None and np.isfinite(x[q]) and x[q] > 0

    def units(num: str, keep: Any, q: str = "range", den: str = "prior") -> list[np.ndarray]:
        by: dict[int, list[float]] = {}
        for rec in recs:
            if not keep(rec):
                continue
            n, d = rec.get(num), rec.get(den)
            if n is not None and d is not None and ok(n, q) and ok(d, q):
                by.setdefault(rec["engagement"], []).append(math.log(n[q] / d[q]))
        return [np.array(v) for v in by.values()]

    def decided(rec: dict[str, Any]) -> bool:
        return bool(
            rec["klass"] == "held"
            and rec["handed"]
            and ok(rec["prior"])
            and ok(rec["ctl"])
            and ok(rec.get("joint"))
        )

    def one_turn(rec: dict[str, Any]) -> bool:
        return bool(rec["klass"] == "one" and rec["handed"] and ok(rec["prior"]) and ok(rec["ctl"]))

    held = [r for r in recs if r["klass"] == "held"]
    out: dict[str, Any] = {
        "config": str(config),
        "seed": json.loads(config.read_text())["seed"],
        "counts": {
            "windows_after_first": len(recs),
            "by_class": {
                k: sum(1 for r in recs if r["klass"] == k) for k in ("held", "one", "more")
            },
            "held_handed": sum(1 for r in held if r["handed"]),
            "held_decided": sum(1 for r in held if decided(r)),
            "held_answered_of_handed": {
                k: sum(1 for r in held if r["handed"] and ok(r.get(k)))
                for k in ("ctl", "prior", "joint")
            },
            "one_handed": sum(1 for r in recs if r["klass"] == "one" and r["handed"]),
            "one_decided": sum(1 for r in recs if one_turn(r)),
            "missing_engagements": missing,
        },
    }
    ests: dict[str, Any] = {}
    for name, num in (("E1_ctl_over_prior", "ctl"), ("E2_joint_over_prior", "joint")):
        ests[name] = {q: _ratio(units(num, decided, q)) for q in QUANTITIES}
        ests[name]["reading"] = _read(ests[name]["range"])
    harm: dict[str, Any] = {q: _ratio(units("ctl", one_turn, q)) for q in QUANTITIES}
    hi = harm["range"]["interval"][1]
    harm["reading"] = "harm" if np.isfinite(hi) and hi < 1.0 else "no harm"
    ests["E1_one_turn"] = harm
    out["estimands"] = ests
    out["outcome"] = {
        "E1_ctl_over_prior": ests["E1_ctl_over_prior"]["reading"],
        "E2_joint_over_prior": ests["E2_joint_over_prior"]["reading"],
        "harm": harm["reading"],
    }

    # beside
    b: dict[str, Any] = {
        "carry_over_prior_held": _ratio(units("carry", decided)),
        "span_reference_over_prior_held": _ratio(units("ref", decided)),
        "joint_over_ctl_held": _ratio(units("joint", decided, den="ctl")),
        "E1_without_fall_back": _ratio(units("ctl", lambda r: decided(r) and not r["fell_back"])),
        "E2_without_fall_back": _ratio(units("joint", lambda r: decided(r) and not r["fell_back"])),
        "E1_held_without_joint": _ratio(
            units(
                "ctl",
                lambda r: r["klass"] == "held" and r["handed"] and ok(r["prior"]) and ok(r["ctl"]),
            )
        ),
    }
    for name, lo, hi_ in (
        ("<15", 0.0, 15.0),
        ("15-25", 15.0, 25.0),
        ("25-35", 25.0, 35.0),
        (">35", 35.0, 1e9),
    ):
        band = lambda r, lo=lo, hi_=hi_: decided(r) and lo <= r["range_km"] < hi_  # noqa: E731
        b[f"E1_range_{name}"] = _ratio(units("ctl", band))
        b[f"E2_range_{name}"] = _ratio(units("joint", band))
    for name, keep in (
        ("detected_under_0.75", lambda r: decided(r) and r["detected"] < 0.75),
        ("detected_0.75_up", lambda r: decided(r) and r["detected"] >= 0.75),
        ("hours_6", lambda r: decided(r) and r["hours"] == 6.0),
        ("hours_12", lambda r: decided(r) and r["hours"] == 12.0),
    ):
        b[f"E1_{name}"] = _ratio(units("ctl", keep))
        b[f"E2_{name}"] = _ratio(units("joint", keep))
    med = {}
    for key in ("ctl", "prior", "carry", "joint", "ref"):
        vals = [r[key]["range"] for r in recs if decided(r) and r.get(key) is not None]
        med[key] = float(np.nanmedian(vals)) if vals and np.isfinite(vals).any() else None
    b["median_error_held"] = med
    dec = [r for r in recs if decided(r)]
    b["held_decided_detected_median"] = (
        float(np.median([r["detected"] for r in dec])) if dec else None
    )
    b["held_decided_range_km_median"] = (
        float(np.median([r["range_km"] for r in dec])) if dec else None
    )
    b["guard_fell_back_held_decided"] = (
        float(np.mean([r["fell_back"] for r in dec])) if dec else None
    )
    b["guard_fell_back_one_decided"] = (
        float(np.mean([r["fell_back"] for r in recs if one_turn(r)]))
        if any(one_turn(r) for r in recs)
        else None
    )
    nees_one = [_nees(r["carried"]) for r in recs if one_turn(r)]
    b["one_turn_coverage"] = (
        float(np.mean([x <= CHI2_4[0.05] for x in nees_one])) if nees_one else None
    )
    b["cost"] = {
        "engagement_hours": cost["hours"],
        "a_s_per_engagement_hour": cost["a_s"] / max(cost["hours"], 1e-9),
        "c_s_per_engagement_hour": cost["c_s"] / max(cost["hours"], 1e-9),
        "c_s_per_held_window": cost["c_s"]
        / max(sum(1 for r in held if r.get("joint") is not None), 1),
        "a_hours": cost["a_s"] / 3600,
        "c_hours": cost["c_s"] / 3600,
    }
    out["beside"] = b

    # soundness
    nees = [_nees(r["carried"]) for r in dec]
    cov = float(np.mean([x <= CHI2_4[0.05] for x in nees])) if nees else math.nan

    def gm_eng(us: list[float]) -> float:
        return float(np.exp(np.mean(us))) if us else math.nan

    s2, s2lo, s2hi = _boot(s2_units, gm_eng, SEED)
    s1 = all(v == 0 for v in missing.values()) and planned > 0 and ran / planned >= 0.95
    sound: dict[str, Any] = {
        "S1_parts_present": {"missing": missing, "planned": planned, "ran": ran, "pass": bool(s1)},
        "S2_ctl_over_reference": {
            "value": s2,
            "interval": [s2lo, s2hi],
            "band": [0.8, 4.0],
            "pass": bool(0.8 <= s2 <= 4.0),
        },
        "S3_held_coverage": {
            "value": cov,
            "median_nees": float(np.median(nees)) if nees else math.nan,
            "hand_overs": len(nees),
            "band": [0.80, 0.99],
            "pass": bool(np.isfinite(cov) and 0.80 <= cov <= 0.99),
        },
    }
    sound["pass"] = bool(all(x["pass"] for x in sound.values()))
    out["soundness"] = sound
    return out
