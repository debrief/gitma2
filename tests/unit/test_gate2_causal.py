"""E is causal per prefix (spec 007 T011, FR-023): its output at row k does not depend on rows
after k. E-w alone: the scenario cut to rows 0 … k and padded back to its length (zeroed later
rows). E end to end (E-s's segmentation, then E-w): every row after k replaced by noise at the
same length."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch

from tma2.cli.oracle import inputs_for
from tma2.data.f32pack import iter_pack_raw
from tma2.gate2.es import ESSettings, make_net
from tma2.gate2.inputs import code_channel, prefix_inputs
from tma2.gate2.model import EWeights
from tma2.gate2.predict import e_rows, es_segmentations
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.segment import STEADY, TRANSITION, Interval
from tma2.segment.evidence import CHANNELS
from tma2.segment.score import g5_rows
from tma2.types.generated.tma import PhysicsModelConfig

from .test_gate2_model import _cfg
from .test_gate2_predict import ENCODER, _params


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


def test_e_end_to_end_ignores_later_rows(man2_pack: Path) -> None:
    """E-s's segmentation and E's prediction at row k (``es_segmentations`` then ``e_rows``, the
    ``tma2-g2predict`` path) are unchanged when every bearing and ownship sample after k is
    replaced by noise at the same length (Gate 2 panel, pre-test causality audit)."""
    torch.set_default_dtype(torch.float64)
    p = _params()
    _, m, own, _tgt, obs = next(
        x for x in iter_pack_raw(man2_pack) if int(x[1]["samples"]) <= 420 and x[1]["manoeuvres"]
    )
    ks = g5_rows(m, own.shape[0])[:2]
    assert ks
    torch.manual_seed(5)
    net = make_net(ESSettings(width=8, dilations=(1, 2)), CHANNELS)
    model = EWeights(PhysicsModelConfig.model_validate(ENCODER)).double()
    for mod in (net, model):
        for w in mod.parameters():
            torch.nn.init.normal_(w, std=0.1)  # non-zero: evidence and weights both move

    def run(o: np.ndarray, b: np.ndarray, rows: list[int]) -> tuple[dict[int, Any], list[Any]]:
        d = bearing_data_from_arrays(m, o, b)
        sg = es_segmentations(net, [d], [o], [rows], p)
        return sg[0], e_rows(model, [d], [rows], sg, p.mode, p.open_handover)[0]

    sg0, r0 = run(own, obs, ks)
    rng = np.random.default_rng(7)
    n = own.shape[0]
    for q, k in enumerate(ks):
        own2, obs2 = own.copy(), obs.copy()
        obs2[k + 1 :, 1] = rng.uniform(0, 2 * np.pi, n - k - 1).astype(np.float32)
        obs2[k + 1 :, 2] = 1
        own2[k + 1 :, 1:3] += rng.normal(0, 3000, (n - k - 1, 2)).astype(np.float32)
        own2[k + 1 :, 3] = rng.uniform(0, 2 * np.pi, n - k - 1).astype(np.float32)
        own2[k + 1 :, 4] = rng.uniform(1, 10, n - k - 1).astype(np.float32)
        sg1, r1 = run(own2, obs2, ks)
        assert sg1[k] == sg0[k]
        assert r1[q] == r0[q]
