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


@pytest.fixture(scope="session")
def man2_pack(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A small MAN2 split (generator 0.6.0, seed 316, 60 scenarios; the train split, 48 of them),
    generated once per session so no binary fixture is committed."""
    import numpy as np

    from tma2.data.dataset import GenerateOptions, generate_dataset

    root = Path(__file__).resolve().parents[1] / "configs"
    out = tmp_path_factory.mktemp("man2")
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(316),
            count=60,
            out_dir=out,
            ranges=json.loads((root / "man2-ranges.json").read_text()),
            heldout_ranges=json.loads((root / "man2-heldout.json").read_text()),
            format="f32pack",
            created_by="tests",
            generator_git_commit=TEST_PROVENANCE[0],
            generator_git_dirty=TEST_PROVENANCE[1],
        )
    )
    return out / "train.f32pack"
