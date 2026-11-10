"""``tma2-rpredict``: the regressor control's prediction rows on one split (spec 012)."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-rpredict", description=__doc__)
    ap.add_argument("--weights", required=True, help="checkpoint.safetensors")
    ap.add_argument("--config", required=True)
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="reg")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=1 << 30)
    a = ap.parse_args(argv)
    import torch

    from tma2.data.canonical import canonical_json
    from tma2.data.provenance import read_git_provenance
    from tma2.regress.model import RegressorConfig
    from tma2.regress.predict import load_model, predict_split
    from tma2.regress.train import config_digest
    from tma2.segment.gate import sha256_file
    from tma2.types import SCHEMA_VERSION

    t0 = time.time()
    gp = read_git_provenance()  # before any output
    cfg = RegressorConfig(**json.loads(Path(a.config).read_text()))
    torch.set_num_threads(4)
    model = load_model(cfg, Path(a.weights))
    recs = predict_split(model, a.inp, a.start, a.count)
    head = {
        "record": "header",
        "schema_version": SCHEMA_VERSION,
        "estimator": a.name,
        "mode": "per_timestep",
        "kind": "regressor-control",
        "dataset_digest": sha256_file(a.inp),
        "config_sha256": config_digest(cfg),
        "weights_sha256": hashlib.sha256(Path(a.weights).read_bytes()).hexdigest(),
        "git_commit": gp.commit,
        "git_dirty": gp.dirty,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(canonical_json(head) + "\n")
        for j, index, rows in sorted(recs, key=lambda r: r[0]):
            rec = {
                "record": "prediction",
                "ordinal": j,
                "scenario_index": index,
                "estimator": a.name,
                "mode": "per_timestep",
                "rows": rows,
            }
            f.write(canonical_json(rec) + "\n")
    print(f"wrote {out}: {len(recs)} scenarios [{time.time() - t0:.0f} s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
