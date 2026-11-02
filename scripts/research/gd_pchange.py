"""Diagnostic for the Gate D validation stop (spec 004): how far does p_change rise near a
manoeuvre? Reads a tma2-detect file and its truth split; prints the per-scenario maximum of
p_change, its maximum inside each span's detection window [start − 1, end + 30], and the share of
spans whose window reaches each level.

    uv run tma2-detect --plan <plan> --model <id> --checkpoint <dir> --truth <split> --limit 1000 --out det.ndjson
    uv run python scripts/research/gd_pchange.py --detector det.ndjson --truth <split> --limit 1000
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from tma2.data.f32pack import iter_pack_raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", required=True)
    ap.add_argument("--truth", required=True)
    ap.add_argument("--limit", type=int, default=1000)
    a = ap.parse_args()
    recs = {}
    with open(a.detector, encoding="utf-8") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            recs[int(r["scenario_index"])] = r
    near: list[float] = []
    top: list[float] = []
    exported = 0
    for i, (_, m, *_rest) in enumerate(iter_pack_raw(a.truth)):
        if i >= a.limit:
            break
        r = recs[int(m["index"])]
        p = np.asarray(r["p_change"])
        top.append(float(p.max()))
        for s in m.get("manoeuvres") or []:
            lo, hi = int(s["start_index"]) - 1, min(int(s["end_index"]) + 30, len(p) - 1)
            near.append(float(p[lo : hi + 1].max()))
        exported += sum(1 for ks in r.get("knot_sets") or [] if ks["knots"])
    q = [0.1, 0.5, 0.9, 0.99, 1.0]

    def quantiles(x: list[float]) -> dict[str, float]:
        return {str(p): float(v) for p, v in zip(q, np.quantile(x, q), strict=True)}

    out = {
        "scenarios": len(top),
        "spans": len(near),
        "max_p_change_per_scenario_quantiles": quantiles(top),
        "max_p_change_in_span_window_quantiles": quantiles(near),
        "spans_reaching": {str(h): float(np.mean(np.asarray(near) >= h)) for h in (0.1, 0.2, 0.5)},
        "knot_sets_with_an_exported_knot": exported,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
