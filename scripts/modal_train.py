# mypy: ignore-errors
"""The regressor control on a Modal GPU (spec 012 research R4).

    modal run scripts/modal_train.py --plan configs/regress/<plan>.json --out <dir> --commit <sha>

One call runs one segment: a T4 container trains until the plan's segment limit (the function's
hard timeout is that limit plus a start-up allowance), resuming from the run's folder on the
volume ``gitma2-regress`` when it holds a checkpoint. The record and the checkpoint come back as
the function's result and are written to ``--out`` by the caller (the Actions job), which is the
only place that talks to GitHub. Written against Modal's documentation as of 2026-11-10
(``gpu="T4"``, ``timeout`` up to 24 h, volumes committed in the background and on exit); not yet
run with credentials.
"""

from __future__ import annotations

import json
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
STARTUP_SECONDS = 600  # as tma2.regress.remote
MAX_SEGMENT_SECONDS = 5 * 3600  # the Actions job that waits has a 6 h limit

image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("torch==2.15.0", "numpy", "numba", "safetensors", "pydantic>=2")
    .add_local_python_source("tma2")
    .add_local_dir(str(ROOT / "configs"), remote_path="/root/configs")
)
app = modal.App("gitma2-regress", image=image)
volume = modal.Volume.from_name("gitma2-regress", create_if_missing=True)


def _segment(plan_json: str, run_name: str, commit: str) -> tuple[str, bytes]:
    import os

    import torch

    from tma2.regress.remote import run_segment

    plan = json.loads(plan_json)
    if int(plan["segment_limit_seconds"]) > MAX_SEGMENT_SECONDS:
        raise ValueError("segment_limit_seconds is above the function's limit")
    if not torch.cuda.is_available():
        raise RuntimeError("no GPU in the container")
    os.chdir("/root")  # the plan's ranges path is relative to the repository root
    work = Path("/vol") / run_name
    rec = run_segment(plan, work, "cuda", commit)
    volume.commit()
    return json.dumps(rec), (work / "checkpoint.safetensors").read_bytes()


# One function per GPU type, each defined at module scope with the decorator: the form the
# runs of spec 012 used. (Addendum 1's form, functions built in a loop with serialized=True,
# was never run before 2026-11-13, when its containers failed at start-up: "the
# 'modal_train' module is not available in the remote environment".)
_OPTS = {"timeout": MAX_SEGMENT_SECONDS + STARTUP_SECONDS, "volumes": {"/vol": volume}}


@app.function(gpu="T4", **_OPTS)
def segment_t4(plan_json: str, run_name: str, commit: str) -> tuple[str, bytes]:
    return _segment(plan_json, run_name, commit)


@app.function(gpu="L4", **_OPTS)
def segment_l4(plan_json: str, run_name: str, commit: str) -> tuple[str, bytes]:
    return _segment(plan_json, run_name, commit)


@app.function(gpu="A10", **_OPTS)
def segment_a10(plan_json: str, run_name: str, commit: str) -> tuple[str, bytes]:
    return _segment(plan_json, run_name, commit)


@app.function(gpu="L40S", **_OPTS)
def segment_l40s(plan_json: str, run_name: str, commit: str) -> tuple[str, bytes]:
    return _segment(plan_json, run_name, commit)


@app.function(gpu="A100-40GB", **_OPTS)
def segment_a100(plan_json: str, run_name: str, commit: str) -> tuple[str, bytes]:
    return _segment(plan_json, run_name, commit)


SEGMENTS = {
    "T4": segment_t4,
    "L4": segment_l4,
    "A10": segment_a10,
    "L40S": segment_l40s,
    "A100-40GB": segment_a100,
}
GPUS = tuple(SEGMENTS)  # a plan's "gpu" (default T4)


@app.local_entrypoint()
def main(plan: str, out: str, run_name: str = "", commit: str = "unknown") -> None:
    text = Path(plan).read_text()
    name = run_name or Path(plan).stem
    gpu = json.loads(text).get("gpu", "T4")
    if gpu not in SEGMENTS:
        raise SystemExit(f"plan gpu {gpu!r}: expected one of {', '.join(GPUS)}")
    rec, ckpt = SEGMENTS[gpu].remote(text, name, commit)
    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "run.json").write_text(json.dumps(json.loads(rec), indent=1, sort_keys=True) + "\n")
    (dest / "checkpoint.safetensors").write_bytes(ckpt)
    r = json.loads(rec)
    print(
        f"{r['stopped']}: {r['updates']} updates, {r['scenarios_seen']} scenarios, "
        f"{r['scenarios_per_second']:.0f} per second, {r['gpu_seconds']:.0f} GPU seconds"
    )
