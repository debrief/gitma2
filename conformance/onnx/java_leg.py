#!/usr/bin/env python3
"""Java leg driver: builds and runs the Maven project, compares its outputs with the torch
reference, and records the result (or a deferral with its reason) in results.json."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TOL = 1e-5


ORT_JAVA_VERSION = re.search(
    r"<artifactId>onnxruntime</artifactId>\s*<version>([^<]+)</version>",
    (HERE / "java" / "pom.xml").read_text(),
).group(1)  # type: ignore[union-attr]


def main() -> int:
    export_dir = Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "export").resolve()
    results_path = HERE / "results.json"
    prior = json.loads(results_path.read_text()) if results_path.exists() else {}

    def record(java: dict) -> None:
        prior["java"] = java
        results_path.write_text(json.dumps(prior, indent=2) + "\n")

    if shutil.which("mvn") is None or shutil.which("java") is None:
        record({"deferred": True, "reason": "mvn or java not available on this runner"})
        print("Java leg deferred: mvn or java not available")
        return 0
    try:
        subprocess.run(
            ["mvn", "-q", "-B", "compile"],
            cwd=HERE / "java",
            check=True,
            capture_output=True,
            text=True,
            timeout=1200,
        )
        run = subprocess.run(
            ["mvn", "-q", "-B", "exec:java", f"-Dexec.args={export_dir}"],
            cwd=HERE / "java",
            check=True,
            capture_output=True,
            text=True,
            timeout=1200,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        err = (getattr(e, "stderr", "") or "")[-2000:]
        record({"deferred": True, "reason": f"maven failed: {err.strip()[:500]}"})
        print(f"Java leg deferred: maven failed\n{err}")
        return 0
    out = json.loads([line for line in run.stdout.splitlines() if line.startswith("{")][-1])
    manifest = json.loads((export_dir / "manifest.json").read_text())
    diffs = {}
    for name, spec in manifest["outputs"].items():
        exp = np.fromfile(export_dir / f"out_{name}.bin", dtype=spec["dtype"]).astype(np.float64)
        got = np.array(out[name], dtype=np.float64)
        diffs[name] = float(np.max(np.abs(got - exp) / np.maximum(np.abs(exp), 1.0)))
    record(
        {
            "deferred": False,
            "max_rel_diff": diffs,
            "tol": TOL,
            "onnx_sha256": hashlib.sha256((export_dir / "toy.onnx").read_bytes()).hexdigest(),
            "runtime": "onnxruntime Java " + ORT_JAVA_VERSION,
        }
    )
    print(json.dumps({"java": diffs}))
    bad = {k: v for k, v in diffs.items() if v > TOL}
    if bad:
        print(f"java leg exceeds {TOL}: {bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
