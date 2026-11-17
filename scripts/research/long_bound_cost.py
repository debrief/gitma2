"""Spec 023: the cost of the whole-engagement Cramér–Rao bound (`timelate.bound.period_bound`).

    OMP_NUM_THREADS=1 uv run python scripts/research/long_bound_cost.py <hours>

Prints one JSON line: rows, manoeuvres, seconds and peak memory for the bound over an engagement
of <hours> (configs/long/long.json's simulator, seed 348, index 0). Collected for 2 to 48 hours
in experiments/20261117-long/bound-cost.jsonl (machine: the session container, one core).
"""

from __future__ import annotations

import json
import resource
import sys
import time
from pathlib import Path

from tma2.long.sim import generate
from tma2.long.timelate import period_of
from tma2.timelate.bound import period_bound

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cfg = json.loads((ROOT / "configs/long/long.json").read_text())
    ranges = json.loads((ROOT / cfg["target_ranges"]).read_text())
    hours = float(sys.argv[1])
    e = generate(int(cfg["seed"]), 0, hours, cfg, ranges)
    p = period_of(e, 0, e.samples, 0)
    t = time.time()
    period_bound(p)
    print(
        json.dumps(
            {
                "hours": hours,
                "rows": e.samples,
                "manoeuvres": len(p.meta["manoeuvres"]),
                "seconds": time.time() - t,
                "max_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
