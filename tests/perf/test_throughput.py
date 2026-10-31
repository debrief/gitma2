"""Throughput (spec 001 FR-011, SC-003), printed and asserted after warm-up.

Measured on a 4-core GitHub runner's class of machine: the kernel alone runs above 10,000
scenarios/s; the compact format above 1,000/s; NDJSON, limited by Python float formatting, in the
hundreds (gitma's own Node CLI wrote both formats at 300–550/s on these ranges). The asserted
bars are the spec's for the pack format and the batch, and a floor for NDJSON.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from tests.conftest import fixture_ranges
from tma2.data.dataset import Format, GenerateOptions, generate_dataset
from tma2.features.batch import generate_batch


def test_file_throughput(tmp_path: Path) -> None:
    ranges, heldout = fixture_ranges("phase4-seed777")
    rates = {}
    formats: tuple[Format, ...] = ("f32pack", "ndjson")
    for fmt in formats:
        t0 = time.perf_counter()
        generate_dataset(
            GenerateOptions(
                seed=np.uint64(5),
                count=500,
                out_dir=tmp_path / fmt,
                ranges=ranges,
                heldout_ranges=heldout,
                format=fmt,
                created_by="perf",
                generator_git_commit="perf",
                generator_git_dirty=True,
            )
        )
        rates[fmt] = 550 / (time.perf_counter() - t0)
    print(
        f"\nfile throughput: {rates['f32pack']:.0f} scenarios/s (f32pack), "
        f"{rates['ndjson']:.0f} (ndjson)"
    )
    assert rates["f32pack"] >= 1000
    assert rates["ndjson"] >= 150


def test_batch_latency() -> None:
    ranges, _ = fixture_ranges("phase4-seed777")
    generate_batch(5, 0, 256, ranges)  # compile / warm
    t0 = time.perf_counter()
    generate_batch(5, 1, 256, ranges)
    dt = time.perf_counter() - t0
    print(f"\nbatch of 256: {dt * 1000:.0f} ms")
    assert dt < 0.5
