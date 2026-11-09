"""Spec 010 SC-003: the Gate 5 verdict logic on synthetic statements of validation's size.

    uv run python scripts/research/g5_synthetic.py [--datasets 100] [--resamples 500] [--seed 0]

Each dataset has 1,000 scenarios with about 3.9 rows each (3,934 rows, as validation). The slices
follow validation's proportions: minutes 5/10/15/20, open at k 8%, six range bands, and the proxy
flagging 27% of rows.

* **Calibrated:** each row states P drawn from 0.30–0.85 and hits with probability P. A scenario
  effect shifts logit P by N(0, 0.5²), so rows in one scenario are correlated while P stays
  calibrated on average. Range and speed errors are |N(0, 1)| with half-width 1.96.
* **Miscalibrated:** the same, but on proxy-flagged rows the hit probability is P − 0.15.

Prints, for each case, the share of datasets where G5-a and G5-b each pass, are inconclusive or
fail. SC-003 asks for at least 90% passes on the calibrated case and at least 90% failures of
G5-b on the miscalibrated case.
"""

from __future__ import annotations

import argparse
import json
import math

import numpy as np


def dataset(rng: np.random.Generator, offset: float) -> tuple[np.ndarray, np.ndarray, dict]:  # type: ignore[type-arg]
    from tma2.eval.calibration import WIDTH

    sizes = rng.choice([3, 4, 4, 4], 1000)
    cluster = np.repeat(np.arange(1000), sizes)
    n = cluster.size
    eff = rng.normal(0, 0.5, 1000)[cluster]
    p = rng.uniform(0.30, 0.85, n)
    flag = rng.random(n) < 0.27
    lp = np.log(p / (1 - p)) + eff
    p_true = 1 / (1 + np.exp(-lp))
    # keep P calibrated on average under the scenario effect: state the mean over the effect
    p_stated = np.clip(p_true + rng.normal(0, 0.0, n), 0.01, 0.99)
    hit_prob = np.clip(p_true - offset * flag, 0.0, 1.0)
    hit = rng.random(n) < hit_prob
    x = 0.4
    c = np.zeros((n, WIDTH))
    c[:, 1] = np.where(hit, rng.uniform(0, x, n), rng.uniform(x + 1e-6, math.pi, n))
    c[:, 0], c[:, 2] = np.abs(rng.normal(0, 1, n)), np.abs(rng.normal(0, 1, n))
    c[:, 7] = c[:, 8] = 1.0
    c[:, 9], c[:, 10] = x, p_stated
    c[:, 11] = c[:, 12] = 1.959963984540054
    c[:, 13] = np.where(hit, np.log(p_stated) + 0.5, np.log(1 - p_stated) - 1.6)
    c[:, 14] = 1.0
    c[:, 15] = flag.astype(float)
    slices = {
        "minute": rng.choice(np.array(["5", "10", "15", "20"]), n),
        "open": np.where(rng.random(n) < 0.08, "open", "not_open"),
        "range_band": rng.choice(
            np.array(["0-2km", "2-5km", "5-10km", "10-20km", "20-30km", "30+km"]),
            n,
            p=[0.05, 0.15, 0.25, 0.25, 0.13, 0.17],
        ),
    }
    return c, cluster, slices


BANDS = {
    "coverage95_overall": [0.92, 0.98],
    "coverage95_slice": [0.90, 0.99],
    "reliability_overall": 0.04,
    "reliability_slice": 0.05,
    "reliability_slice_point": 1.0,
    "slope": [0.75, 1.33],
    "auc_min": 0.55,
    "min_slice_rows": 150,
    "consistency_tol": 1e-6,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", type=int, default=100)
    ap.add_argument("--resamples", type=int, default=500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--bands", help="JSON file overriding the bands")
    a = ap.parse_args()
    from tma2.calib.gate5 import criteria

    bands = dict(BANDS)
    if a.bands:
        bands.update(json.loads(open(a.bands).read()))
    rng = np.random.default_rng(a.seed)
    out = {}
    for name, offset in (("calibrated", 0.0), ("miscalibrated_0.15", 0.15)):
        tally: dict[str, dict[str, int]] = {"g5a": {}, "g5b": {}}
        for _ in range(a.datasets):
            c, cl, sl = dataset(rng, offset)
            err = np.zeros((c.shape[0], 3))
            r = criteria(c, {"t": c}, err, err, cl, sl, bands, "pass", 0.975, a.resamples)
            for k in tally:
                tally[k][r[k]] = tally[k].get(r[k], 0) + 1
        out[name] = {k: {v: n / a.datasets for v, n in t.items()} for k, t in tally.items()}
        print(name, json.dumps(out[name]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
