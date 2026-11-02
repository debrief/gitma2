"""Gate 1 panel diagnostics on the scored test predictions (spec 003, panel round 1): the gross
check's discordant rows with an exact sign test, and how far the carried model's gate-row errors
are from the physics layer with trivial inputs (the "oracle" row on constant-velocity data).

    uv run python scripts/g1_extras.py --test <test> --model p --lsq p --oracle p --out f.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from tma2.cli.g1 import load_truths
from tma2.eval.g1 import errors_at, gate_rows, gate_timestamps, load_gate_rows


def sign_test_one_sided(k: int, n: int) -> float:
    """P(X <= k) for X ~ Binomial(n, 1/2): the chance of k or fewer 'model worse' rows."""
    return float(sum(math.comb(n, i) for i in range(k + 1)) / 2**n) if n else 1.0


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("test", "model", "lsq", "oracle", "out"):
        ap.add_argument(f"--{name}", required=True)
    ap.add_argument("--extract", nargs="*", default=[], help="name=path: gate rows to keep")
    ap.add_argument("--extract-dir", help="write each --extract file's gate rows here (gzip)")
    a = ap.parse_args()
    truths, _, _ = load_truths(a.test)
    by = {t.index: t for t in truths}
    wanted = gate_timestamps(truths)
    p = {n: load_gate_rows(getattr(a, n), wanted) for n in ("model", "lsq", "oracle")}
    out: dict[str, object] = {}
    rows = gate_rows(truths, "range_rel")
    _, gm = errors_at(by, rows, p["model"], "range_rel")
    _, gl = errors_at(by, rows, p["lsq"], "range_rel")
    _, go = errors_at(by, rows, p["oracle"], "range_rel")
    better = int(((gm == 0) & (gl == 1)).sum())
    worse = int(((gm == 1) & (gl == 0)).sum())

    def kinds(name: str) -> dict[str, int]:
        """Gross rows split by cause: no converged row (missing or flagged) vs range error > 50%."""
        nc = big = 0
        for g in rows:
            r = p[name].get(g.index, {}).get(g.timestamp_s)
            if r is None or not r["converged"]:
                nc += 1
            else:
                e, _ = errors_at(by, [g], {g.index: {g.timestamp_s: r}}, "range_rel")
                big += int(e[0] > 0.5)
        return {"not_converged": nc, "range_error_over_50pct": big}

    out["gross_by_cause"] = {n: kinds(n) for n in ("model", "lsq", "oracle")}
    out["gross"] = {
        "rows": len(rows),
        "model_gross": int(gm.sum()),
        "least_squares_gross": int(gl.sum()),
        "oracle_gross": int(go.sum()),
        "model_only": worse,
        "least_squares_only": better,
        "exact_sign_test_one_sided_p": sign_test_one_sided(worse, better + worse),
        "model_vs_oracle_discordant": int((gm != go).sum()),
    }
    diffs: dict[str, object] = {}
    for metric in ("range_rel", "course_deg", "speed_kt"):
        r = gate_rows(truths, metric)
        em, _ = errors_at(by, r, p["model"], metric)
        eo, _ = errors_at(by, r, p["oracle"], metric)
        both = np.isfinite(em) & np.isfinite(eo)
        d = np.abs(em[both] - eo[both])
        diffs[metric] = {
            "rows": len(r),
            "finite_in_both": int(both.sum()),
            "median_abs_diff": float(np.median(d)) if d.size else None,
            "p99_abs_diff": float(np.quantile(d, 0.99)) if d.size else None,
            "max_abs_diff": float(d.max()) if d.size else None,
            "rows_differing_over_1e-6": int((d > 1e-6).sum()),
            "finite_mismatch": int((np.isfinite(em) != np.isfinite(eo)).sum()),
        }
    out["model_minus_oracle"] = diffs
    if a.extract_dir:
        # The gate rows of every prediction file, kept in the repository: the full files are CI
        # artefacts with a 90-day retention (reproducibility review, round 1).
        import gzip

        Path(a.extract_dir).mkdir(parents=True, exist_ok=True)
        for item in a.extract:
            name, path = item.split("=", 1)
            rows_ = load_gate_rows(path, wanted)
            with gzip.open(Path(a.extract_dir) / f"{name}-gate-rows.ndjson.gz", "wt") as f:
                for idx in sorted(rows_):
                    for ts in sorted(rows_[idx]):
                        f.write(json.dumps({"scenario_index": idx, **rows_[idx][ts]}) + "\n")
    Path(a.out).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
