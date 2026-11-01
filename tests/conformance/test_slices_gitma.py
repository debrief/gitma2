"""Slice keys equal gitma's at and around every band edge (P0 panel round 1).

The fixture is gitma's own ``sliceKeys`` (``scripts/slices_fixture.mjs``) on metadata placed at,
just below and just above each range, zig, σ, dropout and manoeuvre band edge, in double and in
float32; never regenerate it from gitma2.
"""

from __future__ import annotations

import json
from pathlib import Path

from tma2.eval.slices import slice_keys

CASES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "gitma" / "slices" / "cases.json").read_text()
)


def test_slice_keys_equal_gitma_at_band_edges() -> None:
    assert len(CASES) > 150
    bad = [
        (c["meta"], c["keys"], slice_keys(c["meta"]))
        for c in CASES
        if slice_keys(c["meta"]) != c["keys"]
    ]
    assert not bad, bad[:3]
