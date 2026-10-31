"""Prediction files: gitma's format (``PredictionHeader`` then one ``Prediction`` per scenario).

Writers stream (records are written as made); readers validate and bind the file to its truth
by digest when asked.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from tma2.data.canonical import canonical_json
from tma2.data.io import AtomicFile, file_digest
from tma2.data.versions import compatible
from tma2.types import SCHEMA_VERSION, RecordError

from .generated_types import Prediction, PredictionHeader, parse_prediction


class PredictionWriter:
    def __init__(self, path: str | Path, estimator: str, mode: str, truth_path: str | Path) -> None:
        self.path = str(path)
        self.file = AtomicFile(path)
        header = {
            "record": "header",
            "schema_version": SCHEMA_VERSION,
            "estimator": estimator,
            "mode": mode,
            "dataset_digest": file_digest(truth_path),
        }
        self.file.write((canonical_json(header) + "\n").encode("utf-8"))
        self.count = 0

    def write(self, prediction: dict[str, Any]) -> None:
        self.file.write((canonical_json(prediction) + "\n").encode("utf-8"))
        self.count += 1

    def close(self) -> None:
        self.file.commit()

    def abort(self) -> None:
        self.file.abort()


def read_prediction_header(path: str | Path) -> PredictionHeader:
    file = str(path)
    with open(file, encoding="utf-8") as fh:
        first = fh.readline()
    if first == "":
        raise RecordError(file, 1, "empty file")
    try:
        raw = json.loads(first)
    except json.JSONDecodeError as e:
        raise RecordError(file, 1, "malformed JSON") from e
    header = parse_prediction(PredictionHeader, raw, file, 1)
    if not compatible(header.schema_version, SCHEMA_VERSION):
        raise RecordError(
            file, 1, f"schema version {header.schema_version} is incompatible with {SCHEMA_VERSION}"
        )
    return header


def iter_predictions_raw(path: str | Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """(line number, raw prediction dict) for every prediction line."""
    file = str(path)
    with open(file, encoding="utf-8") as fh:
        fh.readline()
        for line_no, text in enumerate(fh, start=2):
            text = text.rstrip("\n")
            if text == "":
                raise RecordError(file, line_no, "blank line")
            try:
                yield line_no, json.loads(text)
            except json.JSONDecodeError as e:
                raise RecordError(file, line_no, "malformed JSON") from e


def iter_predictions(path: str | Path) -> Iterator[Prediction]:
    file = str(path)
    for line_no, raw in iter_predictions_raw(path):
        yield parse_prediction(Prediction, raw, file, line_no)


def check_bound(path: str | Path, truth_path: str | Path) -> PredictionHeader:
    """The header, after checking its digest names the truth file."""
    header = read_prediction_header(path)
    digest = file_digest(truth_path)
    if header.dataset_digest != digest:
        raise RecordError(
            str(path), 1, f"dataset_digest {header.dataset_digest} does not match {truth_path}"
        )
    return header
