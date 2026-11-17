"""Data for the long-engagement views on /viewer and /timelate (spec 023).

    uv run python scripts/research/long_viewer_data.py \\
        [--raw experiments/20261117-long/raw] [--out site/static/long-data]

Per engagement (configs/long/long.json, seed 348): the truth (target and ownship) every 2 minutes,
ownship turns and true manoeuvres; the real-time systems' estimates every 10 minutes; the
time-late systems' stitched tracks every 2 minutes, their declared manoeuvres and the window
chain. Positions to 1 m, velocities to 1 mm/s. Precomputed in Python by `tma2-long`; the
pages compute nothing.
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

from long_report import LABEL, RT, TL, build, plausible  # noqa: E402

TRUTH_STEP_S = 120.0
STITCH_STEP_S = 30.0  # the control's stored rows (score_every 6 at 5 s)


def _r(a: np.ndarray, pos: int = 0, vel: int = 3) -> list[list[float | None]]:
    out: list[list[float | None]] = []
    for row in a:
        if not np.isfinite(row).all():
            out.append(None)  # type: ignore[arg-type]
            continue
        out.append(
            [round(float(row[0]), pos), round(float(row[1]), pos)]
            + [round(float(v), vel) for v in row[2:4]]
        )
    return out


def engagement_doc(g: dict[str, Any], f: dict[str, Any]) -> dict[str, Any]:
    from tma2.timelate.score import row_errors

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
        "summary": {k: g[k] for k in ("samples", "manoeuvres", "ownship_turns", "range_km")},
    }
    rt = f.get("realtime")
    if rt:
        A = rt["_arrays"]
        doc["realtime"] = {
            "times_s": [float(t) for t in A["times"]],
            "systems": {
                s: {
                    "states": _r(plausible(A["states"][s], A["truth"])),
                    "range_err": [
                        None if not np.isfinite(v) else round(float(v), 4)
                        for v in row_errors(plausible(A["states"][s], A["truth"]), A["truth"])[:, 0]
                    ],
                    "stats": g["realtime"]["systems"][s],
                }
                for s in RT
            },
            "seconds_per_evaluation": g["realtime"]["seconds_per_evaluation"],
        }
    tl = f.get("timelate")
    if tl:
        A = tl["_arrays"]
        rows = A["rows"]
        # stitched rows sit on each window's own grid (every 30 s): every fourth, about 2 min
        keep = np.arange(0, rows.size, max(1, int(round(TRUTH_STEP_S / STITCH_STEP_S))))
        doc["timelate"] = {
            "times_s": [float(rows[i] * e.dt) for i in keep],
            "systems": {
                s: {
                    "states": _r(plausible(A["states"][s][keep], A["truth"][keep])),
                    "range_err": [
                        None if not np.isfinite(v) else round(float(v), 4)
                        for v in row_errors(
                            plausible(A["states"][s][keep], A["truth"][keep]), A["truth"][keep]
                        )[:, 0]
                    ],
                    "stats": g["timelate"]["systems"][s],
                }
                for s in TL
            },
            "declared_s": tl["_declared"],
            "windows": [
                {
                    "from_s": w["first"] * e.dt,
                    "to_s": (w["first"] + w["rows"]) * e.dt,
                    "minutes": round(w["seconds"] / 60, 1),
                }
                for w in tl["_windows"]
            ],
            "windows_missing": g["timelate"]["windows_missing"],
        }
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="experiments/20261117-long/raw")
    ap.add_argument("--out", default="site/static/long-data")
    a = ap.parse_args(argv)
    from tma2.data.provenance import read_git_provenance

    git = read_git_provenance()
    summary, full = build(ROOT / a.raw)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    index = []
    for g in summary["engagements"]:
        doc = engagement_doc(g, full[g["index"]])
        blob = gzip.compress(
            json.dumps(doc, separators=(",", ":"), allow_nan=False).encode(), 9, mtime=0
        )
        name = f"long-{g['index']}.json.gz"
        (out / name).write_bytes(blob)
        files[name] = hashlib.sha256(blob).hexdigest()
        index.append({"index": g["index"], "hours": g["hours"], "file": name})
    manifest = {
        "what": (
            "Spec 023 (issue #42): the standing systems on one simulated engagement each of 6, "
            "12, 24 and 48 hours (seed 348), computed in Python on windows of the size each "
            "system was built for. A feasibility measurement, not a result."
        ),
        "engagements": index,
        "labels": LABEL,
        "realtime_systems": list(RT),
        "timelate_systems": list(TL),
        "scaling": summary["scaling"],
        "record": "experiments/20261117-long/",
        "note": "docs/research/12-long-engagements.md",
        "files": files,
        "built": {
            "script": "scripts/research/long_viewer_data.py",
            "git_commit": git.commit,
            "git_dirty": git.dirty,
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print({n: len((out / n).read_bytes()) for n in files})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
