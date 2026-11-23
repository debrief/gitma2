"""Spec 037: the digests a decision record binds (plans, protocol, mix, conditions, code).

uv run python scripts/research/rmis_digests.py > experiments/<decision>/digests.json
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    "configs/rmis/protocol.json",
    "configs/rmis/heldout-conditions.json",
    "configs/gateh/conditions.json",
    "configs/gateh/gh-a.json",
    "configs/regress/ft-mix.json",
    "configs/regress/ft-s1.json",
    "configs/regress/ft-s2.json",
    "configs/regress/ft-s3.json",
]
CODE = [
    "src/tma2/sim/mismatch.py",
    "src/tma2/features/batch.py",
    "src/tma2/regress/mixture.py",
    "src/tma2/regress/data.py",
    "src/tma2/regress/model.py",
    "src/tma2/regress/train.py",
    "src/tma2/regress/remote.py",
    "src/tma2/regress/frame.py",
    "src/tma2/regress/predict.py",
    "src/tma2/regress/intervals.py",
    "src/tma2/regress/mread.py",
    "scripts/modal_train.py",
]


def sha(p: str) -> str:
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main() -> None:
    h = hashlib.sha256()
    for p in CODE:
        h.update(p.encode() + b"\0" + (ROOT / p).read_bytes())
    out = {
        "files": {p: sha(p) for p in FILES},
        "code": {p: sha(p) for p in CODE},
        "code_sha256": h.hexdigest(),
    }
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
