from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from tests.conftest import FIXTURE_NAMES, fixture_dir
from tma2.data.canonical import canonical_json
from tma2.types import SCHEMA_VERSION, Scenario, dump_record


def test_schema_version_reads_gitma_files() -> None:
    from tma2.data.versions import compatible

    assert SCHEMA_VERSION == "0.17.0"
    assert compatible("0.16.0", SCHEMA_VERSION)


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_records_validate_and_dump_identically(name: str) -> None:
    with open(fixture_dir(name) / "test.ndjson", encoding="utf-8") as f:
        next(f)
        for line in f:
            raw = json.loads(line)
            model = Scenario.model_validate(raw)
            assert canonical_json(dump_record(model)) == line.rstrip("\n")


def test_unknown_keys_are_rejected() -> None:
    with open(fixture_dir("iter1-seed1") / "test.ndjson", encoding="utf-8") as f:
        next(f)
        raw = json.loads(next(f))
    raw["metadata"]["unexpected"] = 1
    with pytest.raises(ValidationError):
        Scenario.model_validate(raw)
