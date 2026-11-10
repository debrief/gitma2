"""Spec 010, Gate H panel round 1: the gate's statistic by quartile of true range.

    uv run python scripts/research/gh_range_bands.py --errors <errors.npz> --out <range-bands.json>

``errors.npz`` is the primary condition's scoring array from the test run (results branch
``results/headroom-gh-test-all-central-plan-42799040276``). Post hoc, not gated. For each quartile
of true range: rows, medians of the plain solve, the robust control and the attainable ceiling,
R (control over ceiling) and the plain solve over the ceiling, with the gate's intervals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--errors", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    import numpy as np

    from tma2.headroom import gate
    from tma2.segment.score import lower_median

    z = np.load(a.errors)
    errs = {k[4:]: z[k] for k in z.files if k.startswith("err_")}
    cluster, rng = z["ordinal"], z["true_range_m"]
    q = np.quantile(rng, [0.25, 0.5, 0.75])
    edges = [0.0, *[float(x) for x in q], float("inf")]
    bands = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        m = (rng >= lo) & (rng < hi)
        r = gate.comparison(errs, cluster, "robust@truth", "attainable@truth", m, 2000, 0.975)
        n = gate.comparison(errs, cluster, "nominal@truth", "attainable@truth", m, 2000, 0.975)
        bands.append(
            {
                "range_lo_m": lo,
                "range_hi_m": hi if np.isfinite(hi) else None,
                "rows": int(m.sum()),
                "median_plain": lower_median(errs["nominal@truth"][m, 0]),
                "median_robust": lower_median(errs["robust@truth"][m, 0]),
                "median_ceiling": lower_median(errs["attainable@truth"][m, 0]),
                "R": r["range"],
                "plain_over_ceiling": n["range"],
            }
        )
    out = {
        "record": "gate_h_range_bands",
        "errors_sha256": hashlib.sha256(Path(a.errors).read_bytes()).hexdigest(),
        "level": 0.975,
        "resamples": 2000,
        "bands": bands,
    }
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
