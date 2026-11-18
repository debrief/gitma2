"""Data for the long-engagement views on /viewer and /timelate (spec 024; replaces spec 023's).

    uv run python scripts/research/long2_viewer_data.py \\
        [--raw experiments/20261117-long2/raw] [--out site/static/long-data]

Three sets, each one engagement per duration (seed 348): spec 023's engagements, and the
realistic ones (contacts 1 and 2). Per engagement: the truth every 2 minutes; ownship turns,
true manoeuvres and (realistic sets) contact gaps; the incremental real-time systems every
10 minutes; the time-late systems (ctl, ctl-carry, C″, the true-history fit) stitched, every
2 minutes, with their declared manoeuvres and the window chain. Precomputed in Python by
`tma2-long`; the pages compute nothing.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "research"))

from long2_report import LABEL, SET_LABEL, TL, build  # noqa: E402
from long_report import RT, plausible  # noqa: E402

TRUTH_STEP_S = 120.0
STITCH_STEP_S = 30.0


def _r(a: np.ndarray) -> list[Any]:
    out: list[Any] = []
    for row in a:
        if not np.isfinite(row).all():
            out.append(None)
            continue
        out.append(
            [round(float(row[0])), round(float(row[1]))] + [round(float(v), 3) for v in row[2:4]]
        )
    return out


def _part(
    times: np.ndarray,
    states: dict[str, np.ndarray],
    truth: np.ndarray,
    systems: tuple[str, ...],
    st: dict[str, Any],
) -> dict[str, Any]:
    from tma2.timelate.score import row_errors

    out: dict[str, Any] = {"times_s": [float(t) for t in times], "systems": {}}
    for s in systems:
        p = plausible(states[s], truth)
        out["systems"][s] = {
            "states": _r(p),
            "range_err": [
                None if not np.isfinite(v) else round(float(v), 4)
                for v in row_errors(p, truth)[:, 0]
            ],
            "stats": st[s],
        }
    return out


def engagement_doc(g: dict[str, Any], f: dict[str, Any]) -> dict[str, Any]:
    e = f["e"]
    step = int(round(TRUTH_STEP_S / e.dt))
    idx = np.arange(0, e.samples, step)
    doc: dict[str, Any] = {
        "index": e.index,
        "hours": e.meta["hours"],
        "dt_truth_s": TRUTH_STEP_S,
        "truth": [
            [
                round(float(e.tgt[i, 1])),
                round(float(e.tgt[i, 2])),
                round(float(e.own[i, 1])),
                round(float(e.own[i, 2])),
            ]
            for i in idx
        ],
        "turns_s": [[a * e.dt, b * e.dt] for a, b in e.meta["ownship_turns"]],
        "true_s": [
            [(s["start_index"] - 1) * e.dt, s["end_index"] * e.dt] for s in e.meta["manoeuvres"]
        ],
        "gaps_s": (e.meta.get("realism") or {}).get("gaps_s", []),
        "summary": {
            "samples": e.samples,
            "manoeuvres": g["manoeuvres"],
            "ownship_turns": g["ownship_turns"],
            "range_km": g["range_km"],
            "valid_share": g["valid_share"],
        },
    }
    rt = f.get("realtime")
    if rt:
        A = rt["_arrays"]
        doc["realtime"] = _part(A["times"], A["states"], A["truth"], RT, g["realtime"]["systems"])
        doc["realtime"]["seconds_per_evaluation"] = g["realtime"]["seconds_per_evaluation"]
    tl = f.get("carry")
    if tl:
        A = tl["_arrays"]
        keep = np.arange(0, A["rows"].size, max(1, int(round(TRUTH_STEP_S / STITCH_STEP_S))))
        doc["timelate"] = _part(
            A["rows"][keep] * e.dt,
            {s: A["states"][s][keep] for s in TL},
            A["truth"][keep],
            TL,
            g["timelate"]["systems"],
        )
        doc["timelate"]["declared_s"] = tl["_declared"]
        doc["timelate"]["windows"] = [
            {
                "from_s": w["first"] * e.dt,
                "to_s": (w["first"] + w["rows"]) * e.dt,
                "minutes": round(w["seconds"] / 60, 1),
            }
            for w in tl["_windows"]
        ]
        doc["timelate"]["windows_missing"] = sorted(
            set(range(g["timelate"]["windows_planned"])) - {w["index"] for w in tl["_windows"]}
        )
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="experiments/20261117-long2/raw")
    ap.add_argument("--base", default="experiments/20261117-long/raw")
    ap.add_argument("--out", default="site/static/long-data")
    a = ap.parse_args(argv)
    from tma2.data.provenance import read_git_provenance

    git = read_git_provenance()
    summary, full = build(ROOT / a.raw, ROOT / a.base)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("long-*.json.gz"):
        old.unlink()
    files: dict[str, str] = {}
    sets: dict[str, Any] = {}
    for name, rows in summary["sets"].items():
        index = []
        for g in rows:
            doc = engagement_doc(g, full[name][g["index"]])
            blob = gzip.compress(
                json.dumps(doc, separators=(",", ":"), allow_nan=False).encode(), 9, mtime=0
            )
            fn = f"long-{name}-{g['index']}.json.gz"
            (out / fn).write_bytes(blob)
            files[fn] = hashlib.sha256(blob).hexdigest()
            index.append({"index": g["index"], "hours": g["hours"], "file": fn})
        sets[name] = {"label": SET_LABEL[name], "engagements": index}
    manifest = {
        "what": (
            "Specs 023 and 024 (issue #42): the standing systems on one simulated engagement each of "
            "6, 12, 24 and 48 hours (seed 348), with the incremental C, time-late windows that carry "
            "state, and a realistic set (the ownship steering on what it measures, contact gaps, "
            "range-limited detection, a second contact). A feasibility measurement, not a result."
        ),
        "sets": sets,
        "labels": LABEL,
        "realtime_systems": list(RT),
        "timelate_systems": list(TL),
        "record": "experiments/20261117-long2/",
        "note": "docs/research/13-long-engagements-2.md",
        "files": files,
        "built": {
            "script": "scripts/research/long2_viewer_data.py",
            "git_commit": git.commit,
            "git_dirty": git.dirty,
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print({n: len((out / n).read_bytes()) for n in files})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
