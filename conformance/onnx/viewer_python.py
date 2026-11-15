"""The viewer's shipped data against a fresh Python onnxruntime run (spec 020 FR-015).

    uv run python conformance/onnx/viewer_python.py site/static/viewer-data

Checks every file's digest against ``manifest.json``, then re-runs the shipped ``model.onnx``
on every shipped row's inputs and compares with the shipped outputs (relative difference, as
the other legs, at most 1e-5; in practice they should be identical on one CPU family).
Exit 1 on any failure.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort  # type: ignore[import-untyped]

TOL = 1e-5


def main(argv: list[str] | None = None) -> int:
    d = Path((argv or sys.argv[1:])[0])
    man = json.loads((d / "manifest.json").read_text())
    bad = [
        f
        for f, want in man["files"].items()
        if hashlib.sha256((d / f).read_bytes()).hexdigest() != want
    ]
    sess = ort.InferenceSession(str(d / "model.onnx"), providers=["CPUExecutionProvider"])
    worst = 0.0
    rows = 0
    for e in man["engagements"]:
        doc = json.loads(gzip.decompress((d / e["json"]).read_bytes()))
        v = np.frombuffer(gzip.decompress((d / e["binary"]).read_bytes()), dtype="<f8")
        assert v.size == doc["binary_values"], e["binary"]
        for r in range(len(doc["e_rows"])):
            feeds, want = {}, {}
            for L in doc["layout"]:
                per = int(np.prod(L["shape"]))
                start = L["offset"] + (0 if L["shared"] else r * per)
                a = v[start : start + per].reshape(L["shape"])
                if L["kind"] == "input":
                    feeds[L["name"]] = a.astype(np.int64) if L["dtype"] == "int64" else a
                else:
                    want[L["name"]] = a
            names = [o.name for o in sess.get_outputs()]
            got = dict(zip(names, sess.run(None, feeds), strict=True))
            for name, w in want.items():
                g = got[name].astype(np.float64)
                both_nan = np.isnan(g) & np.isnan(w)
                rel = np.abs(g - w) / np.maximum(np.abs(w), 1.0)
                worst = max(worst, float(np.max(np.where(both_nan, 0.0, rel))))
            rows += 1
    print(json.dumps({"rows": rows, "max_rel_diff": worst, "tol": TOL, "bad_digests": bad}))
    if bad or not worst <= TOL or rows == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
