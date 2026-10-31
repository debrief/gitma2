"""The training format (``TMAPACK``), ported from gitma ``packages/data/src/f32pack.ts``.

All little-endian: magic ``TMAPACK\\0`` | u32 format version | u32 header length H | header JSON
| u32 N | u64 × (N+1) block offsets | blocks. Block: u32 M | metadata JSON (M bytes, space-padded
to 4) | u32 S | f32 ownship[S×5] | f32 target[S×5] | f32 observations[S×3].
"""

from __future__ import annotations

import json
import struct
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from tma2.types import (
    DatasetHeader,
    RecordError,
    Scenario,
    ScenarioMetadata,
    dump_record,
    parse_record,
)

from .canonical import canonical_json
from .io import AtomicFile
from .ndjson import Dataset
from .versions import check_versions

MAGIC = b"TMAPACK\0"
PACK_FORMAT_VERSION = 1
STATE_FIELDS = 5
OBS_FIELDS = 3


def _padded_json(value: Any) -> bytes:
    raw = canonical_json(value).encode("utf-8")
    pad = (4 - len(raw) % 4) % 4
    return raw + b" " * pad


def _u32(n: int) -> bytes:
    return struct.pack("<I", n)


def encode_block_arrays(
    metadata: dict[str, Any], own: np.ndarray, tgt: np.ndarray, obs: np.ndarray
) -> bytes:
    """Encode one block from arrays ``own``/``tgt`` [S, 5] and ``obs`` [S, 3] (float32)."""
    meta = _padded_json(metadata)
    n = int(metadata["samples"])
    if (
        own.shape != (n, STATE_FIELDS)
        or tgt.shape != (n, STATE_FIELDS)
        or obs.shape != (n, OBS_FIELDS)
    ):
        raise ValueError(f"scenario {metadata.get('index')}: length mismatch")
    body = np.concatenate([own.ravel(), tgt.ravel(), obs.ravel()]).astype("<f4").tobytes()
    return _u32(len(meta)) + meta + _u32(n) + body


def encode_block(scenario: Scenario) -> bytes:
    """Encode one scenario (gitma ``encodeBlock``)."""
    n = scenario.metadata.samples
    own = np.array(
        [[s.timestamp_s, s.x_m, s.y_m, s.course_rad, s.speed_mps] for s in scenario.ownship.states],
        dtype=np.float32,
    ).reshape(n, STATE_FIELDS)
    tgt = np.array(
        [[s.timestamp_s, s.x_m, s.y_m, s.course_rad, s.speed_mps] for s in scenario.target.states],
        dtype=np.float32,
    ).reshape(n, STATE_FIELDS)
    obs = np.array(
        [[o.timestamp_s, o.bearing_rad, 1.0 if o.valid else 0.0] for o in scenario.observations],
        dtype=np.float32,
    ).reshape(n, OBS_FIELDS)
    return encode_block_arrays(dump_record(scenario.metadata), own, tgt, obs)


class PackWriter:
    """Writes header and a zeroed offset table, then blocks; patches the table on ``close``."""

    def __init__(self, path: str | Path, header: DatasetHeader) -> None:
        self.path = str(path)
        self.n = header.scenario_count
        self.file = AtomicFile(path)
        header_json = _padded_json(dump_record(header))
        prefix = (
            MAGIC + _u32(PACK_FORMAT_VERSION) + _u32(len(header_json)) + header_json + _u32(self.n)
        )
        self.file.write(prefix)
        self.table_pos = len(prefix)
        self.file.write(b"\0" * (8 * (self.n + 1)))
        self.pos = self.table_pos + 8 * (self.n + 1)
        self.offsets = np.zeros(self.n + 1, dtype="<u8")
        self.i = 0

    def write(self, scenario: Scenario) -> None:
        self.write_block(encode_block(scenario))

    def write_block(self, block: bytes) -> None:
        if self.i >= self.n:
            raise RuntimeError(f"{self.path}: more scenarios than header declares")
        self.offsets[self.i] = self.pos
        self.i += 1
        self.file.write(block)
        self.pos += len(block)

    def close(self) -> None:
        if self.i != self.n:
            self.file.abort()
            raise RuntimeError(f"{self.path}: wrote {self.i} of {self.n}")
        self.offsets[self.n] = self.pos
        self.file.write_at(self.table_pos, self.offsets.tobytes())
        self.file.commit()

    def abort(self) -> None:
        self.file.abort()


