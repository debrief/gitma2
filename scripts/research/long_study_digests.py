"""Spec 026: the digests the decision record binds (experiments/20261118-ls-decision/).

    uv run python scripts/research/long_study_digests.py

Prints JSON: the SHA-256 of each bound file, and one code digest over the long-engagement and
time-late modules and the simulator pieces they use (SHA-256 of "path sha256" lines, sorted).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    "configs/long/study-val.json",
    "configs/long/study-test.json",
    "configs/long/runs/ls-val.json",
    "configs/long/runs/ls-test.json",
    "configs/timelate/tl-e.json",
    "configs/timelate/tl-ranges.json",
    "configs/timelate/tl-broad.json",
    "configs/gateh/gh-a.json",
    ".github/workflows/long.yml",
]
CODE_GLOBS = ["src/tma2/long/*.py", "src/tma2/timelate/*.py", "src/tma2/cli/long.py"]
CODE_FILES = ["src/tma2/sim/prng.py", "src/tma2/sim/geometry.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    code = sorted({p for g in CODE_GLOBS for p in ROOT.glob(g)} | {ROOT / f for f in CODE_FILES})
    lines = "\n".join(f"{p.relative_to(ROOT)} {sha(p)}" for p in code)
    out = {
        "files": {f: sha(ROOT / f) for f in FILES},
        "code_sha256": hashlib.sha256(lines.encode()).hexdigest(),
        "code_files": [str(p.relative_to(ROOT)) for p in code],
    }
    from tma2.segment.codeid import code_digest

    out["c_code_sha256"] = code_digest()
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
