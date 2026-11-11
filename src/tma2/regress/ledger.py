"""The GPU-time ledger (spec 012 FR-010, research R5): the sum of ``gpu_seconds`` over every run
record on the ``results/gputrain-*`` branches. A run is refused when its plan's limit would take
the total past the cap.

    python -m tma2.regress.ledger --cap-hours 50 --plan configs/regress/<plan>.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .remote import plan_limit_seconds

PREFIX = "refs/heads/results/gputrain-"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def used_seconds(remote: str = "origin") -> dict[str, float]:
    """{branch: gpu_seconds} from each results branch's run.json files."""
    out: dict[str, float] = {}
    for line in _git("ls-remote", remote, PREFIX + "*").splitlines():
        ref = line.split()[1]
        _git("fetch", "-q", remote, ref)
        total = 0.0
        for path in _git("ls-tree", "-r", "--name-only", "FETCH_HEAD").splitlines():
            if path.startswith("experiments/gputrain-runs/") and path.endswith("/run.json"):
                rec = json.loads(_git("show", f"FETCH_HEAD:{path}"))
                total += float(rec.get("gpu_seconds", 0.0))
        out[ref.removeprefix("refs/heads/")] = total
    return out


def check(used: float, plan_limit: float, cap: float) -> bool:
    return used + plan_limit <= cap


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2.regress.ledger", description=__doc__)
    ap.add_argument("--cap-hours", type=float, required=True)
    ap.add_argument("--plan", required=True)
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    by = used_seconds()
    used = sum(by.values())
    limit = plan_limit_seconds(plan)
    cap = a.cap_hours * 3600.0
    for name, s in sorted(by.items()):
        print(f"{s / 3600:8.2f} h  {name}")
    print(f"used {used / 3600:.2f} h; this plan may use {limit / 3600:.2f} h; cap {a.cap_hours} h")
    if not check(used, limit, cap):
        print("refused: the plan's limit would take the total past the cap", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
