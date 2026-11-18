"""Spec 024's record: summary.json and tables.md from a `long.yml` run's outputs.

    uv run python scripts/research/long2_report.py \\
        [--raw experiments/20261117-long2/raw] [--base experiments/20261117-long/raw] \\
        [--out experiments/20261117-long2]

Three sets of engagements: ``base`` (spec 023's, configs/long/long.json), ``real-c1`` and
``real-c2`` (configs/long/realistic.json, contacts 1 and 2). For each and each duration:
``ctl`` and ``ctl-carry`` stitched over the chain (with C″ and the true-history fit beside), the
incremental real-time run, and for ``base`` spec 023's per-window run beside it. Engagements are
regenerated from their configs (deterministic). Medians are over the rows a system answered
(the plausibility rule); the share answered is given beside. A feasibility measurement, never a
gate result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "research"))

from long_report import RT, stats  # noqa: E402
from long_report import realtime as realtime023  # noqa: E402

TL = ("ctl-d1-q0.01", "ctl-carry", "c2", "history-map")
LABEL = {
    "ctl-d1-q0.01": "ctl",
    "ctl-carry": "ctl-carry",
    "c2": "C″",
    "history-map": "true-history fit (reference)",
    "e": "E",
    "one_leg": "one leg (30 min)",
    "imm": "IMM",
}
SETS = {
    "base": ("configs/long/long.json", 1, ""),
    "real-c1": ("configs/long/realistic.json", 1, "realistic-c1-"),
    "real-c2": ("configs/long/realistic.json", 2, "realistic-c2-"),
}
SET_LABEL = {
    "base": "spec 023's engagements",
    "real-c1": "realistic, contact 1 (the one the ownship tends)",
    "real-c2": "realistic, contact 2",
}


def engagements(config: str, contact: int) -> list[Any]:
    from tma2.long.sim import generate

    cfg = json.loads((ROOT / config).read_text())
    R = json.loads((ROOT / cfg["target_ranges"]).read_text())
    out = []
    for i, h in enumerate(cfg["hours"]):
        e = generate(int(cfg["seed"]), i, float(h), cfg, R)
        out.append(e.other if contact == 2 else e)
    return out


def carry_part(raw: Path, prefix: str, e: Any) -> dict[str, Any] | None:
    from tma2.long.timelate import stitch

    files = sorted(raw.glob(f"{prefix}carry-{e.index}.json")) + sorted(
        raw.glob(f"{prefix}carry-{e.index}-*of*.json")
    )
    if not files:
        return None
    wins: list[dict[str, Any]] = []
    chain: list[Any] = []
    every = 6
    cpu = set()
    for f in files:
        head = json.loads(f.read_text())
        chain = head["chain"]
        every = int(head["settings"]["score_every"])
        cpu.add(head["cpu_model"])
        z = np.load(f.with_suffix(".npz"))
        for w in head["windows"]:
            j = w["index"]
            wins.append(
                w | {"rows_abs": z[f"w{j}_rows"], "tracks": {s: z[f"w{j}_{s}"] for s in TL}}
            )
    wins.sort(key=lambda w: w["index"])
    st = stitch(e, wins, every, TL, ("ctl-d1-q0.01", "ctl-carry", "c2"))
    truth = st["truth"]
    per_window = []
    for w in wins:
        tr = np.stack(
            [e.tgt[w["rows_abs"], k] for k in (1, 2, 3, 4)]
            + [e.own[w["rows_abs"], 1], e.own[w["rows_abs"], 2]],
            axis=1,
        )
        a = stats(w["tracks"]["ctl-d1-q0.01"], tr)["range_rel"]
        b = stats(w["tracks"]["ctl-carry"], tr)["range_rel"]
        ss = w.get("search_s", {})
        per_window.append(
            {
                "index": w["index"],
                "ctl": a,
                "carry": b,
                "seconds": w["seconds"],
                "search_none_s": ss.get("none", 0.0),
                "search_carry_s": ss.get("carry", 0.0),
                "bearings": w["bearings"],
            }
        )
    both = [x for x in per_window if x["ctl"] and x["carry"]]
    ratios = np.array([x["ctl"] / x["carry"] for x in both]) if both else np.zeros(0)
    out: dict[str, Any] = {
        "windows": len(wins),
        "windows_planned": len(chain),
        "systems": {s: stats(st["states"][s], truth) for s in TL},
        "declared": {s: len(v) for s, v in st["declared"].items()},
        "true_manoeuvres": len(e.meta["manoeuvres"]),
        "window_ratio_ctl_over_carry": {
            "median": float(np.median(ratios)) if ratios.size else None,
            "carry_better": int((ratios > 1.0).sum()),
            "carry_worse": int((ratios < 1.0).sum()),
            "level": int((ratios == 1.0).sum()),
            "twice_better": int((ratios >= 2.0).sum()),
            "twice_worse": int((ratios <= 0.5).sum()),
        },
        "seconds": {
            "total_h": float(sum(x["seconds"] for x in per_window) / 3600),
            "search_from_none_h": float(sum(x["search_none_s"] for x in per_window) / 3600),
            "search_from_carry_h": float(sum(x["search_carry_s"] for x in per_window) / 3600),
        },
        "cpu": sorted(cpu),
        "_per_window": per_window,
        "_arrays": {"rows": st["rows"], "truth": truth, "states": st["states"]},
        "_declared": st["declared"],
        "_windows": [{k: w[k] for k in ("index", "first", "rows", "seconds")} for w in wins],
    }
    return out


def realtime_part(raw: Path, prefix: str, e: Any) -> dict[str, Any] | None:
    files = sorted(raw.glob(f"{prefix}realtime-inc-{e.index}.json")) + sorted(
        raw.glob(f"{prefix}realtime-inc-{e.index}-*of*.json")
    )
    if not files:
        return None
    parts, secs, cpu = [], {s: 0.0 for s in RT}, set()
    for f in files:
        head = json.loads(f.read_text())
        z = np.load(f.with_suffix(".npz"))
        if z["rows"].size:
            parts.append(z)
        for s in RT:
            secs[s] += float(head["seconds"][s])
        cpu.add(head["cpu_model"])
    parts.sort(key=lambda p: int(p["rows"][0]))
    times = np.concatenate([p["times_s"] for p in parts])
    truth = np.concatenate([p["truth"] for p in parts])
    st = {s: np.concatenate([p[f"state_{s}"] for p in parts]) for s in RT}
    n = int(times.size)
    return {
        "evaluations": n,
        "systems": {s: stats(st[s], truth) for s in RT},
        "seconds_per_evaluation": {s: secs[s] / max(n, 1) for s in RT if s != "imm"},
        "imm_seconds_whole": secs["imm"] / len(files),
        "cpu": sorted(cpu),
        "_arrays": {"times": times, "truth": truth, "states": st},
    }


def build(raw: Path, base_raw: Path) -> tuple[dict[str, Any], dict[str, dict[int, Any]]]:
    summary: dict[str, Any] = {"sets": {}}
    full: dict[str, dict[int, Any]] = {}
    for name, (config, contact, prefix) in SETS.items():
        rows = []
        full[name] = {}
        for e in engagements(config, contact):
            rng = np.hypot(e.tgt[:, 1] - e.own[:, 1], e.tgt[:, 2] - e.own[:, 2]) / 1e3
            g: dict[str, Any] = {
                "index": e.index,
                "hours": e.meta["hours"],
                "manoeuvres": len(e.meta["manoeuvres"]),
                "ownship_turns": len(e.meta["ownship_turns"]),
                "range_km": [float(rng.min()), float(np.median(rng)), float(rng.max())],
                "valid_share": float((e.obs[:, 2] != 0).mean()),
            }
            if "realism" in e.meta:
                rz = e.meta["realism"]
                g["gaps"] = len(rz["gaps_s"])
                g["steering"] = rz.get("steering")
                g["swapped_bearings"] = rz.get("swapped_bearings")
            tl = carry_part(raw, prefix, e)
            rt = realtime_part(raw, prefix, e)
            full[name][e.index] = {"e": e, "carry": tl, "realtime": rt}
            if tl:
                g["timelate"] = {k: v for k, v in tl.items() if not k.startswith("_")}
            if rt:
                g["realtime"] = {k: v for k, v in rt.items() if not k.startswith("_")}
            if name == "base":
                old = realtime023(base_raw, e)
                if old:
                    g["realtime_per_window"] = {
                        k: v for k, v in old.items() if not k.startswith("_")
                    }
                    full[name][e.index]["realtime_per_window"] = old
            rows.append(g)
        summary["sets"][name] = rows
    return summary, full


def pct(v: Any, d: int = 1) -> str:
    return "–" if v is None else f"{100 * v:.{d}f}%"


def tables(summary: dict[str, Any]) -> str:
    L = [
        "# Long engagements: carrying state, an incremental C, realism (spec 024)",
        "",
        "Generated by `scripts/research/long2_report.py` from `summary.json`; do not edit.",
        "One engagement per duration (seed 348); realism from a stream of its own, so contact 1",
        "of the realistic set is spec 023's target under the new sensor and steering. A",
        "feasibility measurement, not a result.",
    ]
    for name, rows in summary["sets"].items():
        L += ["", f"## {SET_LABEL[name]}", ""]
        L += [
            "| hours | manoeuvres | bearings held | range min / median / max km | gaps | ownship legs planned / lost |",
            "|---|---|---|---|---|---|",
        ]
        for g in rows:
            sr = g.get("steering") or {}
            L.append(
                f"| {g['hours']:g} | {g['manoeuvres']} | {pct(g['valid_share'], 0)} | "
                f"{g['range_km'][0]:.1f} / {g['range_km'][1]:.1f} / {g['range_km'][2]:.1f} | "
                f"{g.get('gaps', '–')} | "
                + (f"{sr.get('planned', '–')} / {sr.get('lost', '–')}" if sr else "–")
                + " |"
            )
        L += [
            "",
            "Time-late, stitched: median relative range error (share answered); course °, speed kt.",
            "",
        ]
        L += [
            "| hours | " + " | ".join(LABEL[s] for s in TL) + " | declared ctl / carry / true |",
            "|---|" + "---|" * (len(TL) + 1),
        ]
        for g in rows:
            t = g.get("timelate")
            if not t:
                continue
            cells = [
                f"{pct(t['systems'][s]['range_rel'])} ({t['systems'][s]['answered']:.2f}); "
                f"{(t['systems'][s]['course_deg'] or float('nan')):.1f}°, {(t['systems'][s]['speed_kt'] or float('nan')):.1f} kt"
                for s in TL
            ]
            L.append(
                f"| {g['hours']:g} | "
                + " | ".join(cells)
                + f" | {t['declared'].get('ctl-d1-q0.01', 0)} / {t['declared'].get('ctl-carry', 0)} / {t['true_manoeuvres']} |"
            )
        L += [
            "",
            "Carry against ctl, window by window (ratio ctl ÷ carry in median range error; above 1: carry better), and run time:",
            "",
        ]
        L += [
            "| hours | windows | median ratio | carry better / worse / level | twice better / worse | CPU h | search from nothing h | from the carry h |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for g in rows:
            t = g.get("timelate")
            if not t:
                continue
            r = t["window_ratio_ctl_over_carry"]
            sc = t["seconds"]
            med = "–" if r["median"] is None else f"{r['median']:.3f}"
            L.append(
                f"| {g['hours']:g} | {t['windows']}/{t['windows_planned']} | {med} | "
                f"{r['carry_better']} / {r['carry_worse']} / {r['level']} | {r['twice_better']} / {r['twice_worse']} | "
                f"{sc['total_h']:.2f} | {sc['search_from_none_h']:.2f} | {sc['search_from_carry_h']:.2f} |"
            )
        L += [
            "",
            "Real-time, incremental C (2-hour blocks): median relative range error (share answered).",
            "",
        ]
        L += [
            "| hours | " + " | ".join(LABEL[s] for s in RT) + " | s per estimate E / C″ |",
            "|---|" + "---|" * (len(RT) + 1),
        ]
        for g in rows:
            r = g.get("realtime")
            if not r:
                continue
            cells = [
                f"{pct(r['systems'][s]['range_rel'])} ({r['systems'][s]['answered']:.2f})"
                for s in RT
            ]
            p = r["seconds_per_evaluation"]
            L.append(
                f"| {g['hours']:g} | " + " | ".join(cells) + f" | {p['e']:.1f} / {p['c2']:.1f} |"
            )
        if name == "base":
            L += ["", "Spec 023's per-window run on the same engagements, for comparison:", ""]
            L += [
                "| hours | " + " | ".join(LABEL[s] for s in RT) + " | s per estimate E / C″ |",
                "|---|" + "---|" * (len(RT) + 1),
            ]
            for g in rows:
                r = g.get("realtime_per_window")
                if not r:
                    continue
                cells = [
                    f"{pct(r['systems'][s]['range_rel'])} ({r['systems'][s]['answered']:.2f})"
                    for s in RT
                ]
                p = r["seconds_per_evaluation"]
                L.append(
                    f"| {g['hours']:g} | "
                    + " | ".join(cells)
                    + f" | {p['e']:.1f} / {p['c2']:.1f} |"
                )
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="experiments/20261117-long2/raw")
    ap.add_argument("--base", default="experiments/20261117-long/raw")
    ap.add_argument("--out", default="experiments/20261117-long2")
    a = ap.parse_args(argv)
    summary, _ = build(ROOT / a.raw, ROOT / a.base)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n")
    (out / "tables.md").write_text(tables(summary))
    print((out / "tables.md").read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
