"""The whole-period model on stored periods (spec 016 FR-009, FR-015): its per-token output,
on CPU, and its ONNX export with the check that the exported model agrees with the trained one.

Float32 throughout (no double anywhere in the graph, so the attention and GELU kernels that
onnxruntime lacks in double do not arise). The exported graph takes the features and the row
mask of periods padded to the model's ``max_rows``, with a dynamic batch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import torch
from torch import Tensor, nn

from .model import Regressor
from .period_data import inputs_of

if TYPE_CHECKING:
    from tma2.timelate.periods import Period

OPSET = 17
INPUTS = ("features", "mask")
OUTPUTS = ("mean", "logvar", "logit")


@dataclass
class PeriodOutput:
    mean: np.ndarray  # [T, 3] at each token's last existing row (frame of regress.frame)
    logvar: np.ndarray  # [T, 3]
    prob: np.ndarray  # [T] probability that a target manoeuvre is in progress


class PeriodExport(nn.Module):
    """The model as exported: (features [B, R, F], mask [B, R]) → mean, log-variance, logit."""

    def __init__(self, model: Regressor) -> None:
        super().__init__()
        self.model = model

    def forward(self, f: Tensor, mask: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        return self.model.forward_all(f, 0, mask)


def run_model(model: Regressor, f: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, ...]:
    """(mean, logvar, logit) of the trained model on CPU in float32."""
    model.eval()
    with torch.no_grad():
        out = model.forward_all(torch.from_numpy(f), 0, torch.from_numpy(mask))
    return tuple(o.float().numpy() for o in out)


def predict_periods(model: Regressor, periods: list[Period], batch: int = 16) -> list[PeriodOutput]:
    """The model's output for each period's own tokens (bearings, ownship and the stated sigma
    are all it reads)."""
    patch = model.patch
    res: list[PeriodOutput] = []
    for s in range(0, len(periods), batch):
        part = periods[s : s + batch]
        f, mask, _th = inputs_of(part, model.cfg.max_rows)
        mean, logvar, logit = run_model(model, f, mask)
        for i, p in enumerate(part):
            t = -(-p.rows // patch)
            prob = 1.0 / (1.0 + np.exp(-logit[i, :t].astype(np.float64)))
            res.append(PeriodOutput(mean[i, :t], logvar[i, :t], prob))
    return res


def export_onnx(model: Regressor, path: Path) -> None:
    """Write the model as ONNX (legacy exporter, opset 17, dynamic batch, fixed rows)."""
    cfg = model.cfg
    wrapper = PeriodExport(model).eval()
    f = torch.zeros(2, cfg.max_rows, cfg.n_features, dtype=torch.float32)
    mask = torch.zeros(2, cfg.max_rows, dtype=torch.bool)
    mask[0, : cfg.max_rows // 2] = True
    mask[1] = True
    prev = torch.get_default_dtype()
    torch.set_default_dtype(torch.float32)  # the exporter's scalar constants follow the default
    try:
        # gradients stay enabled: under no_grad the encoder takes its fused fast path, one
        # operator the exporter does not know
        torch.onnx.export(
            wrapper,
            (f, mask),
            str(path),
            input_names=list(INPUTS),
            output_names=list(OUTPUTS),
            dynamic_axes={name: {0: "batch"} for name in (*INPUTS, *OUTPUTS)},
            opset_version=OPSET,
            dynamo=False,
        )
    finally:
        torch.set_default_dtype(prev)


def run_onnx(path: Path, f: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, ...]:
    import onnxruntime as ort  # type: ignore[import-untyped]

    sess = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    return tuple(sess.run(list(OUTPUTS), {"features": f, "mask": mask}))


def export_check(model: Regressor, path: Path, f: np.ndarray, mask: np.ndarray) -> float:
    """Export, run both on (f, mask) and return the largest absolute difference over the
    tokens that exist (a padded token's output is not a statement)."""
    export_onnx(model, path)
    ref, got = run_model(model, f, mask), run_onnx(path, f, mask)
    exists = mask[:, :: model.patch]
    return max(float(np.abs(a[exists] - b[exists]).max()) for a, b in zip(ref, got, strict=True))
