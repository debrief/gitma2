"""Spec 025's registered study: the estimands, computed from a `long.yml` run's outputs.

Engagements are configs/long/study-<split>.json's (realistic, 6 and 12 hours), regenerated here
(deterministic). Every error is the relative range error at a row, after the project's
plausibility rule (range in (0, 100 km], speed at most 25 m/s; otherwise the row is not
answered). Intervals are 95% percentile intervals from a bootstrap over engagements (the unit
that is drawn independently), 2,000 resamples, seeded.

* **E1** (contact 1, the contact the ownship tends): for each window both systems answer, r =
  median error of ``ctl`` ÷ median error of ``ctl-carry`` over the window's stored rows.
  The estimate is the geometric mean of r. ``ctl-carry`` is **non-inferior** if the
  interval's lower limit is at least 0.95, i.e. it is not more than 5% worse. Reported beside:
  the median r; the shares of windows better, worse and level, and twice better or worse;
  the CPU hours of the search from nothing against that from the carry. The same for contact 2
  is reported, and decides nothing.
* **E2** (the cost of an untended contact): ``ctl``'s stitched rows on both contacts, banded by
  true range (2–10, 10–20, 20–40 km). In each band with at least 50 rows on both contacts:
  median error on contact 2 ÷ on contact 1. The estimate is the geometric mean over those
  bands. It is a magnitude, with no rule.
* **E3** (the IMM's drift; 12-hour engagements, contact 1): the IMM run over the whole
  engagement, read every 10 minutes from five minutes after the first ownship turn. The
  estimate is the median error in hours 6–12 ÷ that in hours 0–6. Drift is **shown** if the
  interval lies wholly above 1. Reported beside: the share answered by 2-hour bin.
* **Soundness** (read on validation; a failure stops the study):
  * S1: at least 95% of contact 1's planned windows ran;
  * S2: ``ctl`` ÷ the true-history fit in pooled median error, contact 1, lies in [0.8, 4];
  * S3: contact 1's share of bearings held lies in [0.6, 0.95].
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .sim import Engagement, generate
from .timelate import stitch

TL = ("ctl-d1-q0.01", "ctl-carry", "c2", "history-map")
BANDS_KM = ((2.0, 10.0), (10.0, 20.0), (20.0, 40.0))
MIN_BAND_ROWS = 50
NON_INFERIORITY = 0.95
RESAMPLES = 2000
BOOT_SEED = 25


def plausible(states: np.ndarray, truth: np.ndarray) -> np.ndarray:
    s = np.array(states, dtype=np.float64, copy=True)
    rng = np.hypot(s[:, 0] - truth[:, 4], s[:, 1] - truth[:, 5])
    bad = ~((rng > 0) & (rng <= 100_000.0) & (np.hypot(s[:, 2], s[:, 3]) <= 25.0))
    s[bad] = np.nan
    return s


def range_error(states: np.ndarray, truth: np.ndarray) -> np.ndarray:
    s = plausible(states, truth)
    true = np.hypot(truth[:, 0] - truth[:, 4], truth[:, 1] - truth[:, 5])
    est = np.hypot(s[:, 0] - truth[:, 4], s[:, 1] - truth[:, 5])
    out: np.ndarray = np.abs(est - true) / true
    return out


def engagements(config: Path, contact: int) -> list[Engagement]:
    cfg = json.loads(config.read_text())
    R = json.loads((config.parents[2] / cfg["target_ranges"]).read_text())
    out = []
    i = 0
    for h in cfg["hours"]:
        for _ in range(int(cfg["engagements_per_duration"])):
            e = generate(int(cfg["seed"]), i, float(h), cfg, R)
            x = e.other if contact == 2 else e
            if x is None:
                raise ValueError(f"{config} has no second contact")
            out.append(x)
            i += 1
    return out


def _truth(e: Engagement, rows: np.ndarray) -> np.ndarray:
    return np.stack(
        [
            e.tgt[rows, 1],
            e.tgt[rows, 2],
            e.tgt[rows, 3],
            e.tgt[rows, 4],
            e.own[rows, 1],
            e.own[rows, 2],
        ],
        axis=1,
    )


def load_carry(raw: Path, stem: str, e: Engagement) -> dict[str, Any] | None:
    files = sorted(raw.glob(f"{stem}-carry-{e.index}.json"))
    if not files:
        return None
    head = json.loads(files[0].read_text())
    z = np.load(files[0].with_suffix(".npz"))
    wins = []
    for w in head["windows"]:
        j = w["index"]
        wins.append(w | {"rows_abs": z[f"w{j}_rows"], "tracks": {s: z[f"w{j}_{s}"] for s in TL}})
    wins.sort(key=lambda w: w["index"])
    st = stitch(e, wins, int(head["settings"]["score_every"]), TL, ("ctl-d1-q0.01", "ctl-carry"))
    per_window = []
    for w in wins:
        tr = _truth(e, w["rows_abs"])
        med = {}
        for s in ("ctl-d1-q0.01", "ctl-carry"):
            err = range_error(w["tracks"][s], tr)
            med[s] = float(np.nanmedian(err)) if np.isfinite(err).any() else math.nan
        ss = w.get("search_s", {})
        per_window.append(
            {
                "ctl": med["ctl-d1-q0.01"],
                "carry": med["ctl-carry"],
                "none_s": float(ss.get("none", 0.0)),
                "carry_s": float(ss.get("carry", 0.0)),
                "seconds": float(w["seconds"]),
            }
        )
    return {
        "planned": len(head["chain"]),
        "ran": len(wins),
        "per_window": per_window,
        "rows": st["rows"],
        "truth": st["truth"],
        "errors": {s: range_error(st["states"][s], st["truth"]) for s in TL},
    }


def load_imm(raw: Path, stem: str, e: Engagement) -> dict[str, Any] | None:
    f = raw / f"{stem}-imm-{e.index}.npz"
    if not f.exists():
        return None
    z = np.load(f)
    return {"hours": z["times_s"] / 3600.0, "error": range_error(z["state_imm"], z["truth"])}


def _boot(units: list[Any], stat: Any, seed: int = BOOT_SEED) -> tuple[float, float, float]:
    """(estimate, lower, upper): ``stat`` over the units, and its bootstrap over units."""
    est = stat(units)
    g = np.random.default_rng(seed)
    n = len(units)
    vals = []
    for _ in range(RESAMPLES):
        pick = [units[i] for i in g.integers(0, n, n)]
        v = stat(pick)
        if np.isfinite(v):
            vals.append(v)
    if not vals:
        return est, math.nan, math.nan
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(est), float(lo), float(hi)


def e1(carry: list[dict[str, Any]]) -> dict[str, Any]:
    units = []
    for c in carry:
        r = [w["ctl"] / w["carry"] for w in c["per_window"] if w["ctl"] > 0 and w["carry"] > 0]
        r = [x for x in r if np.isfinite(x)]
        if r:
            units.append(np.log(np.array(r)))

    def gm(us: list[np.ndarray]) -> float:
        return float(np.exp(np.concatenate(us).mean())) if us else math.nan

    est, lo, hi = _boot(units, gm)
    allr = np.exp(np.concatenate(units)) if units else np.zeros(0)
    none_h = sum(w["none_s"] for c in carry for w in c["per_window"]) / 3600
    carry_h = sum(w["carry_s"] for c in carry for w in c["per_window"]) / 3600
    total_h = sum(w["seconds"] for c in carry for w in c["per_window"]) / 3600
    return {
        "engagements": len(units),
        "windows": int(allr.size),
        "gm_ctl_over_carry": est,
        "interval": [lo, hi],
        "non_inferior": bool(lo >= NON_INFERIORITY),
        "median": float(np.median(allr)) if allr.size else None,
        "better": int((allr > 1).sum()),
        "worse": int((allr < 1).sum()),
        "level": int((allr == 1).sum()),
        "twice_better": int((allr >= 2).sum()),
        "twice_worse": int((allr <= 0.5).sum()),
        "cpu_h": {
            "search_from_none": none_h,
            "search_from_carry": carry_h,
            "windows_total": total_h,
        },
    }


def e2(c1: list[dict[str, Any] | None], c2: list[dict[str, Any] | None]) -> dict[str, Any]:
    units = []
    for a, b in zip(c1, c2, strict=True):
        if a is None or b is None:
            continue
        ra = (
            np.hypot(a["truth"][:, 0] - a["truth"][:, 4], a["truth"][:, 1] - a["truth"][:, 5]) / 1e3
        )
        rb = (
            np.hypot(b["truth"][:, 0] - b["truth"][:, 4], b["truth"][:, 1] - b["truth"][:, 5]) / 1e3
        )
        units.append((ra, a["errors"]["ctl-d1-q0.01"], rb, b["errors"]["ctl-d1-q0.01"]))

    def stat(us: list[Any], detail: bool = False) -> Any:
        logs, rows = [], []
        for lo_km, hi_km in BANDS_KM:
            ea = (
                np.concatenate([u[1][(u[0] >= lo_km) & (u[0] < hi_km)] for u in us])
                if us
                else np.zeros(0)
            )
            eb = (
                np.concatenate([u[3][(u[2] >= lo_km) & (u[2] < hi_km)] for u in us])
                if us
                else np.zeros(0)
            )
            ea, eb = ea[np.isfinite(ea)], eb[np.isfinite(eb)]
            ok = ea.size >= MIN_BAND_ROWS and eb.size >= MIN_BAND_ROWS
            if ok:
                logs.append(math.log(np.median(eb) / np.median(ea)))
            rows.append(
                {
                    "band_km": [lo_km, hi_km],
                    "rows_c1": int(ea.size),
                    "rows_c2": int(eb.size),
                    "median_c1": float(np.median(ea)) if ea.size else None,
                    "median_c2": float(np.median(eb)) if eb.size else None,
                    "used": ok,
                }
            )
        v = math.exp(float(np.mean(logs))) if logs else math.nan
        return (v, rows) if detail else v

    est, lo, hi = _boot(units, stat)
    _v, bands = stat(units, detail=True)
    return {"engagements": len(units), "gm_c2_over_c1": est, "interval": [lo, hi], "bands": bands}


def e3(imm: list[dict[str, Any] | None]) -> dict[str, Any]:
    units = [u for u in imm if u is not None and u["hours"].size]

    def stat(us: list[dict[str, Any]]) -> float:
        if not us:
            return math.nan
        late = np.concatenate([u["error"][(u["hours"] >= 6) & (u["hours"] < 12)] for u in us])
        early = np.concatenate([u["error"][u["hours"] < 6] for u in us])
        late, early = late[np.isfinite(late)], early[np.isfinite(early)]
        if not late.size or not early.size:
            return math.nan
        return float(np.median(late) / np.median(early))

    est, lo, hi = _boot(units, stat)
    bins = []
    for b in range(0, 12, 2):
        sel = [u["error"][(u["hours"] >= b) & (u["hours"] < b + 2)] for u in units]
        allv = np.concatenate(sel) if sel else np.zeros(0)
        ok = allv[np.isfinite(allv)]
        bins.append(
            {
                "hours": [b, b + 2],
                "answered": float(ok.size / allv.size) if allv.size else None,
                "median": float(np.median(ok)) if ok.size else None,
            }
        )
    return {
        "engagements": len(units),
        "late_over_early": est,
        "interval": [lo, hi],
        "drift_shown": bool(lo > 1.0),
        "bins": bins,
    }


def soundness(c1: list[dict[str, Any] | None], engs: list[Engagement]) -> dict[str, Any]:
    planned = sum(c["planned"] for c in c1 if c)
    ran = sum(c["ran"] for c in c1 if c)
    missing = sum(1 for c in c1 if c is None)
    ctl = np.concatenate([c["errors"]["ctl-d1-q0.01"] for c in c1 if c])
    ref = np.concatenate([c["errors"]["history-map"] for c in c1 if c])
    ratio = float(np.nanmedian(ctl) / np.nanmedian(ref))
    held = float(np.mean([(e.obs[:, 2] != 0).mean() for e in engs]))
    s1 = (ran / planned if planned else 0.0) >= 0.95 and missing == 0
    return {
        "S1_windows_ran": {
            "planned": planned,
            "ran": ran,
            "engagements_missing": missing,
            "pass": bool(s1),
        },
        "S2_ctl_over_reference": {
            "value": ratio,
            "band": [0.8, 4.0],
            "pass": bool(0.8 <= ratio <= 4.0),
        },
        "S3_bearings_held": {"value": held, "band": [0.6, 0.95], "pass": bool(0.6 <= held <= 0.95)},
        "pass": bool(s1 and 0.8 <= ratio <= 4.0 and 0.6 <= held <= 0.95),
    }


def score(raw: Path, config: Path) -> dict[str, Any]:
    stem = config.stem
    e1s = engagements(config, 1)
    e2s = engagements(config, 2)
    c1 = [load_carry(raw, f"{stem}-c1", e) for e in e1s]
    c2 = [load_carry(raw, f"{stem}-c2", e) for e in e2s]
    hours = [float(e.meta["hours"]) for e in e1s]
    imm = [
        load_imm(raw, f"{stem}-c1", e) if h == 12.0 else None
        for e, h in zip(e1s, hours, strict=True)
    ]
    out: dict[str, Any] = {
        "config": str(config),
        "seed": json.loads(config.read_text())["seed"],
        "soundness": soundness(c1, e1s),
        "E1": e1([c for c in c1 if c]),
        "E1_contact2_reported": e1([c for c in c2 if c and c["per_window"]]),
        "E2": e2(c1, c2),
        "E3": e3(imm),
        "by_duration": {},
    }
    for h in sorted(set(hours)):
        sel = [c for c, hh in zip(c1, hours, strict=True) if hh == h and c]
        out["by_duration"][f"{h:g}h"] = {
            "E1": e1(sel),
            "median_error": {
                s: float(np.nanmedian(np.concatenate([c["errors"][s] for c in sel])))
                if sel
                else None
                for s in TL
            },
        }
    return out
