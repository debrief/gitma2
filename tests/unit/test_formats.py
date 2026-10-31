"""Readers, writers and round trips for NDJSON and Float32-pack, on gitma's fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import FIXTURE_NAMES, fixture_dir
from tma2.data.f32pack import PackWriter, read_pack
from tma2.data.io import file_digest
from tma2.data.ndjson import NdjsonWriter, read_ndjson
from tma2.types import RecordError


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_files_read_and_validate(name: str) -> None:
    d = fixture_dir(name)
    ds = read_ndjson(d / "test.ndjson")
    scenarios = list(ds.scenarios())
    assert len(scenarios) == ds.header.scenario_count
    for split in ("train", "validation", "test", "heldout"):
        pack = d / f"{split}.f32pack"
        if not pack.exists():
            continue
        ps = read_pack(pack)
        n = sum(1 for _ in ps.scenarios())
        assert n == ps.header.scenario_count


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_pack_and_ndjson_round_trip(name: str, tmp_path: Path) -> None:
    d = fixture_dir(name)
    src = read_ndjson(d / "test.ndjson")
    pack_path = tmp_path / "test.f32pack"
    w = PackWriter(pack_path, src.header)
    for s in src.scenarios():
        w.write(s)
    w.close()
    expected = json.loads((d / "digests.json").read_text())
    if "test.f32pack" in expected:
        assert file_digest(pack_path) == expected["test.f32pack"]
    back = tmp_path / "back.ndjson"
    ps = read_pack(pack_path)
    nw = NdjsonWriter(back, ps.header)
    for s in ps.scenarios():
        nw.write(s)
    nw.close()
    assert back.read_bytes() == (d / "test.ndjson").read_bytes()


def test_bad_files_are_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "empty.ndjson"
    empty.write_text("")
    with pytest.raises(RecordError, match="empty file"):
        read_ndjson(empty)
    bad = tmp_path / "bad.f32pack"
    bad.write_bytes(b"NOTAPACK" + b"\0" * 16)
    with pytest.raises(RecordError, match="bad magic"):
        read_pack(bad)
    truncated = tmp_path / "trunc.ndjson"
    src = fixture_dir("iter1-seed1") / "test.ndjson"
    lines = src.read_text().splitlines()
    truncated.write_text(lines[0] + "\n")
    with pytest.raises(RecordError, match="declares"):
        list(read_ndjson(truncated).scenarios())
