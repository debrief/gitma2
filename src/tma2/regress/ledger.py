"""The GPU ledger (spec 012 FR-010, research R5), in dollars: the sum over every run record on
the ``results/gputrain-*`` branches of ``gpu_seconds`` × the rate of the plan's GPU type. A run
is refused when its plan's limit would take the total past the cap.

Rates are Modal's listed GPU prices per hour (2026-11-11) plus the $0.09 an hour of CPU and
memory measured on the T4 runs ($25.81 for 38.06 hours).

    python -m tma2.regress.ledger --cap-usd 45 --plan configs/regress/<plan>.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .remote import plan_limit_seconds

PREFIX = "refs/heads/results/gputrain-"
OVERHEAD = 0.09
USD_PER_HOUR = {"T4": 0.59, "L4": 0.80, "A10": 1.10, "L40S": 1.95, "A100-40GB": 2.10}


def rate(gpu: str) -> float:
    return USD_PER_HOUR[gpu] + OVERHEAD


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def used_usd(remote: str = "origin") -> dict[str, float]:
    """{branch: dollars} from each results branch's run.json files."""
    out: dict[str, float] = {}
    for line in _git("ls-remote", remote, PREFIX + "*").splitlines():
        ref = line.split()[1]
        _git("fetch", "-q", remote, ref)
        total = 0.0
        for path in _git("ls-tree", "-r", "--name-only", "FETCH_HEAD").splitlines():
            if path.startswith("experiments/gputrain-runs/") and path.endswith("/run.json"):
                rec = json.loads(_git("show", f"FETCH_HEAD:{path}"))
                gpu = (rec.get("plan") or {}).get("gpu", "T4")
                total += float(rec.get("gpu_seconds", 0.0)) / 3600.0 * rate(gpu)
        out[ref.removeprefix("refs/heads/")] = total
    return out


def check(used: float, plan_limit: float, cap: float) -> bool:
    return used + plan_limit <= cap


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2.regress.ledger", description=__doc__)
    ap.add_argument("--cap-usd", type=float, required=True)
    ap.add_argument("--plan", required=True)
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    by = used_usd()
    used = sum(by.values())
    limit = plan_limit_seconds(plan) / 3600.0 * rate(plan.get("gpu", "T4"))
    cap = a.cap_usd
    for name, s in sorted(by.items()):
        print(f"${s:7.2f}  {name}")
    print(f"used ${used:.2f}; this plan may use ${limit:.2f}; cap ${cap:.2f}")
    if not check(used, limit, cap):
        print("refused: the plan's limit would take the total past the cap", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
