"""PRNG port against gitma's known-answer vectors (tests/fixtures/prng-vectors.json)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tma2.sim import prng

VECTORS = json.loads((Path(__file__).parent.parent / "fixtures" / "prng-vectors.json").read_text())


@pytest.mark.parametrize("seed_text", sorted(VECTORS))
def test_known_answers(seed_text: str) -> None:
    exp = VECTORS[seed_text]
    seed = np.uint64(int(seed_text))
    s = prng.create_rng(seed)
    assert [int(w) for w in s] == exp["state_words"]
    assert [prng.uniform01(s) for _ in range(8)] == exp["uniform01"]
    assert [str(int(prng.derive_seed(seed, i))) for i in range(4)] == exp["derive_seed"]
    assert prng.uniform_int(prng.create_rng(seed), 7) == exp["uniform_int_7"]
    # Transcendental functions may differ from V8 in the last double bit (research R3).
    g = prng.create_rng(seed)
    for got, want in zip([prng.gaussian(g) for _ in range(4)], exp["gaussian"], strict=True):
        assert got == pytest.approx(want, abs=1e-14)
    assert prng.log_uniform(prng.create_rng(seed), 1.0, 100.0) == pytest.approx(
        exp["log_uniform_1_100"], abs=1e-12
    )


def test_parse_seed() -> None:
    assert int(prng.parse_seed("0")) == 0
    assert int(prng.parse_seed("18446744073709551615")) == 2**64 - 1
    with pytest.raises(ValueError, match="exceeds 64 bits"):
        prng.parse_seed("18446744073709551616")
    with pytest.raises(ValueError, match="decimal integer"):
        prng.parse_seed("-1")
    with pytest.raises(ValueError, match="decimal integer"):
        prng.parse_seed("1e3")


def test_uniform01_range() -> None:
    s = prng.create_rng(np.uint64(99))
    values = [prng.uniform01(s) for _ in range(10_000)]
    assert min(values) >= 0.0 and max(values) < 1.0
    assert abs(sum(values) / len(values) - 0.5) < 0.02
