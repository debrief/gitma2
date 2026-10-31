"""Golden test (constitution II): seed 1, count 10 with gitma's iteration-1 ranges produces files
byte-identical to gitma's committed golden digests. ``UPDATE_GOLDEN=1`` rewrites the digests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from tests.conftest import TEST_PROVENANCE, fixture_dir
from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.data.io import file_digest
from tma2.sim.ranges import DEFAULT_RANGES, HELDOUT_RANGES

FILES = [
    f"{s}.{ext}"
    for s in ("train", "validation", "test", "heldout")
    for ext in ("ndjson", "f32pack")
]


def test_seed1_count10_matches_gitma_golden(tmp_path: Path) -> None:
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(1),
            count=10,
            out_dir=tmp_path,
            ranges=DEFAULT_RANGES,
            heldout_ranges=HELDOUT_RANGES,
            format="both",
            created_by="tma-generate --seed 1 --count 10",
            generator_git_commit=TEST_PROVENANCE[0],
            generator_git_dirty=TEST_PROVENANCE[1],
            schema_version="0.16.0",  # gitma's digests were made at schema 0.16.0
        )
    )
    digests = {f: file_digest(tmp_path / f) for f in FILES}
    golden = fixture_dir("iter1-seed1") / "digests.json"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        golden.write_text(json.dumps(digests, indent=2) + "\n")
    assert digests == json.loads(golden.read_text())
    assert (tmp_path / "test.ndjson").read_bytes() == (
        fixture_dir("iter1-seed1") / "test.ndjson"
    ).read_bytes()
    written = json.loads((tmp_path / "digests.json").read_text())
    assert written == digests
