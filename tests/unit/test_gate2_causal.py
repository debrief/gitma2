"""E is causal per prefix (spec 007 T011, FR-023): its output at row k does not change when the
scenario is cut to rows 0 … k (arrays truncated, not masked)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from tma2.cli.oracle import inputs_for
from tma2.data.f32pack import iter_pack_raw
from tma2.gate2.inputs import code_channel, prefix_inputs
from tma2.gate2.model import EWeights
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment import STEADY, TRANSITION, Interval

from .test_gate2_model import _cfg


def _cut(d: BearingData, k: int) -> BearingData:
    return BearingData(
        t=d.t[: k + 1].copy(),
        ox=d.ox[: k + 1].copy(),
        oy=d.oy[: k + 1].copy(),
        z=d.z[: k + 1].copy(),
        valid=d.valid[: k + 1].copy(),
        zig_index=d.zig_index,
        sigma=d.sigma,
        index=d.index,
    )


def test_output_at_k_ignores_later_rows(man2_pack: Path) -> None:
    torch.set_default_dtype(torch.float64)
    _, m, own, _tgt, obs = next(iter(iter_pack_raw(man2_pack)))
    d = bearing_data_from_arrays(m, own, obs)
    k = min(d.n - 50, int(m["zig_index"]) + 60)
    ivs = [Interval(STEADY, 0, k - 21), Interval(TRANSITION, k - 20, k, True)]  # open at k
    torch.manual_seed(3)
    model = EWeights(_cfg()).double()
    for p in model.parameters():
        torch.nn.init.normal_(p, std=0.05)
    outs = []
    for dd in (d, _cut(d, k)):
        inp = prefix_inputs(dd, k, ivs, "gap", None)
        assert inp is not None
        code = torch.tensor(np.pad(code_channel(ivs, k, dd.n), (0, d.n - dd.n)))[None]
        with torch.no_grad():
            outs.append(model(inputs_for([(dd, k, inp)], d.n), code).state.numpy())
    np.testing.assert_array_equal(outs[0], outs[1])
