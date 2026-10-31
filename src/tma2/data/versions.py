"""Schema and generator version compatibility (gitma ``packages/data/src/versions.ts``)."""

from __future__ import annotations

from tma2.sim.version import GENERATOR_VERSION
from tma2.types import SCHEMA_VERSION, RecordError

READABLE_GENERATOR_VERSIONS: tuple[str, ...] = ("0.1.0", "0.2.0", "0.3.0", "0.4.0", "0.5.0")
"""Generator versions whose files this build reads. Each later version reproduces the earlier
ones byte for byte when the ranges lack the newer parameters (gitma's record), so earlier
datasets stay readable; 0.4.0 is included because gitma's phase-3 datasets exist as files."""


def _parts(v: str) -> tuple[int, int]:
    major, minor = v.split(".")[:2]
    return int(major), int(minor)


def compatible(file_version: str, build_version: str) -> bool:
    """Same MAJOR and the file's MINOR not newer than this build's."""
    f_major, f_minor = _parts(file_version)
    b_major, b_minor = _parts(build_version)
    return f_major == b_major and f_minor <= b_minor


def check_versions(file: str, schema_version: str, generator_version: str | None) -> None:
    """Reject an incompatible schema version or an unknown generator version."""
    if not compatible(schema_version, SCHEMA_VERSION):
        raise RecordError(
            file,
            "header",
            f"schema version {schema_version} is incompatible with this build ({SCHEMA_VERSION})",
        )
    if generator_version is not None and generator_version not in READABLE_GENERATOR_VERSIONS:
        raise RecordError(
            file,
            "header",
            f"generator version {generator_version} does not match this build "
            f"({GENERATOR_VERSION}); regenerate the dataset",
        )
