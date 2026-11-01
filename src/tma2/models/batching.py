"""Torch inputs for the Gate 1 model from :mod:`tma2.models.rows` arrays (double precision)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from .gate1 import Gate1Model, ModelOutput
from .rows import RowBatch, ScenarioTensors


@dataclass
class ModelInputs:
    bearing: Tensor
    valid: Tensor
    ox: Tensor
    oy: Tensor
    t: Tensor
    sigma: Tensor
    n_rows: Tensor
    source: Tensor
    k: Tensor
    theta_grid: Tensor
    truth: Tensor
    bound_cov: Tensor

    def okx(self) -> Tensor:
        return self.ox[self.source, self.k]

    def oky(self) -> Tensor:
        return self.oy[self.source, self.k]


def model_inputs(tensors: ScenarioTensors, rows: RowBatch, samples: np.ndarray) -> ModelInputs:
    """``samples`` [S]: rows in each (scenario, draw) window."""
    f = torch.float64

    def d(a: np.ndarray) -> Tensor:
        return torch.from_numpy(np.ascontiguousarray(a, dtype=np.float64)).to(f)

    def i(a: np.ndarray) -> Tensor:
        return torch.from_numpy(np.ascontiguousarray(a, dtype=np.int64))

    return ModelInputs(
        bearing=d(tensors.bearing),
        valid=d(tensors.valid),
        ox=d(tensors.ox),
        oy=d(tensors.oy),
        t=d(tensors.t),
        sigma=d(tensors.sigma),
        n_rows=i(samples),
        source=i(rows.source),
        k=i(rows.k),
        theta_grid=d(rows.theta_grid),
        truth=d(rows.truth),
        bound_cov=d(rows.bound_cov),
    )


def run(model: Gate1Model, x: ModelInputs) -> ModelOutput:
    out: ModelOutput = model(
        x.bearing, x.valid, x.ox, x.oy, x.t, x.sigma, x.n_rows, x.source, x.k, x.theta_grid
    )
    return out
