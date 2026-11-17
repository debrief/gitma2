"""Data for the site's time-late page (spec 022), from a committed time-late test record.

    uv run python scripts/research/timelate_viewer_data.py \\
        [--record experiments/20261114-tl4] [--out site/static/timelate-data]

Reads the record's ``tracks.npz`` (tracks at every 30 s for the first 20 periods of three
splits) and ``<split>.periods.json`` (true manoeuvre spans and each system's declared ones).
Writes one gzipped JSON per split and ``manifest.json`` with the inputs' digests and the commit.
Each period carries:
* ``truth``: target x, y, course, speed and ownship x, y at each stored row;
* each system's track (x, y, vx, vy), rounded to 0.1 m and 1 mm/s;
* the true spans and each system's declared spans, in seconds from the period's start;
* each system's median errors over the stored rows (``timelate.score.row_errors``: relative range,
  course in degrees, speed in knots).

The stored rows are every row of these periods at 30 s, not the scorer's rows: the record's
figures are taken over rows whose known-history bound is below 0.5, so these medians are not
the record's. The page says so.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPLITS = {
    "man2": "Annex B targets",
    "man2-out": "2% wild bearings",
    "shift": "shifted manoeuvre prior (busier targets)",
}
SYSTEMS = {
    "ctl-d1-q0.01": "standing classical control (declared history)",
    "c2": "C″ read as a track (the old system)",
    "history-best": "fit told the true manoeuvre history (a reference, not a bound)",
    "learned-s1-arc": "learned whole-period model, arc read-out (stopped by study L)",
}
DECLARED = ("ctl-d1-q0.01", "c2", "learned-s1-arc")
STEP_S = 30.0


def build(record: Path) -> tuple[dict[str, Any], dict[str, bytes], list[Path]]:
    import numpy as np

    from tma2.timelate.score import COLS, row_errors

    z = np.load(record / "tracks.npz")
    run = json.loads((record / "run.json").read_text())
    out: dict[str, bytes] = {}
    index: dict[str, Any] = {}
    inputs = [record / "tracks.npz", record / "run.json"]
    for split, label in SPLITS.items():
        pj = record / f"{split}.periods.json"
        inputs.append(pj)
        per = {int(r["ordinal"]): r for r in json.loads(pj.read_text())}
        ids = sorted(int(i) for i in np.unique(z[f"{split}/period"]))
        periods = []
        for pid in ids:
            m = z[f"{split}/period"] == pid
            tr = z[f"{split}/truth"][m].astype(np.float64)
            rec = per[pid]
            sysd: dict[str, Any] = {}
            for s in SYSTEMS:
                st = z[f"{split}/{s}"][m].astype(np.float64)
                err = row_errors(st, tr)
                med = {c: float(np.nanmedian(err[:, j])) for j, c in enumerate(COLS)}
                sysd[s] = {
                    "track": [
                        [round(float(v), 1) for v in r[:2]] + [round(float(v), 3) for v in r[2:]]
                        for r in st
                    ],
                    "median": {k: (v if np.isfinite(v) else None) for k, v in med.items()},
                    "declared": rec["histories"].get(s, {}).get("spans") if s in DECLARED else None,
                }
            periods.append(
                {
                    "ordinal": pid,
                    "seconds": float(rec["seconds_long"]),
                    "step_s": STEP_S,
                    "truth": [
                        [
                            round(float(r[0]), 1),
                            round(float(r[1]), 1),
                            round(float(r[2]), 5),
                            round(float(r[3]), 3),
                            round(float(r[4]), 1),
                            round(float(r[5]), 1),
                        ]
                        for r in tr
                    ],  # fmt: skip
                    "true_spans": rec["true"],
                    "true_kinds": rec.get("true_kinds"),
                    "edited": rec.get("edited", 0),
                    "systems": sysd,
                }
            )
        text = json.dumps(
            {"split": split, "label": label, "periods": periods},
            separators=(",", ":"),
            allow_nan=False,
        )
        name = f"{split}.json.gz"
        out[name] = gzip.compress(text.encode(), compresslevel=9, mtime=0)
        index[split] = {"label": label, "file": name, "periods": len(periods)}
    manifest = {
        "what": (
            "Time-late periods from spec 016's test record: tracks at every 30 s for the first 20 "
            "stored periods of three splits, with true and declared manoeuvres."
        ),
        "record": str(record.relative_to(ROOT)),
        "seed": run.get("seed"),
        "splits": index,
        "systems": SYSTEMS,
        "note": (
            "Medians here are over every stored row of a period; the record's figures are over "
            "rows whose known-history bound is below 0.5, so they are not the record's numbers."
        ),
        "account": "/blog/2026/11/15/time-late-synthesis",
        "tables": "https://github.com/debrief/gitma2/blob/main/experiments/20261115-tl-synthesis/tables.md",
    }
    return manifest, out, inputs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record", default="experiments/20261114-tl4")
    ap.add_argument("--out", default="site/static/timelate-data")
    a = ap.parse_args(argv)

    from tma2.data.provenance import read_git_provenance

    g = read_git_provenance()
    manifest, files, inputs = build(ROOT / a.record)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    for name, blob in files.items():
        (out / name).write_bytes(blob)
    manifest["files"] = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
    manifest["inputs"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs
    }
    manifest["built"] = {
        "script": "scripts/research/timelate_viewer_data.py",
        "git_commit": g.commit,
        "git_dirty": g.dirty,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print({n: len(b) for n, b in files.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
