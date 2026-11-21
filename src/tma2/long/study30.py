"""Spec 030's registered study: the carried prior against longer windows and a joint solve.

    uv run tma2-long study30 --raw <dir> --config configs/long/<cmp config>.json --out <dir>

Reads, per engagement of contact 1 (``<stem>`` the config's stem):

* (a) ``<stem>-c1-carry2-<i>``: spec 028's ``carry2`` on 1-hour windows (``ctl``, ``ctl-carry``,
  ``ctl-prior``);
* (b) ``<stem>-2h-c1-carry2-<i>``: ``carry2`` on 2-hour windows overlapping 30 min, stitched
  mid-overlap (spec 023), giving ``ctl`` (and ``ctl-prior``) on 2-hour windows;
* (c) ``<stem>-c1-jointheld-<i>``: ``ctl`` on the union of each turn-free 1-hour window and the
  one before it, on the window's rows, with the true-history fit over the union (``history-best``).

On every held 1-hour window (no ownship turn overlaps it; not a chain's first; handed on in (a);
answered by (a), (b) and (c)) it takes each system's median error over that window's rows and
returns ``study.json``'s content: the decided estimands D1 = (b) ÷ (a), D2 = (c) ÷ (a) and,
added on tuning before validation, D3 = (b)'s ``ctl-prior`` ÷ (a), with a bootstrap over
engagements, each read "ctl-prior better" (lower limit above 1), "ctl-prior worse" (upper limit
below 1) or "not separated"; readings beside; soundness S1–S3.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .carried import CHI2_4
from .sim import Engagement
from .study import _boot, _truth, engagements
from .study27 import QUANTITIES, _errors, load27
from .study29 import klass, turns_in
from .timelate import stitch

SEED = 30
TWO_H = ("ctl-d1-q0.01", "ctl-carry", "ctl-prior")


def _med(x: np.ndarray) -> float:
    return float(np.nanmedian(x)) if np.isfinite(x).any() else math.nan


def _window_meds(states: np.ndarray, rows: np.ndarray, e: Engagement) -> dict[str, float]:
    if rows.size == 0:
        return {q: math.nan for q in QUANTITIES}
    err = _errors(states, _truth(e, rows), e, rows)
    return {q: _med(err[q]) for q in QUANTITIES}


def _load_2h(raw: Path, stem: str, e: Engagement) -> dict[str, Any] | None:
    f = raw / f"{stem}-2h-c1-carry2-{e.index}.json"
    if not f.exists():
        return None
    head = json.loads(f.read_text())
    z = np.load(f.with_suffix(".npz"))
    wins = []
    for w in sorted(head["windows"], key=lambda x: x["index"]):
        j = w["index"]
        wins.append(
            {
                "first": int(w["first"]),
                "rows": int(w["rows"]),
                "rows_abs": z[f"w{j}_rows"],
                "tracks": {s: z[f"w{j}_{s}"] for s in TWO_H},
                "declared": {},
                "seconds": float(w["seconds"]),
            }
        )
    st = stitch(e, wins, int(head["settings"]["score_every"]), TWO_H, ())
    return {
        "rows": st["rows"],
        "states": st["states"],
        "seconds": sum(w["seconds"] for w in wins),
        "windows": len(wins),
        "planned": len(head["chain"]),
    }


def _load_joint(raw: Path, stem: str, e: Engagement) -> dict[int, dict[str, Any]] | None:
    f = raw / f"{stem}-c1-jointheld-{e.index}.json"
    if not f.exists():
        return None
    head = json.loads(f.read_text())
    z = np.load(f.with_suffix(".npz"))
    out = {}
    for w in head["windows"]:
        j = int(w["index"])
        rows = z[f"w{j}_rows"]
        out[j] = {
            "ctl": _window_meds(z[f"w{j}_ctl-d1-q0.01"], rows, e),
            "ref": _window_meds(z[f"w{j}_history-best"], rows, e),
            "seconds": float(w["seconds"]),
        }
    return out


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
        "share_a_better": float((allr > 1).mean()) if allr.size else None,
        "share_twice_a_better": float((allr >= 2).mean()) if allr.size else None,
        "share_twice_a_worse": float((allr <= 0.5).mean()) if allr.size else None,
    }


def _read(r: dict[str, Any]) -> str:
    lo, hi = r["interval"]
    if np.isfinite(lo) and lo > 1.0:
        return "ctl-prior better"
    if np.isfinite(hi) and hi < 1.0:
        return "ctl-prior worse"
    return "not separated"


def score30(raw: Path, config: Path) -> dict[str, Any]:
    stem = config.stem
    engs = engagements(config, 1)
    rows_out: list[dict[str, Any]] = []
    missing = {"a": 0, "b": 0, "c": 0}
    planned = ran = 0
    s2_units: list[float] = []
    cost = {"a_s": 0.0, "b_s": 0.0, "c_s": 0.0, "a_windows": 0, "b_windows": 0, "c_windows": 0}
    for e in engs:
        a = load27(raw, f"{stem}-c1", e, 1)
        b2 = _load_2h(raw, stem, e)
        c = _load_joint(raw, stem, e)
        for key, got in (("a", a is not None), ("b", b2 is not None), ("c", c is not None)):
            if not got:
                missing[key] += 1
        if a is None:
            continue
        planned += a["planned"]
        ran += a["ran"]
        cost["a_s"] += sum(w["seconds"] for w in a["windows"])
        cost["a_windows"] += len(a["windows"])
        if b2 is not None:
            cost["b_s"] += b2["seconds"]
            cost["b_windows"] += b2["windows"]
        if c is not None:
            cost["c_s"] += sum(x["seconds"] for x in c.values())
            cost["c_windows"] += len(c)
        r = []
        for w in a["windows"]:
            x, y = w["med"]["ctl-d1-q0.01"]["range"], w["med"]["history-map"]["range"]
            if np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0:
                r.append(math.log(x / y))
        if r:
            s2_units.append(float(np.mean(r)))
        for w in a["windows"]:
            if w["index"] == 0:
                continue
            first, nrows = int(w["first"]), int(w["rows"])
            k = klass(turns_in(e, first, nrows))
            rec: dict[str, Any] = {
                "engagement": e.index,
                "hours": float(e.meta["hours"]),
                "index": int(w["index"]),
                "klass": k,
                "handed": w["carried"] is not None,
                "a": w["med"]["ctl-prior"],
                "a_ctl": w["med"]["ctl-d1-q0.01"],
                "a_carry": w["med"]["ctl-carry"],
                "carried": w["carried"],
            }
            if b2 is not None:
                sel = (b2["rows"] >= first) & (b2["rows"] < first + nrows)
                rec["b"] = _window_meds(b2["states"]["ctl-d1-q0.01"][sel], b2["rows"][sel], e)
                rec["b_prior"] = _window_meds(b2["states"]["ctl-prior"][sel], b2["rows"][sel], e)
            if c is not None and int(w["index"]) in c:
                rec["c"] = c[int(w["index"])]["ctl"]
                rec["c_ref"] = c[int(w["index"])]["ref"]
            tr = _truth(e, np.arange(first, first + nrows, 12))
            rec["range_km"] = float(
                np.median(np.hypot(tr[:, 0] - tr[:, 4], tr[:, 1] - tr[:, 5])) / 1e3
            )
            rows_out.append(rec)

    def ok(x: Any, q: str = "range") -> bool:
        return x is not None and np.isfinite(x[q]) and x[q] > 0

    def units(num: str, keep: Any, q: str = "range") -> list[np.ndarray]:
        by: dict[int, list[float]] = {}
        for rec in rows_out:
            if not keep(rec):
                continue
            n, d = rec.get(num), rec["a"]
            if n is not None and ok(n, q) and ok(d, q):
                by.setdefault(rec["engagement"], []).append(math.log(n[q] / d[q]))
        return [np.array(v) for v in by.values()]

    def decided(rec: dict[str, Any]) -> bool:
        return bool(
            rec["klass"] == "held"
            and rec["handed"]
            and ok(rec["a"])
            and ok(rec.get("b"))
            and ok(rec.get("c"))
        )

    held_all = [r for r in rows_out if r["klass"] == "held"]
    out: dict[str, Any] = {
        "config": str(config),
        "seed": json.loads(config.read_text())["seed"],
        "counts": {
            "held_windows": len(held_all),
            "held_handed": sum(1 for r in held_all if r["handed"]),
            "held_decided": sum(1 for r in held_all if decided(r)),
            "held_answered": {
                k: sum(1 for r in held_all if r["handed"] and ok(r.get(k))) for k in ("a", "b", "c")
            },
            "missing_engagements": missing,
        },
    }
    ests: dict[str, Any] = {}
    for name, num in (
        ("D1_2h_over_prior", "b"),
        ("D2_joint_over_prior", "c"),
        ("D3_prior2h_over_prior", "b_prior"),
    ):
        ests[name] = {q: _ratio(units(num, decided, q)) for q in QUANTITIES}
        ests[name]["reading"] = _read(ests[name]["range"])
    out["estimands"] = ests
    out["outcome"] = {k: d["reading"] for k, d in ests.items()}
    # beside
    b: dict[str, Any] = {
        "ctl1h_over_prior_held": _ratio(units("a_ctl", decided)),
        "carry1h_over_prior_held": _ratio(units("a_carry", decided)),
        "prior2h_over_prior_held": _ratio(units("b_prior", decided)),
        "span_reference_over_prior_held": _ratio(units("c_ref", decided)),
        "D1_one_turn": _ratio(
            units(
                "b",
                lambda r: r["klass"] == "one" and r["handed"] and ok(r["a"]) and ok(r.get("b")),
            )
        ),
        "D1_held_without_c": _ratio(
            units("b", lambda r: r["klass"] == "held" and r["handed"] and ok(r.get("b")))
        ),
    }
    for name, lo, hi in (("<15", 0, 15), ("15-25", 15, 25), (">25", 25, 1e9)):
        band = lambda r, lo=lo, hi=hi: decided(r) and lo <= r["range_km"] < hi  # noqa: E731
        b[f"D1_range_{name}"] = _ratio(units("b", band))
        b[f"D2_range_{name}"] = _ratio(units("c", band))
    med = {}
    for key in ("a", "a_ctl", "b", "b_prior", "c", "c_ref"):
        vals = [r[key]["range"] for r in rows_out if decided(r) and r.get(key) is not None]
        med[key] = float(np.nanmedian(vals)) if vals and np.isfinite(vals).any() else None
    b["median_error_held"] = med
    b["cost"] = {
        "a_s_per_window": cost["a_s"] / max(cost["a_windows"], 1),
        "b_s_per_window": cost["b_s"] / max(cost["b_windows"], 1),
        "c_s_per_held_window": cost["c_s"] / max(cost["c_windows"], 1),
        "a_hours": cost["a_s"] / 3600,
        "b_hours": cost["b_s"] / 3600,
        "c_hours": cost["c_s"] / 3600,
    }
    out["beside"] = b
    # soundness
    hits = []
    for rh in held_all:
        cw = rh["carried"]
        if cw is None:
            continue
        try:
            nees = float(cw["d"] @ np.linalg.solve(cw["cov"], cw["d"]))
        except np.linalg.LinAlgError:
            nees = math.inf
        hits.append(nees <= CHI2_4[0.05])
    cov = float(np.mean(hits)) if hits else math.nan

    def gm_eng(us: list[float]) -> float:
        return float(np.exp(np.mean(us))) if us else math.nan

    s2, s2lo, s2hi = _boot(s2_units, gm_eng, SEED)
    sound: dict[str, Any]
    s1 = all(v == 0 for v in missing.values()) and planned > 0 and ran / planned >= 0.95
    sound = {
        "S1_parts_present": {"missing": missing, "planned": planned, "ran": ran, "pass": bool(s1)},
        "S2_ctl_over_reference": {
            "value": s2,
            "interval": [s2lo, s2hi],
            "band": [0.8, 4.0],
            "pass": bool(0.8 <= s2 <= 4.0),
        },
        "S3_held_coverage": {
            "value": cov,
            "hand_overs": len(hits),
            "band": [0.80, 0.99],
            "pass": bool(np.isfinite(cov) and 0.80 <= cov <= 0.99),
        },
    }
    sound["pass"] = bool(all(x["pass"] for x in sound.values()))
    out["soundness"] = sound
    return out
