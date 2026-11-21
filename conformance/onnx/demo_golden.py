"""Golden least-squares vectors for the demonstrator (spec 035 FR-025, shared golden vectors).

    (cd conformance/onnx && node demo_problems.mjs > demo/problems.json)
    uv run python conformance/onnx/demo_golden.py conformance/onnx/demo/problems.json \
        conformance/onnx/demo/golden-ls.json

Runs Python's reference batch least squares (``tma2.references.lsq.solve_batch``, the code the
gates score) on each problem the page builds and writes the solution, so the page's JavaScript
port (spec 021's ``lsq.js``) can be checked against it in Node (``demo_node.mjs``).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from tma2.references.lsq import solve_batch


def solve(case: dict[str, list[float]]) -> dict[str, object]:
    t, ox, oy, z = (np.asarray(case[k], dtype=np.float64) for k in ("t", "ox", "oy", "z"))
    valid = np.ones(t.shape[0], dtype=np.uint8)
    found, th, conv, it, c = solve_batch(t, ox, oy, z, valid, t.shape[0], 50)
    return {
        "found": bool(found),
        "theta": [float(x) for x in th],
        "converged": bool(conv),
        "iterations": int(it),
        "cost": float(c),
    }


def main(argv: list[str]) -> int:
    src, out = Path(argv[0]), Path(argv[1])
    raw = src.read_bytes()
    cases = json.loads(raw)["cases"]
    rec = {
        "what": "tma2.references.lsq.solve_batch on the demonstrator's problems (spec 035)",
        "problems_sha256": hashlib.sha256(raw).hexdigest(),
        "solutions": {c["id"]: solve(c) for c in cases},
    }
    out.write_text(json.dumps(rec, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