def _read_header(path: str, data: bytes) -> tuple[DatasetHeader, int, np.ndarray]:
    if len(data) < 16 or data[:8] != MAGIC:
        raise RecordError(path, "header", "not a .f32pack file (bad magic)")
    version, h = struct.unpack_from("<II", data, 8)
    if version != PACK_FORMAT_VERSION:
        raise RecordError(path, "header", f"unsupported pack format version {version}")
    if len(data) < 16 + h + 4:
        raise RecordError(path, "header", "truncated header")
    try:
        raw = json.loads(data[16 : 16 + h].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RecordError(path, "header", "corrupted header JSON") from e
    header = parse_record(DatasetHeader, raw, path, "header")
    check_versions(path, header.schema_version, header.generator_version)
    (n,) = struct.unpack_from("<I", data, 16 + h)
    if n != header.scenario_count:
        raise RecordError(path, "header", "scenario count does not match header")
    table_pos = 16 + h + 4
    if len(data) < table_pos + 8 * (n + 1):
        raise RecordError(path, "header", "truncated offsets")
    offsets = np.frombuffer(data, dtype="<u8", count=n + 1, offset=table_pos)
    if int(offsets[n]) != len(data):
        raise RecordError(path, "end", f"file is {len(data)} bytes, expected {int(offsets[n])}")
    return header, n, offsets


def decode_block_raw(
    path: str, index: int, buf: bytes
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    """Raw metadata dict and float32 arrays own [S,5], tgt [S,5], obs [S,3]."""
    where = f"scenario {index}"
    if len(buf) < 8:
        raise RecordError(path, where, "truncated block")
    (m,) = struct.unpack_from("<I", buf, 0)
    if 4 + m + 4 > len(buf):
        raise RecordError(path, where, "truncated block")
    try:
        meta = json.loads(buf[4 : 4 + m].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise RecordError(path, where, "corrupted metadata JSON") from e
    metadata = parse_record(ScenarioMetadata, meta, path, where)
    (n,) = struct.unpack_from("<I", buf, 4 + m)
    start = 8 + m
    count = n * (2 * STATE_FIELDS + OBS_FIELDS)
    if n != metadata.samples or start + 4 * count != len(buf):
        raise RecordError(path, where, "block length does not match sample count")
    floats = np.frombuffer(buf, dtype="<f4", count=count, offset=start)
    own = floats[: n * STATE_FIELDS].reshape(n, STATE_FIELDS)
    tgt = floats[n * STATE_FIELDS : 2 * n * STATE_FIELDS].reshape(n, STATE_FIELDS)
    obs = floats[2 * n * STATE_FIELDS :].reshape(n, OBS_FIELDS)
    return meta, own, tgt, obs


def block_to_scenario(
    meta: dict[str, Any], own: np.ndarray, tgt: np.ndarray, obs: np.ndarray
) -> dict[str, Any]:
    """The scenario dict gitma's ``decodeBlock`` builds (floats as Python floats of float32)."""

    def track(a: np.ndarray) -> list[dict[str, float]]:
        return [
            {
                "timestamp_s": float(r[0]),
                "x_m": float(r[1]),
                "y_m": float(r[2]),
                "course_rad": float(r[3]),
                "speed_mps": float(r[4]),
            }
            for r in a
        ]

    return {
        "record": "scenario",
        "metadata": meta,
        "ownship": {"id": "ownship", "states": track(own)},
        "target": {"id": "target", "states": track(tgt)},
        "observations": [
            {"timestamp_s": float(r[0]), "bearing_rad": float(r[1]), "valid": bool(r[2] != 0)}
            for r in obs
        ],
    }


def read_pack_raw(
    path: str | Path,
) -> tuple[DatasetHeader, Iterator[tuple[int, dict[str, Any], np.ndarray, np.ndarray, np.ndarray]]]:
    """Header and an iterator of (index, metadata dict, own, tgt, obs) per block."""
    file = str(path)
    data = Path(path).read_bytes()
    header, n, offsets = _read_header(file, data)

    def blocks() -> Iterator[tuple[int, dict[str, Any], np.ndarray, np.ndarray, np.ndarray]]:
        for i in range(n):
            a, b = int(offsets[i]), int(offsets[i + 1])
            meta, own, tgt, obs = decode_block_raw(file, i, data[a:b])
            yield i, meta, own, tgt, obs

    return header, blocks()


def read_pack(path: str | Path) -> Dataset:
    """Validated header and a scenario iterator factory (gitma ``readPack``)."""
    header, _ = read_pack_raw(path)
    file = str(path)

    def scenarios() -> Iterator[Scenario]:
        _, blocks = read_pack_raw(path)
        for i, meta, own, tgt, obs in blocks:
            yield parse_record(
                Scenario, block_to_scenario(meta, own, tgt, obs), file, f"scenario {i}"
            )

    return Dataset(header=header, scenarios=scenarios)
