"""P0 check 1: the Python generator reproduces gitma's committed files (spec 001 FR-012, FR-013).

Two levels: (1) scenario-level comparison with the one-ulp float32 tolerance of the constitution,
counting and reporting residuals; (2) byte-level: regenerating each fixture with its header's
``created_by`` and provenance gives files with gitma's SHA-256 digests.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from tests.conftest import FIXTURE_NAMES, fixture_dir, fixture_header, fixture_ranges
from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.data.f32pack import block_to_scenario, read_pack_raw
from tma2.data.io import file_digest
from tma2.sim.generate import generate_scenario
from tma2.types import dump_record

PROVENANCE_KEYS = ("created_by", "generator_git_commit", "generator_git_dirty")


def ulp_distance(a: float, b: float) -> int:
    fa, fb = np.float32(a), np.float32(b)
    if fa == fb:
        return 0
    return abs(int(fa.view(np.int32)) - int(fb.view(np.int32)))


class Comparison:
    def __init__(self) -> None:
        self.floats = 0
        self.ulp1: dict[str, int] = {}
        self.failures: list[str] = []

    def compare(self, path: str, a: Any, b: Any) -> None:
        if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
            if a != b:
                self.failures.append(f"{path}: {a!r} != {b!r}")
        elif isinstance(a, dict) and isinstance(b, dict):
            if set(a) != set(b):
                self.failures.append(f"{path}: keys {sorted(set(a) ^ set(b))}")
            for k in sorted(set(a) & set(b)):
                self.compare(f"{path}.{k}", a[k], b[k])
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                self.failures.append(f"{path}: length {len(a)} != {len(b)}")
            for i, (x, y) in enumerate(zip(a, b, strict=False)):
                self.compare(f"{path}[{i}]", x, y)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if isinstance(a, int) and isinstance(b, int):
                if a != b:
                    self.failures.append(f"{path}: {a} != {b}")
                return
            self.floats += 1
            d = ulp_distance(float(a), float(b))
            if d == 1:
                field = path.split("]")[-1].rsplit(".", 1)[-1]
                self.ulp1[field] = self.ulp1.get(field, 0) + 1
            elif d > 1 or (math.isnan(float(a)) != math.isnan(float(b))):
                self.failures.append(f"{path}: {a!r} != {b!r} ({d} ulp)")
        elif a != b:
            self.failures.append(f"{path}: {a!r} != {b!r}")


def _fixture_scenarios(name: str) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """(split, header, scenario dict) for every scenario in the fixture's pack files."""
    out = []
    d = fixture_dir(name)
    for split in ("train", "validation", "test", "heldout"):
        pack = d / f"{split}.f32pack"
        if not pack.exists():
            continue
        header, blocks = read_pack_raw(pack)
        hdr = dump_record(header)
        for _, meta, own, tgt, obs in blocks:
            out.append((split, hdr, block_to_scenario(meta, own, tgt, obs)))
    if not out:  # iter1 fixture: NDJSON test split only
        with open(d / "test.ndjson", encoding="utf-8") as f:
            hdr = json.loads(f.readline())
            for line in f:
                out.append(("test", hdr, json.loads(line)))
    return out


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_scenarios_match_within_one_ulp(name: str, capsys: pytest.CaptureFixture[str]) -> None:
    cmp = Comparison()
    n = 0
    redraws_by_split: dict[str, int] = {}
    for split, hdr, theirs in _fixture_scenarios(name):
        ranges = hdr["parameter_ranges"]
        g = generate_scenario(int(hdr["dataset_seed"]), theirs["metadata"]["index"], ranges)
        mine = dump_record(g.scenario)
        cmp.compare(f"{split}[{theirs['metadata']['index']}]", theirs, mine)
        redraws_by_split[split] = redraws_by_split.get(split, 0) + g.redraws
        n += 1
        if len(cmp.failures) > 20:
            break
    for split, hdr, _ in {s: (s, h, None) for s, h, _ in _fixture_scenarios(name)}.values():
        assert redraws_by_split[split] == hdr["redraw_count"], f"{name}/{split} redraw count"
    with capsys.disabled():
        print(
            f"\nconformance {name}: scenarios={n} floats={cmp.floats} "
            f"one-ulp residuals={sum(cmp.ulp1.values())} {cmp.ulp1 or ''}"
        )
    assert not cmp.failures, "\n".join(cmp.failures[:20])


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_regenerated_files_have_gitma_digests(name: str, tmp_path: Path) -> None:
    hdr = fixture_header(name)
    ranges, heldout = fixture_ranges(name)
    count = hdr["index_end"] if hdr["split"] == "test" else None
    assert count is not None
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(int(hdr["dataset_seed"])),
            count=count,
            out_dir=tmp_path,
            ranges=hdr["parameter_ranges"],
            heldout_ranges=heldout,
            format="both",
            created_by=hdr["created_by"],
            generator_git_commit=hdr["generator_git_commit"],
            generator_git_dirty=hdr["generator_git_dirty"],
        )
    )
    expected = json.loads((fixture_dir(name) / "digests.json").read_text())
    got = {f: file_digest(tmp_path / f) for f in expected}
    assert got == expected
    assert ranges == hdr["parameter_ranges"]
