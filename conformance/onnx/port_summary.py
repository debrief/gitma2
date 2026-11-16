"""Summarise the Node port comparison (spec 021): port_node.mjs's per-process reports.

    python3 conformance/onnx/port_summary.py [--expect N] <out.json> <port-0.json> ...

Fails (exit 1) unless:
* every expected scenario is present (``--expect``: a crashed shard must not shrink the check);
* at least 95% of scored rows have the same segmentation as Python, for C and E together
  (SC-001);
* every scenario's nominations and search transitions are identical;
* every confirmation decision is identical, for C and E.

Reported, not gated (spec 021 research R3, R4): the numeric differences of the intermediates,
the GLR rows on the other side of the alarm threshold, and the scenarios whose least-squares
comparison is vacuous (no usable row). Writes the summary JSON and prints it.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    args = sys.argv[1:]
    expect = None
    if args and args[0] == "--expect":
        expect, args = int(args[1]), args[2:]
    out, paths = args[0], args[1:]
    recs = [r for p in paths for r in json.load(open(p))]
    rows = same = 0
    differ: list[dict[str, object]] = []
    noms_differ = []
    decisions_differ = []
    glr_crossings = {}
    stage_ms: dict[str, list[float]] = {}
    for r in recs:
        st = r["stages"]
        if not (st["nominations"]["same"] and st["search"]["by_prefix_same"]):
            noms_differ.append(r["ordinal"])
        for k in ("c", "e"):
            c = st[k]
            rows += c["rows"]
            same += c["rows_same"]
            if c["first_decision_differs"] >= 0 or c["decisions"] != c["py_decisions"]:
                decisions_differ.append((r["ordinal"], k))
            if c["first_decision_differs"] >= 0 or c["rows_same"] < c["rows"]:
                differ.append({"ordinal": r["ordinal"], "segmenter": k, **c})
        if st["glr"].get("crossings"):
            glr_crossings[str(r["ordinal"])] = st["glr"]["crossings"]
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
        "expected": expect,
        "decisions_differ": decisions_differ,
        "glr_threshold_crossings": glr_crossings,
        "vacuous_ls": [r["ordinal"] for r in recs if r["stages"]["ls"].get("usable_rows") == 0],
        "max_ls_rel": max(r["stages"]["ls"]["max_rel"] for r in recs),
        "max_glr_abs": max(r["stages"]["glr"].get("max_abs", 0.0) for r in recs),
        "max_evidence_abs": max(r["stages"]["evidence"].get("max_abs", 0.0) for r in recs),
        "max_cost_table_rel": max(r["stages"]["search"]["cost_max_rel"] for r in recs),
        "cost_table_finite_differs": sum(r["stages"]["search"]["finite_differs"] for r in recs),
        "min_decision_margin": min(
            r["stages"][k]["min_abs_score"] for r in recs for k in ("c", "e")
        ),
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
    ok = (
        rows > 0
        and same >= 0.95 * rows
        and not noms_differ
        and not decisions_differ
        and (expect is None or len(recs) == expect)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
