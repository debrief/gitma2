"""The viewer's E against Gate 2's committed E predictions on the same G5 rows (spec 020).

    git fetch origin results/g2predict-g2-a-test-42406326175
    git show FETCH_HEAD:experiments/g2predict-runs/g2-a-test-42406326175/e-s3.ndjson > <file>
    uv run python scripts/research/viewer_vs_gate2.py site/static/viewer <file>

For each demo engagement, Python's onnxruntime outputs shipped with the viewer (E-w's graph on
the builder's hand-over) against the torch rows Gate 2's run wrote (its chunked segmentation
and padding): range, course and speed differences at each G5 row. Agreement shows the demo's
host-side inputs are the ones Gate 2 scored; a disagreement names the row.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    d, pred = Path(sys.argv[1]), Path(sys.argv[2])
    man = json.loads((d / "manifest.json").read_text())
    want = {e["ordinal"] for e in man["engagements"]}
    gate: dict[int, dict[float, dict[str, float]]] = {}
    with open(pred, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("record") == "prediction" and rec["ordinal"] in want:
                gate[rec["ordinal"]] = {round(r["timestamp_s"], 1): r for r in rec["rows"]}
    out = []
    for e in man["engagements"]:
        doc = json.loads(gzip.decompress((d / e["json"]).read_bytes()))
        v = np.frombuffer(gzip.decompress((d / e["binary"]).read_bytes()), dtype="<f8")
        lay = {L["name"]: L for L in doc["layout"]}
        st = lay["state"]
        for r, q in enumerate(doc["e_rows"]):
            t = round(doc["times_s"][q], 1)
            g = gate.get(e["ordinal"], {}).get(t)
            if g is None:
                continue
            x, y, vx, vy = v[st["offset"] + 4 * r : st["offset"] + 4 * r + 4]
            k = doc["rows"][q]
            ox, oy = doc["own"][k]
            rng = math.hypot(x - ox, y - oy)
            dc = (math.atan2(vx, vy) - g["course_rad"] + math.pi) % (2 * math.pi) - math.pi
            out.append(
                {
                    "engagement": e["id"],
                    "ordinal": e["ordinal"],
                    "row": k,
                    "range_rel": abs(rng - g["range_m"]) / g["range_m"] if g["range_m"] else None,
                    "course_rad": abs(dc),
                    "speed_mps": abs(math.hypot(vx, vy) - g["speed_mps"]),
                }
            )
    rel = [o["range_rel"] for o in out if o["range_rel"] is not None]
    print(
        json.dumps(
            {
                "rows": len(out),
                "max_range_rel": max(rel) if rel else None,
                "max_course_rad": max(o["course_rad"] for o in out) if out else None,
                "max_speed_mps": max(o["speed_mps"] for o in out) if out else None,
                "per_row": out,
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
