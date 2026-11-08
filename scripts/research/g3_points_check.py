"""Spec 008 T012: two prediction files agree on every point field.

    uv run python scripts/research/g3_points_check.py <old.ndjson> <new.ndjson> [--rtol 1e-6]

Used to show that re-made files carrying covariances (schema 0.26.0) state the same estimates as
Gate 2's. Exit 1 on any row that differs beyond ``rtol`` (relative, floor 1) or changes its
converged flag, or on a missing ordinal or row.
"""

from __future__ import annotations

import argparse
import json
import sys

POINT = ("range_m", "course_rad", "speed_mps", "x_m", "y_m")


def load(path: str) -> dict[int, dict[float, dict[str, object]]]:
    out = {}
    with open(path, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            rec = json.loads(line)
            out[int(rec["ordinal"])] = {float(r["timestamp_s"]): r for r in rec["rows"]}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--rtol", type=float, default=1e-6)
    a = ap.parse_args()
    old, new = load(a.old), load(a.new)
    bad, worst, n = [], 0.0, 0
    if set(old) != set(new):
        bad.append(f"ordinals differ: {sorted(set(old) ^ set(new))[:5]}")
    for j in sorted(set(old) & set(new)):
        for t, ro in old[j].items():
            rn = new[j].get(t)
            if rn is None:
                bad.append(f"{j} {t}: row missing")
                continue
            n += 1
            if ro["converged"] != rn["converged"]:
                bad.append(f"{j} {t}: converged {ro['converged']} -> {rn['converged']}")
            for k in POINT:
                d = abs(float(ro[k]) - float(rn[k])) / max(abs(float(ro[k])), 1.0)  # type: ignore[arg-type]
                worst = max(worst, d)
                if d > a.rtol:
                    bad.append(f"{j} {t} {k}: {ro[k]} -> {rn[k]}")
    print(json.dumps({"rows": n, "max_rel_diff": worst, "failures": len(bad)}))
    for b in bad[:20]:
        print(b, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
