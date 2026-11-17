"""Spec 023's record: summary.json and tables.md from a `long.yml` run's outputs.

    uv run python scripts/research/long_report.py --raw experiments/20261117-long/raw \\
        --out experiments/20261117-long

Engagements are regenerated from configs/long/long.json (deterministic) for the truth and the
stitching. Medians are over the rows a system answered; the share answered is given beside.
An investigation's measurement, never a gate result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RT = ("e", "c2", "one_leg", "imm")
TL = ("ctl-d1-q0.01", "c2", "history-best")
LABEL = {
    "e": "E (carried model)",
    "c2": "C″",
    "one_leg": "one leg (30 min)",
    "imm": "IMM",
    "ctl-d1-q0.01": "standing control ctl",
    "history-best": "true-history fit (reference)",
}
SEAM_S = 900.0


def engagements() -> list[Any]:
    from tma2.long.sim import generate_all

    cfg = json.loads((ROOT / "configs/long/long.json").read_text())
    R = json.loads((ROOT / cfg["target_ranges"]).read_text())
    return generate_all(cfg, R)


def plausible(states: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """States with the project's plausibility rule applied (``eval.errors.plausible_row``: range
    in (0, 100 km], speed at most 25 m/s); an implausible row is no answer (NaN)."""
    s = np.array(states, dtype=np.float64, copy=True)
    rng = np.hypot(s[:, 0] - truth[:, 4], s[:, 1] - truth[:, 5])
    bad = ~((rng > 0) & (rng <= 100_000.0) & (np.hypot(s[:, 2], s[:, 3]) <= 25.0))
    s[bad] = np.nan
    return s


def stats(states: np.ndarray, truth: np.ndarray) -> dict[str, Any]:
    from tma2.timelate.score import row_errors

    err = row_errors(plausible(states, truth), truth)
    ok = np.isfinite(err[:, 0])
    out: dict[str, Any] = {"rows": int(ok.size), "answered": float(ok.mean()) if ok.size else 0.0}
    for j, k in enumerate(("range_rel", "course_deg", "speed_kt")):
        v = err[ok, j]
        out[k] = float(np.median(v)) if v.size else None
        out[f"{k}_q90"] = float(np.quantile(v, 0.9)) if v.size else None
    return out


def realtime(raw: Path, e: Any) -> dict[str, Any] | None:
    files = sorted(raw.glob(f"realtime-{e.index}*.json"))
    if not files:
        return None
    parts = []
    secs = {s: 0.0 for s in RT}
    cpu = set()
    for f in files:
        head = json.loads(f.read_text())
        z = np.load(f.with_suffix(".npz"))
        parts.append(z)
        for s in RT:
            secs[s] += float(head["seconds"][s])
        cpu.add(head["cpu_model"])
    order = np.argsort([int(p["rows"][0]) if p["rows"].size else 0 for p in parts])
    parts = [parts[i] for i in order]
    times = np.concatenate([p["times_s"] for p in parts])
    truth = np.concatenate([p["truth"] for p in parts])
    st = {s: np.concatenate([p[f"state_{s}"] for p in parts]) for s in RT}
    n = int(times.size)
    out: dict[str, Any] = {
        "evaluations": n,
        "systems": {s: stats(st[s], truth) for s in RT},
        "seconds_per_evaluation": {s: secs[s] / max(n, 1) for s in RT if s != "imm"},
        "imm_seconds_whole": secs["imm"],
        "cpu": sorted(cpu),
    }
    # by six-hour block of the engagement
    blocks = []
    for b0 in np.arange(0, e.meta["hours"] * 3600, 6 * 3600):
        m = (times >= b0) & (times < b0 + 6 * 3600)
        if m.any():
            blocks.append(
                {"from_h": float(b0 / 3600)}
                | {s: stats(st[s][m], truth[m])["range_rel"] for s in RT}
            )
    out["blocks"] = blocks
    out["_arrays"] = {"times": times, "truth": truth, "states": st}
    return out


def timelate(raw: Path, e: Any) -> dict[str, Any] | None:
    from tma2.long.timelate import stitch

    files = sorted(raw.glob(f"timelate-{e.index}*.json"))
    if not files:
        return None
    wins: list[dict[str, Any]] = []
    chain = None
    cpu = set()
    every = 6
    for f in files:
        head = json.loads(f.read_text())
        chain = head["chain"]
        every = int(head["settings"]["score_every"])
        cpu.add(head["cpu_model"])
        z = np.load(f.with_suffix(".npz"))
        for w in head["windows"]:
            j = w["index"]
            wins.append(
                w
                | {
                    "rows_abs": z[f"w{j}_rows"],
                    "tracks": {s: z[f"w{j}_{s}"] for s in TL},
                }
            )
    wins.sort(key=lambda w: w["index"])
    st = stitch(e, wins, every)
    rows = st["rows"]
    t = rows * e.dt
    missing = sorted(set(range(len(chain or []))) - {w["index"] for w in wins})
    out: dict[str, Any] = {
        "windows": len(wins),
        "windows_planned": len(chain or []),
        "windows_missing": missing,
        "systems": {s: stats(st["states"][s], st["truth"]) for s in TL},
        "seconds_per_window": {
            "median": float(np.median([w["seconds"] for w in wins])),
            "max": float(np.max([w["seconds"] for w in wins])),
            "total": float(np.sum([w["seconds"] for w in wins])),
        },
        "true_manoeuvres": len(e.meta["manoeuvres"]),
        "declared": {s: len(v) for s, v in st["declared"].items()},
        "cpu": sorted(cpu),
    }
    # error near the seams (centre of each overlap) against elsewhere
    seams = []
    for (a, n), (b, _m) in zip(chain[:-1], chain[1:], strict=True):
        seams.append(0.5 * ((a + n) + b) * e.dt)
    near = np.zeros(rows.size, dtype=bool)
    for s_ in seams:
        near |= np.abs(t - s_) <= SEAM_S
    out["seams"] = {
        s: {
            "near": stats(st["states"][s][near], st["truth"][near])["range_rel"],
            "elsewhere": stats(st["states"][s][~near], st["truth"][~near])["range_rel"],
        }
        for s in TL
    }
    out["_arrays"] = {"rows": rows, "truth": st["truth"], "states": st["states"]}
    out["_declared"] = st["declared"]
    out["_windows"] = [
        {k: w[k] for k in ("index", "first", "rows", "seconds", "true", "declared")} for w in wins
    ]
    return out


def scaling(raw: Path) -> list[dict[str, Any]]:
    rows = []
    for f in sorted(raw.glob("scaling-*.json")):
        head = json.loads(f.read_text())
        for r in head["scaling"]:
            rows.append(
                {k: r[k] for k in ("seconds_long", "true_manoeuvres", "declared", "run_s")}
                | {"search_s": float(sum(v for k, v in r["parts"].items() if "/" in k))}
                | {"cpu": head["cpu_model"]}
            )
    return sorted(rows, key=lambda r: r["seconds_long"])


def fmt(v: Any, d: int = 2, pct: bool = False) -> str:
    if v is None:
        return "–"
    return f"{100 * v:.{d - 1}f}%" if pct else f"{v:.{d}f}"


def tables(summary: dict[str, Any]) -> str:
    L = [
        "# Long engagements: the standing systems on 6 to 48 hours (spec 023)",
        "",
        "Generated by `scripts/research/long_report.py` from `summary.json`; do not edit.",
        "One engagement per duration (seed 348). A feasibility measurement, not a result.",
        "",
        "## Engagements",
        "",
        "| hours | samples (5 s) | target manoeuvres | ownship turns | range min / median / max km |",
        "|---|---|---|---|---|",
    ]
    for g in summary["engagements"]:
        L.append(
            f"| {g['hours']:g} | {g['samples']} | {g['manoeuvres']} | {g['ownship_turns']} | "
            f"{g['range_km'][0]:.1f} / {g['range_km'][1]:.1f} / {g['range_km'][2]:.1f} |"
        )
    L += ["", "## Real-time: every 10 minutes from the bearings so far", ""]
    L += [
        "Median relative range error (share of evaluations answered); course ° and speed kt.",
        "",
        "| hours | " + " | ".join(LABEL[s] for s in RT) + " |",
        "|---|" + "---|" * len(RT),
    ]
    for g in summary["engagements"]:
        r = g.get("realtime")
        if not r:
            continue
        cells = []
        for s in RT:
            x = r["systems"][s]
            cells.append(
                f"{fmt(x['range_rel'], 2, True)} ({fmt(x['answered'], 2)}); "
                f"{fmt(x['course_deg'], 1)}°, {fmt(x['speed_kt'], 1)} kt"
            )
        L.append(f"| {g['hours']:g} | " + " | ".join(cells) + " |")
    L += ["", "Run time per evaluation, seconds (one CPU core; IMM: whole engagement once):", ""]
    L += ["| hours | E | C″ | one leg | IMM whole |", "|---|---|---|---|---|"]
    for g in summary["engagements"]:
        r = g.get("realtime")
        if r:
            p = r["seconds_per_evaluation"]
            L.append(
                f"| {g['hours']:g} | {p['e']:.1f} | {p['c2']:.1f} | {p['one_leg']:.2f} | "
                f"{r['imm_seconds_whole']:.1f} |"
            )
    L += ["", "Median relative range error by six-hour block:", ""]
    L += [
        "| hours | from h | " + " | ".join(LABEL[s] for s in RT) + " |",
        "|---|---|" + "---|" * len(RT),
    ]
    for g in summary["engagements"]:
        r = g.get("realtime")
        for b in (r or {}).get("blocks", []):
            L.append(
                f"| {g['hours']:g} | {b['from_h']:g} | "
                + " | ".join(fmt(b[s], 2, True) for s in RT)
                + " |"
            )
    L += ["", "## Time-late: ctl on 2-hour windows overlapping by 30 minutes, stitched", ""]
    L += [
        "| hours | windows | "
        + " | ".join(LABEL[s] for s in TL)
        + " | declared / true manoeuvres |",
        "|---|---|" + "---|" * len(TL) + "---|",
    ]
    for g in summary["engagements"]:
        r = g.get("timelate")
        if not r:
            continue
        cells = [
            f"{fmt(r['systems'][s]['range_rel'], 2, True)} ({fmt(r['systems'][s]['answered'], 2)}); "
            f"{fmt(r['systems'][s]['course_deg'], 1)}°, {fmt(r['systems'][s]['speed_kt'], 1)} kt"
            for s in TL
        ]
        L.append(
            f"| {g['hours']:g} | {r['windows']}/{r['windows_planned']} | "
            + " | ".join(cells)
            + f" | ctl {r['declared']['ctl-d1-q0.01']}, C″ {r['declared']['c2']} / "
            f"{r['true_manoeuvres']} |"
        )
    L += [
        "",
        "Run time per window (minutes) and error near the seams (±15 min of an overlap's middle):",
        "",
    ]
    L += [
        "| hours | median min | max min | total h | ctl near seams | ctl elsewhere |",
        "|---|---|---|---|---|---|",
    ]
    for g in summary["engagements"]:
        r = g.get("timelate")
        if r:
            w = r["seconds_per_window"]
            sm = r["seams"]["ctl-d1-q0.01"]
            L.append(
                f"| {g['hours']:g} | {w['median'] / 60:.1f} | {w['max'] / 60:.1f} | "
                f"{w['total'] / 3600:.2f} | {fmt(sm['near'], 2, True)} | "
                f"{fmt(sm['elsewhere'], 2, True)} |"
            )
    if summary["scaling"]:
        L += ["", "## ctl on one period of growing length (the 24-hour engagement)", ""]
        L += [
            "| period h | true manoeuvres | declared | run time min | search min |",
            "|---|---|---|---|---|",
        ]
        for r in summary["scaling"]:
            L.append(
                f"| {r['seconds_long'] / 3600:g} | {r['true_manoeuvres']} | {r['declared']} | "
                f"{r['run_s'] / 60:.1f} | {r['search_s'] / 60:.1f} |"
            )
    return "\n".join(L) + "\n"


def build(raw: Path) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    full: dict[int, dict[str, Any]] = {}
    out = []
    for e in engagements():
        rng = np.hypot(e.tgt[:, 1] - e.own[:, 1], e.tgt[:, 2] - e.own[:, 2]) / 1e3
        g: dict[str, Any] = {
            "index": e.index,
            "hours": e.meta["hours"],
            "samples": e.samples,
            "manoeuvres": len(e.meta["manoeuvres"]),
            "ownship_turns": len(e.meta["ownship_turns"]),
            "range_km": [float(rng.min()), float(np.median(rng)), float(rng.max())],
        }
        rt, tl = realtime(raw, e), timelate(raw, e)
        full[e.index] = {"e": e, "realtime": rt, "timelate": tl}
        if rt:
            g["realtime"] = {k: v for k, v in rt.items() if not k.startswith("_")}
        if tl:
            g["timelate"] = {k: v for k, v in tl.items() if not k.startswith("_")}
        out.append(g)
    return {"engagements": out, "scaling": scaling(raw)}, full


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="experiments/20261117-long/raw")
    ap.add_argument("--out", default="experiments/20261117-long")
    a = ap.parse_args(argv)
    summary, _ = build(ROOT / a.raw)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (out / "tables.md").write_text(tables(summary))
    print((out / "tables.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
