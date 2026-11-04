"""Golden test for generator 0.6.0's MAN2 path (spec 006, T020): seed 316, 40 scenarios, the
MAN2 ranges with their held-out twin, written in both formats with fixed provenance. The digests
in ``tests/fixtures/man2-seed316/digests.json`` were made by this test at the commit that added
the leg model; ``UPDATE_GOLDEN=1`` rewrites them and the commit must say why. The header's schema version is
pinned to 0.22.0, the version they were made under."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from tests.conftest import TEST_PROVENANCE
from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.data.io import file_digest

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "tests" / "fixtures" / "man2-seed316" / "digests.json"
FILES = [
    f"{s}.{ext}"
    for s in ("train", "validation", "test", "heldout")
    for ext in ("ndjson", "f32pack")
]


def test_man2_seed316_matches_golden(tmp_path: Path) -> None:
    ranges = json.loads((ROOT / "configs" / "man2-ranges.json").read_text())
    heldout = json.loads((ROOT / "configs" / "man2-heldout.json").read_text())
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(316),
            count=40,
            out_dir=tmp_path,
            ranges=ranges,
            heldout_ranges=heldout,
            format="both",
            created_by="tma2-generate --seed 316 --count 40 --ranges configs/man2-ranges.json",
            generator_git_commit=TEST_PROVENANCE[0],
            generator_git_dirty=TEST_PROVENANCE[1],
            # the header version the golden was made under; later schema versions change only
            # the header (gitma's fixtures pin 0.16.0 the same way)
            schema_version="0.22.0",
        )
    )
    digests = {f: file_digest(tmp_path / f) for f in FILES}
    if os.environ.get("UPDATE_GOLDEN") == "1":
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(digests, indent=2) + "\n")
    assert digests == json.loads(GOLDEN.read_text())
