"""Spec 017: extract stored tracks of the first periods of a split from a results folder.

    uv run python scripts/research/tl5_tracks.py <results dir> <record dir> [--split shift] [--periods 20]

Reads ``<split>.errors.npz`` (the ``trk_*`` arrays the runner stores) and writes
``<record dir>/tracks.npz`` with ``<split>/period``, ``<split>/truth`` and the tracks of
C″, the standing search, the declared control and the true-history reference for the
lowest ``--periods`` stored ordinals. Used by ``tl5_charts.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

KEEP = ("c2", "search3", "ctl-d1-q0.01", "history-best")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results")
    ap.add_argument("record")
    ap.add_argument("--split", default="shift")
    ap.add_argument("--periods", type=int, default=20)
    a = ap.parse_args(argv)
    z = np.load(Path(a.results) / f"{a.split}.errors.npz")
    ids = np.unique(z["trk_period"])[: a.periods]
    m = np.isin(z["trk_period"], ids)
    out = {f"{a.split}/period": z["trk_period"][m], f"{a.split}/truth": z["trk_truth"][m]}
    for k in KEEP:
        out[f"{a.split}/{k}"] = z[f"trk_{k}"][m]
    np.savez_compressed(Path(a.record) / "tracks.npz", **out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
