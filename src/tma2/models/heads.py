"""Model heads and their liveness (spec 004 R1, Gate 1 panel follow-up).

A head is Linear → activation → zero-initialised Linear, so an untrained model outputs zeros from
every head. Gate 1's heads used ReLU and ended with no active hidden unit: a ReLU unit whose input
stays negative has zero gradient for every input and never recovers. From spec 004 every head uses
tanh, whose derivative is never zero; ``relu`` remains so Gate 1's committed weights load and
re-score unchanged. The module layout (indices 0, 1, 2) is the same for both, so state-dict keys do
not change.

``liveness`` measures, on a batch of inputs, the share of hidden units whose activation varies
across rows and the spread of the head's output across rows; the training loop records both after
every epoch, and a test asserts their floors (a model with dead heads fails it).
"""

from __future__ import annotations

import torch
from torch import Tensor, nn

from tma2.types.generated.tma import HeadActivation, HeadLiveness

ALIVE_DELTA = 1e-3  # a hidden unit is alive if its activation varies by more than this across rows
ALIVE_SHARE_FLOOR = 0.5
OUTPUT_SD_FLOOR = 1e-3


def zero_linear(n_in: int, n_out: int) -> nn.Linear:
    lin = nn.Linear(n_in, n_out)
    nn.init.zeros_(lin.weight)
    nn.init.zeros_(lin.bias)
    return lin


def head(n_in: int, n_out: int, activation: HeadActivation | None) -> nn.Sequential:
    """Linear(n_in, n_in) → activation → zero-initialised Linear(n_in, n_out); absent = relu."""
    act: nn.Module = nn.Tanh() if activation == HeadActivation.tanh else nn.ReLU()
    return nn.Sequential(nn.Linear(n_in, n_in), act, zero_linear(n_in, n_out))


@torch.no_grad()
def liveness(name: str, module: nn.Sequential, x: Tensor) -> HeadLiveness:
    """Alive share of the hidden units and the mean (over outputs) of the output's standard
    deviation across rows, on inputs ``x`` [..., n_in] (flattened over the leading axes)."""
    flat = x.reshape(-1, x.shape[-1])
    hidden = module[1](module[0](flat))
    spread = hidden.max(dim=0).values - hidden.min(dim=0).values
    out = module(flat)
    sd = out.std(dim=0).mean() if flat.shape[0] > 1 else torch.zeros(())
    return HeadLiveness(
        head=name,
        alive_share=float((spread > ALIVE_DELTA).to(torch.float64).mean()),
        output_sd=float(sd),
    )


def is_alive(rec: HeadLiveness) -> bool:
    return rec.alive_share >= ALIVE_SHARE_FLOOR and rec.output_sd >= OUTPUT_SD_FLOOR
