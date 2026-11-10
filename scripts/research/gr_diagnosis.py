"""Spec 011 FR-001/FR-002: how the frozen C fails under each mismatch condition.

Reads the segmentation files of a `diagnose.yml` run (one directory per condition, each with
`<variant>.ndjson.gz`) and the clean split of the same seed (manoeuvre times do not depend on
the mismatch overlay), and counts per scored prefix: transitions declared, true target changes
begun by the prefix, matched pairs (`segment.metrics.match_transitions`), false transitions
(declared, unmatched) and misses (true, unmatched; split by whether the change began within
the last 5 min of the prefix). Detection delay is not measured: the files hold scored prefixes
only.

    uv run python scripts/research/gr_diagnosis.py --truth <train.f32pack> --runs <dir> \
        --ordinals 150 --out <json>
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

from tma2.segment import metrics as mx
from tma2.segment.score import iter_selected
from tma2.segment.truth import change_rows

RECENT_ROWS = 30  # 5 min at 10 s


def transitions(rec: dict[str, Any]) -> list[tuple[int, int]]:
    return [
        (int(i["start_index"]), int(i["end_index"]))
        for i in rec["intervals"]
        if i["kind"] == "transition"
    ]


def count_file(path: Path, metas: dict[int, dict[str, Any]]) -> dict[str, float]:
    c = dict.fromkeys(("rows", "declared", "true", "matched", "false", "missed", "missed_old"), 0)
    held = held_false = 0
    with gzip.open(path, "rt") as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("record") != "segmentation" or rec.get("vessel") != "target":
                continue
            k = int(rec["prefix_row"])
            pred = transitions(rec)
            truth = [(a, min(b, k)) for a, b in change_rows(metas[int(rec["ordinal"])], "target")]
            truth = [s for s in truth if s[0] <= k]
            m = mx.match_transitions(pred, truth)
            hit = sum(j is not None for j in m)
            c["rows"] += 1
            c["declared"] += len(pred)
            c["true"] += len(truth)
            c["matched"] += hit
            c["false"] += len(pred) - hit
            c["missed"] += len(truth) - hit
            c["missed_old"] += sum(
                j is None and k - s[0] >= RECENT_ROWS for j, s in zip(m, truth, strict=True)
            )
            if not truth:
                held += 1
                held_false += bool(pred)
    out: dict[str, float] = dict(c)
    n = max(c["rows"], 1)
    out["false_per_row"] = c["false"] / n
    out["missed_per_row"] = c["missed"] / n
    out["miss_rate"] = c["missed"] / max(c["true"], 1)
    out["miss_rate_old"] = c["missed_old"] / max(c["true"], 1)
    out["held_rows"] = held
    out["held_rows_with_transition"] = held_false
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--runs", required=True, help="directory with one folder per condition")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--ordinals", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    metas = {j: meta for j, meta, *_ in iter_selected(a.truth, a.start, a.ordinals)}
    res: dict[str, dict[str, dict[str, float]]] = {}
    for d in sorted(p for p in Path(a.runs).iterdir() if p.is_dir()):
        res[d.name] = {
            f.name.removesuffix(".ndjson.gz"): count_file(f, metas)
            for f in sorted(d.glob("*.ndjson.gz"))
        }
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    hdr = f"{'condition':14} {'variant':11} rows decl true match false miss  miss(>5min)"
    print(hdr)
    for cond, vs in res.items():
        for v, r in vs.items():
            print(
                f"{cond:14} {v:11} {r['rows']:4.0f} {r['declared']:4.0f} {r['true']:4.0f} "
                f"{r['matched']:5.0f} {r['false']:5.0f} {r['missed']:4.0f}  {r['missed_old']:4.0f}"
            )


if __name__ == "__main__":
    main()
