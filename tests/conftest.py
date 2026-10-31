from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "gitma"
FIXTURE_NAMES = ("iter1-seed1", "iter4-seed777", "phase4-seed777")

TEST_PROVENANCE = ("0123456789abcdef0123456789abcdef01234567", False)


def fixture_dir(name: str) -> Path:
    return FIXTURES / name


def fixture_header(name: str) -> dict[str, Any]:
    with open(fixture_dir(name) / "test.ndjson", encoding="utf-8") as f:
        return dict(json.loads(f.readline()))


def fixture_ranges(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    d = fixture_dir(name)
    return (
        json.loads((d / "ranges.json").read_text()),
        json.loads((d / "heldout-ranges.json").read_text()),
    )


@pytest.fixture(scope="session", autouse=True)
def _warm_numba() -> None:
    from tma2.sim.generate import warm_up

    warm_up()
