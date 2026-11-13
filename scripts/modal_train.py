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

image = modal.Image.debian_slim(python_version="3.12").uv_pip_install(
    "torch==2.15.0", "numpy", "numba", "safetensors", "pydantic>=2"
)
if modal.is_local():
    # The container imports this module by name to find the function (the pilot of
    # 2026-11-13 failed at start-up with "the 'modal_train' module is not available in the
    # remote environment"), so the script itself goes into the image beside the package.
    image = (
        image.add_local_python_source("tma2")
        .add_local_dir(str(ROOT / "configs"), remote_path="/root/configs")
        .add_local_file(__file__, remote_path="/root/modal_train.py")
    )
app = modal.App("gitma2-regress", image=image)
volume = modal.Volume.from_name("gitma2-regress", create_if_missing=True)


GPUS = ("T4", "L4", "A10", "L40S", "A100-40GB")  # a plan's "gpu" (default T4)


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


# One statically configured function per GPU type (a per-call override is documented for
# deployed functions; this form needs nothing beyond what the first runs already used).
SEGMENTS = {
    g: app.function(
        gpu=g,
        timeout=MAX_SEGMENT_SECONDS + STARTUP_SECONDS,
        volumes={"/vol": volume},
        name="segment_" + g.lower().replace("-", "_"),
        serialized=True,
    )(_segment)
    for g in GPUS
}


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
