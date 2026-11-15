"""Summarise the Node port comparison (spec 021): port_node.mjs's per-process reports.

    python3 conformance/onnx/port_summary.py <out.json> <port-0.json> ...

Fails (exit 1) unless at least 95% of scored rows have the same segmentation as Python, for C
and for E together (SC-001), and every scenario's nominations are identical. Writes the summary
JSON and prints it.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    out, paths = sys.argv[1], sys.argv[2:]
    recs = [r for p in paths for r in json.load(open(p))]
    rows = same = 0
    differ: list[dict[str, object]] = []
    noms_differ = []
    stage_ms: dict[str, list[float]] = {}
    for r in recs:
        st = r["stages"]
        if not (st["nominations"]["same"] and st["search"]["by_prefix_same"]):
            noms_differ.append(r["ordinal"])
        for k in ("c", "e"):
            c = st[k]
            rows += c["rows"]
            same += c["rows_same"]
            if c["first_decision_differs"] >= 0 or c["rows_same"] < c["rows"]:
                differ.append({"ordinal": r["ordinal"], "segmenter": k, **c})
        for name, v in st.items():
            if isinstance(v, dict) and "ms" in v:
                stage_ms.setdefault(name, []).append(v["ms"])
    summary = {
        "scenarios": len(recs),
        "rows": rows,
        "rows_same": same,
        "share_same": same / rows if rows else 0.0,
        "nominations_differ": noms_differ,
        "differ": differ,
        "max_ls_rel": max(r["stages"]["ls"]["max_rel"] for r in recs),
        "max_evidence_rel": max(r["stages"]["evidence"]["worst"] for r in recs),
        "max_drop_abs_diff": max(
            r["stages"][k]["max_drop_abs_diff_before"] for r in recs for k in ("c", "e")
        ),
        "ownship_rows_differ": sum(r["stages"]["ownship"]["differs"] for r in recs),
        "max_stage_seconds": {k: max(v) / 1000 for k, v in stage_ms.items()},
    }
    with open(out, "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))
    ok = rows > 0 and same >= 0.95 * rows and not noms_differ
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
