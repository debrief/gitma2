"""Spec 016 FR-015, made good in spec 017: the ONNX export of each trained whole-period
model, run by onnxruntime on CPU, against the torch model.

    uv run python scripts/research/tlm_export_check.py --work <scratch dir> --out <json>

For each seed the checkpoint is read from its results branch (named in
`configs/timelate/runs/tl-e-test.json`), the model exported (opset 17, float32, dynamic
batch) and both run on 32 periods of the training stream's monitor slice (seed 339; no
validation or test data) at a batch size other than the trace's. Records the largest
absolute difference over tokens that exist, and the digests of the checkpoint and export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    import torch

    from tma2.regress import period_data as pdata
    from tma2.regress.model import RegressorConfig
    from tma2.regress.period_predict import export_check
    from tma2.regress.predict import load_model

    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    run = json.loads((ROOT / "configs/timelate/runs/tl-e-test.json").read_text())
    out: dict[str, object] = {}
    for name, v in run["learned"].items():
        subprocess.run(
            ["git", "fetch", "-q", "--depth", "1", "origin", v["branch"]], check=True, cwd=ROOT
        )
        blob = subprocess.run(
            ["git", "show", f"FETCH_HEAD:{v['dir']}/checkpoint.safetensors"],
            check=True,
            capture_output=True,
            cwd=ROOT,
        ).stdout
        ckpt = work / f"{name}.safetensors"
        ckpt.write_bytes(blob)
        cfg = RegressorConfig(**json.loads((ROOT / v["config"]).read_text())["config"])
        model = load_model(cfg, ckpt)
        x = pdata.monitor(cfg, pdata.load_mix(cfg.mix))
        onnx = work / f"{name}.onnx"
        prev = torch.get_default_dtype()
        torch.set_default_dtype(torch.float64)  # as the physics layer's CLIs leave it
        try:
            diff = export_check(model, onnx, x.f[:32], x.mask[:32])
        finally:
            torch.set_default_dtype(prev)
        out[name] = {
            "checkpoint_sha256": hashlib.sha256(blob).hexdigest(),
            "onnx_sha256": hashlib.sha256(onnx.read_bytes()).hexdigest(),
            "onnx_bytes": onnx.stat().st_size,
            "periods": 32,
            "max_abs_difference": float(diff),
            "pass": bool(diff < 1e-4),
        }
        print(name, out[name])
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0 if all(v["pass"] for v in out.values()) else 3  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())
