"""Spec 022: the time-late page's data equal the committed record (SC-003)."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from tma2.timelate.score import COLS, row_errors

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site/static/timelate-data"


def test_files_match_manifest_and_errors_match_record() -> None:
    man = json.loads((DATA / "manifest.json").read_text())
    for name, digest in man["files"].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest
    for path, digest in man["inputs"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    z = np.load(ROOT / man["record"] / "tracks.npz")
    for split, meta in man["splits"].items():
        doc = json.loads(gzip.decompress((DATA / meta["file"]).read_bytes()))
        assert len(doc["periods"]) == meta["periods"] == 20
        for p in doc["periods"]:
            m = z[f"{split}/period"] == p["ordinal"]
            tr = z[f"{split}/truth"][m].astype(np.float64)
            for s, sysd in p["systems"].items():
                err = row_errors(z[f"{split}/{s}"][m].astype(np.float64), tr)
                for j, c in enumerate(COLS):
                    want = float(np.nanmedian(err[:, j]))
                    got = sysd["median"][c]
                    assert got is not None and abs(got - want) <= 1e-6 * max(abs(want), 1e-12)
