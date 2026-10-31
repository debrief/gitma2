"""Atomic file writes and digests (gitma ``packages/data/src/io.ts``)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import IO


class AtomicFile:
    """A file written to ``<path>.tmp-<pid>`` and renamed into place on ``commit``."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.tmp = self.path.with_name(f"{self.path.name}.tmp-{os.getpid()}")
        self.fh: IO[bytes] = open(self.tmp, "wb")  # noqa: SIM115 - closed by commit/abort

    def write(self, data: bytes) -> None:
        self.fh.write(data)

    def write_at(self, position: int, data: bytes) -> None:
        self.fh.flush()
        self.fh.seek(position)
        self.fh.write(data)
        self.fh.seek(0, os.SEEK_END)

    def tell(self) -> int:
        return self.fh.tell()

    def commit(self) -> None:
        self.fh.close()
        os.replace(self.tmp, self.path)

    def abort(self) -> None:
        self.fh.close()
        try:
            self.tmp.unlink()
        except FileNotFoundError:
            pass


def file_digest(path: str | Path) -> str:
    """SHA-256 hex digest of a file, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
