"""The learned calibration (spec 008 research R5).

s = bound · tanh(MLP(x)), with x the row's features (``calib.data``): E-w's encoder state at the
row, the raw log standard deviations of log range, course and speed, and C's code. The MLP has
one hidden tanh layer, and its output layer starts at zero, so an untrained head is the identity
(s = 0, the raw covariance). Form ``scalar``: one s, the covariance times e^(2s); form ``local``
(research R5 as amended): four, the standard deviations of log range, bearing, speed and course
times e^(s_i), correlations kept (``physics.uncertainty.local_rescale``).
"""

from __future__ import annotations

import torch
from torch import Tensor, nn

from tma2.types.generated.tma import CalibrationForm, CalibrationHeadConfig


def outputs(form: CalibrationForm | None) -> int:
    """How many log-scales a form has: 1 (scalar, the default) or 4 (local)."""
    return 4 if form == CalibrationForm.local else 1


class CalHead(nn.Module):
    def __init__(self, cfg: CalibrationHeadConfig, inputs: int) -> None:
        super().__init__()
        self.bound = float(cfg.bound)
        self.hidden = nn.Linear(inputs, cfg.width)
        self.out = nn.Linear(cfg.width, outputs(cfg.form))
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x: Tensor) -> Tensor:
        """[N, F] → [N, m] log-scales s (m = 1 scalar, 4 local)."""
        h = torch.tanh(self.hidden(x))
        return self.bound * torch.tanh(self.out(h))
