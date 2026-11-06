"""The segmenter's code identity (Gate S panel round 2): a digest over the source files a
segmentation depends on, recorded in every segmentation header as ``code_sha256``.

The parameter digest (``segmenter_sha256``) binds a segmenter's configuration only, so a gate
could not tell segmentations made by the leaky r1 code from the fixed r2 code. A decision record
names the code digest it accepts; a gate refuses any other.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# Relative to the ``tma2`` package: every module ``tma2-segment`` runs for C, O and L.
SOURCES = (
    "segment/__init__.py",
    "segment/confirm.py",
    "segment/evidence.py",
    "segment/inputs.py",
    "segment/ownship.py",
    "segment/search.py",
    "segment/segmenter.py",
    "detect/confirm.py",
    "detect/controls.py",
    "physics/layer.py",
    "physics/segmentation.py",
    "references/classical.py",
    "references/lsq.py",
)


def code_digest(root: Path | None = None) -> str:
    """SHA-256 over ``path:sha256(content)`` lines of ``SOURCES``, in that order."""
    base = root or Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for rel in SOURCES:
        h.update(f"{rel}:{hashlib.sha256((base / rel).read_bytes()).hexdigest()}\n".encode())
    return h.hexdigest()
