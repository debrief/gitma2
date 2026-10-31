"""The inspection format: line 1 ``DatasetHeader``, then one ``Scenario`` per line.

Ported from gitma ``packages/data/src/ndjson.ts``; files are interchangeable between the two.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tma2.types import DatasetHeader, RecordError, Scenario, dump_record, parse_record

from .canonical import canonical_json, scenario_json
from .io import AtomicFile
from .versions import check_versions


class NdjsonWriter:
    """Writes the header first, then scenarios; ``close`` checks the count and commits."""

    def __init__(self, path: str | Path, header: DatasetHeader) -> None:
        self.path = str(path)
        self.header = header
        self.file = AtomicFile(path)
        self.file.write((canonical_json(dump_record(header)) + "\n").encode("utf-8"))
        self.written = 0

    def write(self, scenario: Scenario) -> None:
        self.write_record(dump_record(scenario))

    def write_record(self, record: dict[str, Any]) -> None:
        """Write an already-dumped scenario dict."""
        self.write_text(scenario_json(record))

    def write_text(self, line: str) -> None:
        """Write one pre-serialised canonical scenario line (the generator's fast path)."""
        self.file.write((line + "\n").encode("utf-8"))
        self.written += 1

    def close(self) -> None:
        if self.written != self.header.scenario_count:
            self.file.abort()
            raise RuntimeError(f"{self.path}: wrote {self.written} of {self.header.scenario_count}")
        self.file.commit()

    def abort(self) -> None:
        self.file.abort()


@dataclass
class Dataset:
    header: DatasetHeader
    scenarios: Any  # Callable[[], Iterator[Scenario]]


def _parse_json(file: str, line: int, text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RecordError(file, line, "malformed JSON (truncated or corrupted file?)") from e


def read_ndjson_header(path: str | Path) -> DatasetHeader:
    """The validated header (line 1); opens and closes the file."""
    file = str(path)
    with open(file, encoding="utf-8") as fh:
        first = fh.readline()
    if first == "":
        raise RecordError(file, 1, "empty file")
    header = parse_record(DatasetHeader, _parse_json(file, 1, first.rstrip("\n")), file, 1)
    check_versions(file, header.schema_version, header.generator_version)
    return header


def iter_ndjson_raw(
    path: str | Path, header: DatasetHeader
) -> Iterator[tuple[int, dict[str, Any]]]:
    """(line number, raw scenario dict) for every scenario line; the file is closed on exit."""
    file = str(path)
    count = 0
    with open(file, encoding="utf-8") as fh:
        fh.readline()
        for line_no, text in enumerate(fh, start=2):
            text = text.rstrip("\n")
            if text == "":
                raise RecordError(file, line_no, "blank line")
            yield line_no, _parse_json(file, line_no, text)
            count += 1
    if count != header.scenario_count:
        raise RecordError(
            file, "end", f"header declares {header.scenario_count} scenarios, file has {count}"
        )


def read_ndjson_raw(path: str | Path) -> tuple[DatasetHeader, Iterator[tuple[int, dict[str, Any]]]]:
    """Header plus an iterator of (line number, raw scenario dict), validated as JSON only."""
    header = read_ndjson_header(path)
    return header, iter_ndjson_raw(path, header)


def read_ndjson(path: str | Path) -> Dataset:
    """Validated header and a scenario iterator factory (gitma ``readNdjson``)."""
    header = read_ndjson_header(path)
    file = str(path)

    def scenarios() -> Iterator[Scenario]:
        for line_no, raw in iter_ndjson_raw(path, header):
            yield parse_record(Scenario, raw, file, line_no)

    return Dataset(header=header, scenarios=scenarios)
