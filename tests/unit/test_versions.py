from __future__ import annotations

import pytest

from tma2.data.versions import check_versions
from tma2.types import SCHEMA_VERSION, RecordError


def test_schema_compatibility() -> None:
    major, minor, _ = SCHEMA_VERSION.split(".")
    check_versions("f", f"{major}.{int(minor) - 1}.9", None)
    check_versions("f", SCHEMA_VERSION, "0.3.0")
    with pytest.raises(RecordError, match="incompatible"):
        check_versions("f", f"{int(major) + 1}.0.0", None)
    with pytest.raises(RecordError, match="incompatible"):
        check_versions("f", f"{major}.{int(minor) + 1}.0", None)


def test_generator_version_must_be_readable() -> None:
    with pytest.raises(RecordError, match="generator version 9.9.9 does not match this build"):
        check_versions("f", SCHEMA_VERSION, "9.9.9")
