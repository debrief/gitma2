"""Canonical JSON and JavaScript number formatting (research R4)."""

from __future__ import annotations

import json
import math
import random

import numpy as np
import pytest

from tests.conftest import FIXTURE_NAMES, fixture_dir
from tma2.data.canonical import canonical_json, js_number, scenario_json


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, "0"),
        (-0.0, "0"),
        (1930.0, "1930"),
        (0.1, "0.1"),
        (-0.5, "-0.5"),
        (1e21, "1e+21"),
        (1e-7, "1e-7"),
        (1.5e-10, "1.5e-10"),
        (0.000001, "0.000001"),
        (0.00001234, "0.00001234"),
        (1e16, "10000000000000000"),
        (123456789012345680000.0, "123456789012345680000"),
        (2.5722222222222224, "2.5722222222222224"),
        (6.283185, "6.283185"),
        (float(np.float32(0.017453292519943295)), "0.01745329238474369"),
    ],
)
def test_js_number(value: float, expected: str) -> None:
    assert js_number(value) == expected


def test_js_number_rejects_non_finite() -> None:
    with pytest.raises(ValueError):
        js_number(math.nan)
    with pytest.raises(ValueError):
        js_number(math.inf)


def test_js_number_round_trips_random_float32_values() -> None:
    rng = random.Random(1)
    for _ in range(20_000):
        exponent = rng.uniform(-12, 12)
        x = float(np.float32(rng.choice((-1, 1)) * 10**exponent))
        s = js_number(x)
        assert float(s) == x
        assert "e" not in s or ("e+" in s or "e-" in s)
        assert not s.endswith(".0")


def test_canonical_json_sorts_keys_and_omits_whitespace() -> None:
    assert (
        canonical_json({"b": 1, "a": [True, None, "x", 2.5]}) == '{"a":[true,null,"x",2.5],"b":1}'
    )


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_lines_reserialise_byte_for_byte(name: str) -> None:
    with open(fixture_dir(name) / "test.ndjson", encoding="utf-8") as f:
        for line in f:
            text = line.rstrip("\n")
            record = json.loads(text)
            assert canonical_json(record) == text
            if record.get("record") == "scenario":
                assert scenario_json(record) == text
