"""Compile the training data path's numba kernels (generator batch and row kernel) once, so the
first epoch's time excludes compilation (CI; spec 003)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tma2.features.batch import generate_batch
from tma2.models.rows import row_batch, scenario_tensors

ranges = json.loads(Path("tests/fixtures/gitma/iter4-seed777/ranges.json").read_text())
b = generate_batch(1, 0, 4, ranges)
row_batch(b, scenario_tensors(b, 1, 1), np.random.default_rng(0), 2)
print("numba kernels compiled")
