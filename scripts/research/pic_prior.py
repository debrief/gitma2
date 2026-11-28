"""Spec 039: tabulate the generator's distribution of ln range at the scored rows.

    uv run python scripts/research/pic_prior.py --seed 321 --count 40000 \
        --ranges configs/man2-ranges.json --out configs/pic/prior-man2.json

Generates the split in a temporary folder (a spent seed only; never a test seed), reads the true
range at each engagement's scored rows (bearing sd 1 degree, as the scorer selects) and writes a
histogram density per unit ln range with the ranges file's speed support.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--count", type=int, default=40000)
    ap.add_argument("--ranges", default="configs/man2-ranges.json")
    ap.add_argument("--bins", type=int, default=40)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from tma2.segment.score import g5_rows, iter_selected

    xs: list[float] = []
    n = 0
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, "-m", "tma2.cli.generate", "--seed", str(a.seed), "--count",
             str(a.count), "--ranges", a.ranges, "--heldout-ranges", "configs/man2-heldout.json",
             "--format", "f32pack", "--out", tmp, "--allow-dirty"],
            check=True, cwd=ROOT, capture_output=True,
        )  # fmt: skip
        for _j, m, own, tgt, _obs in iter_selected(f"{tmp}/train.f32pack", 0, 1 << 30):
            n += 1
            for k in g5_rows(m, int(m["samples"])):
                xs.append(float(np.hypot(tgt[k, 1] - own[k, 1], tgt[k, 2] - own[k, 2])))
    x = np.log(np.asarray(xs))
    edges = np.linspace(np.floor(x.min() * 10) / 10, np.ceil(x.max() * 10) / 10, a.bins + 1)
    dens, _ = np.histogram(x, bins=edges, density=True)
    ranges = json.loads((ROOT / a.ranges).read_text())
    sp = ranges["target_speed_mps"]
    out = {
        "description": "Spec 039: the generator's distribution of ln range (m) at scored rows "
        f"(5, 10, 15, 20 min after the zig), seed {a.seed}, {n} engagements, {x.size} rows; "
        "written by scripts/research/pic_prior.py.",
        "seed": a.seed,
        "ranges": a.ranges,
        "ranges_sha256": hashlib.sha256((ROOT / a.ranges).read_bytes()).hexdigest(),
        "engagements": n,
        "rows": int(x.size),
        "quantiles_m": [float(np.exp(q)) for q in np.quantile(x, [0.05, 0.25, 0.5, 0.75, 0.95])],
        "ln_range_edges": [round(float(e), 6) for e in edges],
        "density": [round(float(v), 6) for v in dens],
        "speed_mps": [sp["min"], sp["max"]],
    }
    (ROOT / a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(a.out, n, "engagements", out["quantiles_m"])


if __name__ == "__main__":
    main()
