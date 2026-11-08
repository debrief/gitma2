"""tma2-g3predict: a calibrated copy of an E prediction file (spec 008 contracts/cli.md).

    uv run tma2-g3predict --in <E prediction.ndjson> --features <cache.npz>… --plan <g3 plan>
        (--model <id> --weights <head.safetensors> | --temperature <temperature.json>) --out <file>

Each row named in the cache gets its covariance scaled by e^(2s) (``calib.predict``); every
point field is copied unchanged (FR-020). The header gains ``calibration``: the kind, the
weights' or temperatures' digest and the plan's. Refuses a cache made from other E weights than
the prediction file's.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g3predict", description=__doc__)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--features", nargs="+", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--model")
    ap.add_argument("--weights")
    ap.add_argument("--temperature")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if (a.weights is None) == (a.temperature is None):
        print("give exactly one of --weights and --temperature", file=sys.stderr)
        return 2

    from tma2.calib import data
    from tma2.calib.predict import write_calibrated
    from tma2.segment.gate import sha256_file

    raw = Path(a.plan).read_bytes()
    plan, plan_sha = json.loads(raw), hashlib.sha256(raw).hexdigest()
    d = data.load(a.features)
    with open(a.inp, encoding="utf-8") as fh:
        ph = json.loads(fh.readline())
    if ph.get("weights_sha256") != d.header.get("weights_sha256"):
        print(f"{a.inp}: the cache was made from other E weights", file=sys.stderr)
        return 2
    if a.weights:
        import torch
        from safetensors.torch import load_file

        from tma2.calib.head import CalHead
        from tma2.calib.train import predict_s
        from tma2.types.generated.tma import CalibrationHeadConfig

        torch.set_default_dtype(torch.float64)
        m = plan["models"][a.model]
        cfg = CalibrationHeadConfig.model_validate({**plan["head"], "seed": m["seed"]})
        head = CalHead(cfg, d.x.shape[1]).double()
        head.load_state_dict(load_file(a.weights))
        s = predict_s(head, d.x)
        cal = {"kind": "head", "model": a.model, "weights_sha256": sha256_file(a.weights)}
    else:
        from tma2.calib.temperature import apply

        trec = json.loads(Path(a.temperature).read_text())
        s = apply(trec["temperatures"], d, list(trec["slices"]))
        cal = {"kind": "temperature", "weights_sha256": sha256_file(a.temperature)}
    cal["plan_sha256"] = plan_sha
    s = np.where(d.usable, s, 0.0)
    scales = {(int(j), float(t)): float(v) for j, t, v in zip(d.ordinal, d.t, s, strict=True)}
    n = write_calibrated(Path(a.inp), Path(a.out), scales, cal)
    print(json.dumps({"rows_scaled": n, "out": a.out, **cal}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
