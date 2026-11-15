"""Spec 018: the factor that makes two stated sds of the hedged track's range cover 95% of
rows, from a tuning run's per-row errors (the setting ``adaptive_study.spread_scale``).

    uv run python scripts/research/tl6_spread_scale.py <results folder> [--hedge ada-h1] [--splits man2,shift]

Pools the determined rows of the named splits, takes the 95% quantile of
|mixture mean range − true range| ÷ mixture sd and halves it; then prints, for every split
in the folder, the coverage at one and two stated sds with that factor.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from tma2.timelate.score import UNDETERMINED


def z_scores(path: Path, hedge: str) -> np.ndarray:
    z = np.load(path)
    bound = z["bound"].astype(np.float64)
    det = np.isfinite(bound[:, 0]) & (bound[:, 0] < UNDETERMINED)
    mean = z[f"hrange_{hedge}"].astype(np.float64)
    sd = z[f"spread_{hedge}"].astype(np.float64)
    true = z["true_range"].astype(np.float64)
    ok = det & np.isfinite(mean) & np.isfinite(sd) & (sd > 0)
    out: np.ndarray = np.abs(mean - true)[ok] / sd[ok]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir")
    ap.add_argument("--hedge", default="ada-h1")
    ap.add_argument("--splits", default="man2,shift")
    a = ap.parse_args(argv)
    files = {p.name.split(".")[0]: p for p in sorted(Path(a.dir).glob("*.errors.npz"))}
    pool = np.concatenate([z_scores(files[s], a.hedge) for s in a.splits.split(",")])
    scale = float(np.quantile(pool, 0.95)) / 2.0
    print(f"scale {scale:.2f} ({pool.size} rows of {a.splits})")
    for name, p in files.items():
        z = z_scores(p, a.hedge)
        print(
            f"{name}: within 1 sd {np.mean(z <= scale):.2f}, within 2 sd {np.mean(z <= 2 * scale):.2f} ({z.size} rows)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
