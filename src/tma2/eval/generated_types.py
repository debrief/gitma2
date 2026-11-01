"""Re-exports of the evaluation-side schema types (constitution I)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from tma2.types import RecordError
from tma2.types.generated.tma import (
    CurvePoint,
    ExperimentManifest,
    GateCheck,
    GateVerdict,
    MetricsRecord,
    NaiveMeans,
    NaiveModel,
    Prediction,
    PredictionHeader,
    PredictionRow,
)

__all__ = [
    "CurvePoint",
    "ExperimentManifest",
    "GateCheck",
    "GateVerdict",
    "MetricsRecord",
    "NaiveMeans",
    "NaiveModel",
    "Prediction",
    "PredictionHeader",
    "PredictionRow",
    "parse_prediction",
]


def parse_prediction[M: BaseModel](model: type[M], raw: Any, file: str, where: int | str) -> M:
    try:
        return model.model_validate(raw)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(p) for p in first.get("loc", ()))
        raise RecordError(file, where, f"{loc}: {first.get('msg', 'invalid')}") from e
