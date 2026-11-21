"""Spec 016's whole-period learned model for the demonstrator (spec 035, owner 2026-11-21).

    (cd conformance/onnx && node demo_problems.mjs > /tmp/problems.json)
    uv run python -m tma2.viewer.demo_tlm_export --problems /tmp/problems.json \
        --out site/static/demo-data --golden conformance/onnx/demo/golden-tlm.json

For each training seed: reads the checkpoint from its results branch (``git show``) and checks
its digest against ``experiments/20261114-tlm-runs/export-check.json``. Exports the model with
spec 016's own ``period_predict.export_onnx`` (float32, opset 17, 1,440 rows) to
``tlm-s<k>.onnx``, and checks onnxruntime against torch on the demonstrator's own problems
(every 5-second problem of at most 1,440 rows). Writes ``tlm.json`` (digests, differences) and,
for seed 1, a golden file of the model's features and its own track (spec 016's
``learned.direct_track``) on those problems, against which the page's JavaScript port is
checked in Node.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
RUNS = {
    1: "tlm-s1-43507401545",
    2: "tlm-s2-43507608865",
    3: "tlm-s3-43507809179",
}
DT = 5.0


def checkpoint(seed: int, into: Path) -> Path:
    run = RUNS[seed]
    branch = f"origin/results/gputrain-{run}"
    subprocess.run(
        ["git", "fetch", "-q", "origin", f"results/gputrain-{run}"], cwd=ROOT, check=True
    )
    raw = subprocess.run(
        ["git", "show", f"{branch}:experiments/gputrain-runs/{run}/checkpoint.safetensors"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    want = json.loads((ROOT / "experiments/20261114-tlm-runs/export-check.json").read_text())
    got = hashlib.sha256(raw).hexdigest()
    if got != want[f"learned-s{seed}"]["checkpoint_sha256"]:
        raise SystemExit(f"seed {seed}: checkpoint digest {got[:12]}… is not the record's")
    path = into / f"tlm-s{seed}.safetensors"
    path.write_bytes(raw)
    return path


def problem_arrays(c: dict[str, Any], max_rows: int) -> dict[str, np.ndarray]:
    n = len(c["t"])
    own = np.zeros((1, max_rows, 2))
    bearing = np.zeros((1, max_rows))
    valid = np.zeros((1, max_rows), dtype=bool)
    mask = np.zeros((1, max_rows), dtype=bool)
    own[0, :n, 0] = c["ox"]
    own[0, :n, 1] = c["oy"]
    bearing[0, :n] = c["z"]
    valid[0, :n] = True
    mask[0, :n] = True
    return {"own": own, "bearing": bearing, "valid": valid, "mask": mask, "n": np.array(n)}


def main(argv: list[str] | None = None) -> int:
    import torch

    from tma2.regress.model import RegressorConfig
    from tma2.regress.period_data import period_features
    from tma2.regress.period_predict import export_onnx, run_model, run_onnx
    from tma2.regress.predict import load_model
    from tma2.timelate.learned import direct_track

    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--problems", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--golden", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    raw = Path(a.problems).read_bytes()
    cases = [
        c
        for c in json.loads(raw)["cases"]
        if len(c["t"]) <= 1440 and np.allclose(np.diff(c["t"]), DT)
    ]
    record: dict[str, Any] = {
        "what": "spec 016's whole-period model (period_predict.export_onnx) for spec 035",
        "problems_sha256": hashlib.sha256(raw).hexdigest(),
        "seeds": {},
    }
    golden: dict[str, Any] = {"problems_sha256": record["problems_sha256"], "cases": {}}
    torch.manual_seed(0)
    with tempfile.TemporaryDirectory() as tmp:
        for seed in RUNS:
            cfg_raw = json.loads((ROOT / f"configs/regress/tlm-s{seed}.json").read_text())
            cfg = RegressorConfig(**cfg_raw["config"])
            model = load_model(cfg, checkpoint(seed, Path(tmp)))
            path = out / f"tlm-s{seed}.onnx"
            export_onnx(model, path)
            worst = 0.0
            for c in cases:
                arr = problem_arrays(c, cfg.max_rows)
                n = int(arr["n"])
                f, th = period_features(
                    arr["own"],
                    arr["bearing"],
                    arr["valid"],
                    arr["mask"],
                    np.array([c["sigma"]]),
                    np.array([n]),
                    DT,
                )
                mask = arr["mask"]
                ref = run_model(model, f, mask)
                got = run_onnx(path, f, mask)
                tokens = -(-n // cfg.patch_rows)
                worst = max(
                    worst,
                    *(
                        float(np.abs(x[0, :tokens] - y[0, :tokens]).max())
                        for x, y in zip(ref, got, strict=True)
                    ),
                )
                if seed == 1:
                    period = SimpleNamespace(
                        first=0,
                        rows=n,
                        own=np.stack(
                            [np.zeros(n), np.asarray(c["ox"]), np.asarray(c["oy"])], axis=1
                        ),
                        obs=np.stack([np.zeros(n), np.asarray(c["z"]), np.ones(n)], axis=1),
                    )
                    track = direct_track(ref[0][0, :tokens], cast(Any, period), cfg.patch_rows)
                    golden["cases"][c["id"]] = {
                        "rows": n,
                        "theta": float(th[0]),
                        "features_sha256_f32": hashlib.sha256(f[0, :n].tobytes()).hexdigest(),
                        "features_head": f[0, :8].astype(np.float64).round(7).tolist(),
                        "mean": ref[0][0, :tokens].astype(np.float64).tolist(),
                        "logit": ref[2][0, :tokens].astype(np.float64).tolist(),
                        "track_every_6": track[::6].tolist(),
                    }
            record["seeds"][f"tlm-s{seed}"] = {
                "checkpoint_sha256": json.loads(
                    (ROOT / "experiments/20261114-tlm-runs/export-check.json").read_text()
                )[f"learned-s{seed}"]["checkpoint_sha256"],
                "onnx_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "onnx_bytes": path.stat().st_size,
                "problems": len(cases),
                "max_abs_difference": worst,
            }
            print(f"seed {seed}: {record['seeds'][f'tlm-s{seed}']}")
    (out / "tlm.json").write_text(json.dumps(record, indent=2) + "\n")
    Path(a.golden).write_text(json.dumps(golden) + "\n")
    bad = [k for k, v in record["seeds"].items() if not v["max_abs_difference"] <= 1e-3]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
