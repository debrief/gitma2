"""Spec 037: write a scoring plan (validation or test) from the bound protocol and the
fine-tuned checkpoints found on the results branches.

    uv run python scripts/research/rmis_plan.py validation --out configs/headroom/rm-val-370.json
    uv run python scripts/research/rmis_plan.py test --interval-fit <file> --prior-weight W \
        --prior-static M,SD --out configs/headroom/rm-test-371.json

The unchanged regressors are spec 012's; the fine-tuned ones are the newest
``results/gputrain-ft-sK-<run id>`` branches, each with its checkpoint's digest from run.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def git(*a: str) -> str:
    return subprocess.run(["git", *a], check=True, capture_output=True, text=True, cwd=ROOT).stdout


def checkpoint(name: str, prefix: str) -> dict[str, str]:
    refs = [
        ln.split()[1]
        for ln in git("ls-remote", "origin", f"refs/heads/results/gputrain-{prefix}-*").splitlines()
    ]
    if not refs:
        raise SystemExit(f"no results branch for {prefix}")
    ref = sorted(refs, key=lambda r: int(r.rsplit("-", 1)[1]))[-1]
    branch = ref.removeprefix("refs/heads/")
    d = "experiments/gputrain-runs/" + branch.removeprefix("results/gputrain-")
    git("fetch", "-q", "origin", ref)
    rec = json.loads(git("show", f"FETCH_HEAD:{d}/run.json"))
    return {"name": name, "branch": branch, "dir": d, "sha256": rec["checkpoint_sha256"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("validation", "test"))
    ap.add_argument("--interval-fit")
    ap.add_argument("--prior-weight", type=float, default=1.0)
    ap.add_argument("--prior-static")
    ap.add_argument("--shard-size", type=int, default=50)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    proto = json.loads((ROOT / "configs/rmis/protocol.json").read_text())
    st = proto[a.stage]
    decided = (
        st["conditions"] if a.stage == "validation" else list(st["decided_conditions"].values())
    )
    conds = decided + (st.get("reported_conditions", []) if a.stage == "test" else [])
    hyb_conds = ["off", "all-central"]
    runs: list[dict[str, Any]] = list(proto["systems"]["classical"])
    hyb: list[str] = []
    if a.stage == "validation":
        # the weight is chosen on validation, on training seed 1 only (addendum 1)
        for w in (0.125, 0.25, 0.5, 1.0):
            hyb.append(f"hyb-s1-w{w:g}")
            runs.append(
                {
                    "kind": "hybrid",
                    "segmentation": "c2",
                    "name": hyb[-1],
                    "prior_from": "ft-s1",
                    "prior_weight": w,
                    "conditions": hyb_conds,
                }
            )
    else:
        for k in (1, 2, 3):
            hyb.append(f"hyb-s{k}")
            runs.append(
                {
                    "kind": "hybrid",
                    "segmentation": "c2",
                    "name": hyb[-1],
                    "prior_from": f"ft-s{k}",
                    "prior_weight": a.prior_weight,
                    "conditions": hyb_conds,
                }
            )
    if a.prior_static:
        runs.append(
            {
                "kind": "hybrid",
                "segmentation": "c2",
                "name": "c2-prior",
                "prior_static": a.prior_static,
                "prior_weight": 1.0,
                "conditions": hyb_conds,
            }
        )
    cks = [checkpoint(f"ft-s{k}", f"ft-s{k}") for k in (1, 2, 3)]
    cks += [checkpoint(f"reg-s{k}", f"r-a-s{k}") for k in (1, 2, 3)]
    n = int(st["ordinals"])
    plan: dict[str, Any] = {
        "description": f"Spec 037 {a.stage} scoring, written by scripts/research/rmis_plan.py from "
        "configs/rmis/protocol.json (bound by experiments/20261123-rmis-decision): seed "
        f"{proto['seeds'][a.stage]}, the first {n} sigma = 1 deg engagements per condition.",
        "stage": a.stage,
        "plan": "configs/gateh/gh-a.json",
        "conditions_file": "configs/rmis/all-conditions.json",
        "split": "tuning",
        "seed": proto["seeds"][a.stage],
        "count": proto["data"]["count"],
        "data_split": proto["data"]["data_split"],
        "start": 0,
        "ordinals": n,
        "shards": -(-n // a.shard_size),
        "shard_size": a.shard_size,
        "conditions": conds,
        "runs": runs,
        "imm": proto["systems"]["imm"],
        "ekf": proto["systems"]["ekf"],
        "checkpoints": cks,
        "read_controls": [
            "c2-robust",
            "c2",
            "robust-true",
            "reg-s1",
            "reg-s2",
            "reg-s3",
            "imm",
            "one_leg",
        ],
        "read_extra": [
            {
                "systems": ["hyb-s1", "hyb-s2", "hyb-s3", "c2-prior"],
                "controls": ["c2-robust", "c2", "ft-s1", "ft-s2", "ft-s3", "robust-true"],
                "out": "reading-hybrid.json",
            }
        ],
        "interval_scale": a.interval_fit or "1,1,1",
    }
    if a.interval_fit:
        plan["interval_fit"] = a.interval_fit
    Path(a.out).write_text(json.dumps(plan, indent=2) + "\n")
    print(f"wrote {a.out}: {len(conds)} conditions, {plan['shards']} shards, {len(runs)} runs")


if __name__ == "__main__":
    main()
