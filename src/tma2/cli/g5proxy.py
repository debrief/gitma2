"""tma2-g5proxy: the causal unsettled proxy's features for a feature cache's rows (spec 010 T004).

    uv run tma2-g5proxy --data <split.f32pack> --features <cache shards *.npz> --out <dir>

For each feature-cache shard, writes ``<dir>/<shard name>`` with the same rows: ``ordinal``, ``k``
and the residual statistics of ``calib.proxy`` (bearings at rows ≤ k only, against E's state at
k). The header binds the data digest (which must equal the cache header's), the shard's
SHA-256, and this run's commit and dirty flag (read before anything is written).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-g5proxy", description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--features", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    from tma2.calib.proxy import residual_features
    from tma2.data.provenance import read_git_provenance
    from tma2.segment.gate import sha256_file
    from tma2.segment.score import iter_selected

    g = read_git_provenance()  # before anything is written
    shards = [(p, np.load(p)) for p in a.features]
    heads = [json.loads(str(z["header"])) for _, z in shards]
    digest = sha256_file(a.data)
    for (p, _), h in zip(shards, heads, strict=True):
        if h.get("dataset_digest") != digest:
            print(f"{p}: cache made from another dataset", file=sys.stderr)
            return 2
    ords = np.concatenate([z["ordinal"] for _, z in shards])
    lo, hi = int(ords.min()), int(ords.max())
    blocks = {}
    for j, m, own, _tgt, obs in iter_selected(a.data, lo, hi - lo + 1):
        blocks[j] = (float(m["parameters"]["noise_sigma_rad"]), np.asarray(own, np.float64),
                     np.asarray(obs, np.float64))  # fmt: skip
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for (p, z), h in zip(shards, heads, strict=True):
        n = z["ordinal"].shape[0]
        cols: dict[str, np.ndarray] = {}
        for i in range(n):
            o, k = int(z["ordinal"][i]), int(z["k"][i])
            if o not in blocks:
                print(f"{p}: ordinal {o} is not in {a.data}", file=sys.stderr)
                return 2
            sigma, own, obs = blocks[o]
            f = residual_features(z["state"][i], k, own, obs, sigma)
            for key, v in f.items():
                cols.setdefault(key, np.full(n, np.nan))[i] = v
        header = {
            "record": "proxy_header",
            "dataset_digest": digest,
            "features_sha256": sha256_file(p),
            "features_dataset_digest": h.get("dataset_digest"),
            "weights_sha256": h.get("weights_sha256"),
            "git_commit": g.commit,
            "git_dirty": g.dirty,
        }
        head = np.array(json.dumps(header, sort_keys=True))
        arrays: dict[str, Any] = {"ordinal": z["ordinal"], "k": z["k"], "header": head, **cols}
        np.savez_compressed(out / Path(p).name, **arrays)
        total += n
    print(json.dumps({"rows": total, "shards": len(shards), "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
