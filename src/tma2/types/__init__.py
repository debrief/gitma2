"""Generated data types (constitution I): the only place a persisted type is defined.

``generated/`` is produced from ``schema/tma.yaml`` by ``scripts/gen_types.py``; nothing in it is
hand-written. This module re-exports the models used across the package and adds the record
parsing helper that every file reader goes through.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from .generated.tma import (
    DatasetHeader,
    FloatRange,
    ManoeuvreKind,
    ManoeuvreSpan,
    Observation,
    ParameterRanges,
    PlatformState,
    RecordKind,
    Scenario,
    ScenarioMetadata,
    ScenarioParameters,
    Split,
    TargetManoeuvre,
    Track,
    TrackId,
)
from .generated.version import SCHEMA_VERSION

__all__ = [
    "SCHEMA_VERSION",
    "DatasetHeader",
    "FloatRange",
    "ManoeuvreKind",
    "ManoeuvreSpan",
    "Observation",
    "ParameterRanges",
    "PlatformState",
    "RecordError",
    "RecordKind",
    "Scenario",
    "ScenarioMetadata",
    "ScenarioParameters",
    "Split",
    "TargetManoeuvre",
    "Track",
    "TrackId",
    "dump_record",
    "parse_record",
]


class RecordError(ValueError):
    """A file whose content is not what its format promises: file, where, reason."""

    def __init__(self, file: str, where: int | str, reason: str) -> None:
        super().__init__(f"{file}:{where}: {reason}")
        self.file = file
        self.where = where
        self.reason = reason


def parse_record[M: BaseModel](model: type[M], raw: Any, file: str, where: int | str) -> M:
    """Validate ``raw`` as ``model`` or raise ``RecordError`` naming file and position."""
    try:
        return model.model_validate(raw)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(p) for p in first.get("loc", ()))
        raise RecordError(file, where, f"{loc}: {first.get('msg', 'invalid')}") from e


def dump_record(record: BaseModel) -> dict[str, Any]:
    """A plain dict with enums as strings and absent optional keys omitted (gitma's shape)."""
    return record.model_dump(mode="json", exclude_none=True)
