"""Spec 011 FR-002: each mismatch kind's effect on C's downstream range error, with paired,
scenario-clustered bootstrap intervals (95%, 2,000 resamples, seed 11).

For each condition against `off`, on the same rows: the change in C's median relative range
error, the change in the true-segmentation plain solve's (`oracle`), and the change in their
difference (the part that is segmentation's). Reads `errors.npz` of a `diagnose.yml` run.

    uv run python scripts/research/gr_kind_shares.py --runs <dir> --out <json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def med(x: np.ndarray) -> float:
    return float(np.median(x))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variant", default="C")
    a = ap.parse_args()
    z = {p.name: np.load(p / "errors.npz") for p in sorted(Path(a.runs).iterdir()) if p.is_dir()}
    off = z["off"]
    ords = off["ordinal"]
    uniq = np.unique(ords)
    rows_of = [np.flatnonzero(ords == u) for u in uniq]
    rng = np.random.default_rng(11)
    draws = [
        np.concatenate([rows_of[i] for i in rng.integers(0, uniq.size, uniq.size)])
        for _ in range(2000)
    ]

    def stat(c: str, idx: np.ndarray) -> tuple[float, float, float]:
        d = z[c]
        dc = med(d[f"err_{a.variant}"][idx, 0]) - med(off[f"err_{a.variant}"][idx, 0])
        do = med(d["err_oracle"][idx, 0]) - med(off["err_oracle"][idx, 0])
        return dc, do, dc - do

    res: dict[str, dict[str, list[float]]] = {}
    every = np.arange(ords.size)
    for c in z:
        if c == "off":
            continue
        assert np.array_equal(z[c]["ordinal"], ords) and np.array_equal(z[c]["k"], off["k"])
        point = stat(c, every)
        b = np.array([stat(c, i) for i in draws])
        lo, hi = np.quantile(b, [0.025, 0.975], axis=0)
        res[c] = {
            n: [point[j], float(lo[j]), float(hi[j])]
            for j, n in enumerate(("d_C", "d_true_segmentation", "d_segmentation_part"))
        }
        print(c, {n: [round(x, 3) for x in v] for n, v in res[c].items()})
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
