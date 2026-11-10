"""One training segment as the GPU function runs it (spec 012 research R4), kept free of any
provider's API so it can be exercised on CPU: ``scripts/modal_train.py`` is a thin wrapper.

A plan is ``{"config": {...RegressorConfig...}, "segments": n, "segment_limit_seconds": s}``.
The work directory persists between segments (a Modal volume); a segment resumes from it when
it holds a checkpoint. ``gpu_seconds`` in the run record is the wall time of every segment's
whole call (start-up, compilation and saving included), which is what is billed and what the
ledger counts.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from .model import RegressorConfig
from .train import train


def run_segment(
    plan: dict[str, Any], workdir: Path, device: str, git_commit: str | None = None
) -> dict[str, Any]:
    t0 = time.time()
    cfg = RegressorConfig(**plan["config"])
    limit = int(plan["segment_limit_seconds"])
    resume = None
    prev = 0.0
    if (workdir / "state.pt").exists():
        # train() reads the previous record from the resume directory and writes the new one to
        # the output directory: keep them apart, then replace.
        resume = workdir.with_name(workdir.name + ".prev")
        if resume.exists():
            shutil.rmtree(resume)
        shutil.copytree(workdir, resume)
        prev = float(json.loads((resume / "run.json").read_text()).get("gpu_seconds", 0.0))
    rec = train(cfg, workdir, device, resume, limit, git_commit)
    if resume is not None:
        shutil.rmtree(resume)
    rec["gpu_seconds"] = prev + (time.time() - t0)
    rec["plan"] = {k: v for k, v in plan.items() if k != "config"}
    (workdir / "run.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    return rec


def plan_limit_seconds(plan: dict[str, Any]) -> int:
    """The most GPU time a plan may use: every segment's limit plus its allowance for start-up
    and saving (the function's hard timeout)."""
    return int(plan["segments"]) * (int(plan["segment_limit_seconds"]) + STARTUP_SECONDS)


STARTUP_SECONDS = 600
