"""Paired gap-recovered differences between any two estimators of a tma2-g2 / tma2-gs scoring run.

Gate 2 panel round 1 (`experiments/20261107-g2-veto/`): the scorer reports each estimator against
C only; the classical controls need E − C′, E − C″, and so on. Same rows, same clusters and the
same resamples as the scorer (``bootstrap_clustered_statistic``, 97.5%, 2,000 resamples), median
range error (column 0) unless ``--col`` says otherwise.

    uv run python scripts/research/g2_paired_gaps.py <errors.npz> A-B [A-B ...] [--col 0]

``A-B`` names two estimators as stored in ``errors.npz`` (``err_<name>``), for example
``e-s3-veto-w6-fade``: the split is at the first ``-`` that leaves two known names.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from tma2.cli.gs import LEVEL, RESAMPLES
from tma2.eval.bootstrap import bootstrap_clustered_statistic
from tma2.segment import score as sc


def split(pair: str, names: set[str]) -> tuple[str, str]:
    for i, ch in enumerate(pair):
        if ch == "-" and pair[:i] in names and pair[i + 1 :] in names:
            return pair[:i], pair[i + 1 :]
    raise SystemExit(f"{pair}: not two of {sorted(names)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("errors")
    ap.add_argument("pairs", nargs="+")
    ap.add_argument("--col", type=int, default=0)
    a = ap.parse_args()
    z = np.load(a.errors)
    errs = {k[4:]: z[k] for k in z.files if k.startswith("err_")}
    cluster = z["ordinal"]
    out = {}
    for pair in a.pairs:
        x, y = split(pair, set(errs))
        cols = {k: errs[k] for k in ("one_leg", "oracle", x, y)}

        def stat(cc: dict[str, np.ndarray], x: str = x, y: str = y) -> float:
            g = sc.gap_recovered_cols(cc, x, a.col)
            return g - sc.gap_recovered_cols(cc, y, a.col)

        si = bootstrap_clustered_statistic(cols, cluster, stat, LEVEL, RESAMPLES)
        out[f"{x} - {y}"] = {"value": si.value, "lo": si.lo, "hi": si.hi}
        print(f"{x} - {y}: {si.value:+.4f} [{si.lo:+.4f}, {si.hi:+.4f}]", flush=True)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
