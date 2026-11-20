"""Spec 030 panel supplement: readings the panel recomputed that the registered scorer does not
report, generated from the committed records (never hand-copied).

    uv run python scripts/research/tl10_supplement.py

Writes ``experiments/20261120-tl10/supplement.json``: per split (test seed 363) carry ÷ k4,
cprior ÷ k4 and alone ÷ k4 on later periods and on own rows, with the scored engagements; Annex B
alone ÷ k4 by seed (360, 361, 362, 363) and pooled over the four.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from tma2.timelate.study8 import UNDETERMINED, paired, period_table

TEST = Path("experiments/20261120-tl10")
SEEDS = {
    360: Path("experiments/20261119-tl10-refine/seed360"),
    361: Path("experiments/20261119-tl10-refine/seed361"),
    362: Path("experiments/20261119-tl10-val"),
    363: TEST,
}
SYSTEMS = ["alone", "joint", "carry", "cprior", "cv-k4"]


def _rows(z: dict[str, np.ndarray], own: bool) -> np.ndarray:
    span = z["bound_span"][:, 0].astype(np.float64)
    r = np.isfinite(span) & (span < UNDETERMINED) & ~z["carry_first"].astype(bool)
    if own:
        o = z["bound_own"][:, 0].astype(np.float64)
        r &= np.isfinite(o) & (o < UNDETERMINED)
    return r


def _pair(t: dict[str, Any], a: str, b: str) -> dict[str, float]:
    d = paired(t[a], t[b], t["eng"], 0)
    return {k: d[k] for k in ("value", "lo", "hi", "median", "periods", "engagements")}


def main() -> int:
    out: dict[str, Any] = {"test": {}, "annex_b_by_seed": {}}
    for split in ("man2", "shift", "man2-out", "quiet"):
        z = dict(np.load(TEST / f"{split}.errors.npz"))
        res: dict[str, Any] = {}
        for own in (False, True):
            t = period_table(z, _rows(z, own), SYSTEMS)
            key = "own_rows" if own else "later_periods"
            res[key] = {
                f"{a}/{b}": _pair(t, a, b)
                for a, b in (
                    ("alone", "cv-k4"),
                    ("carry", "cv-k4"),
                    ("cprior", "cv-k4"),
                    ("cv-k4", "joint"),
                )
            }
        out["test"][split] = res
    logs, engs = [], []
    for seed, rec in SEEDS.items():
        z = dict(np.load(rec / "man2.errors.npz"))
        t = period_table(z, _rows(z, False), SYSTEMS)
        out["annex_b_by_seed"][str(seed)] = _pair(t, "alone", "cv-k4")
        logs.append(np.log(t["alone"][:, 0] / t["cv-k4"][:, 0]))
        engs.append(t["eng"].astype(np.int64) + seed * 100000)
    lr, eg = np.concatenate(logs), np.concatenate(engs)
    ok = np.isfinite(lr)
    lr, eg = lr[ok], eg[ok]
    uniq = np.unique(eg)
    rng = np.random.default_rng(23)
    idx = {e: np.flatnonzero(eg == e) for e in uniq}
    boots = []
    for _ in range(2000):
        pick = rng.choice(uniq, uniq.size)
        boots.append(np.mean(np.concatenate([lr[idx[e]] for e in pick])))
    out["annex_b_pooled_four_seeds"] = {
        "value": float(np.exp(lr.mean())),
        "lo": float(np.exp(np.percentile(boots, 2.5))),
        "hi": float(np.exp(np.percentile(boots, 97.5))),
        "periods": int(lr.size),
        "engagements": int(uniq.size),
        "note": "seed 361 chose k4 and seed 360 checked it; not an independent estimate",
    }
    (TEST / "supplement.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
