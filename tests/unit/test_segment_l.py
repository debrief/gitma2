"""Spec 005 T030–T031: L's evidence network and its hand-over to C. An untrained L equals C
exactly (SC-003); the evidence is causal."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from tma2.data.f32pack import iter_pack_raw
from tma2.detect.controls import ls_states
from tma2.physics.layer import PhysicsLayer
from tma2.references.classical import bearing_data_from_arrays, classical_predict
from tma2.segment import default_parameters, to_codes
from tma2.segment.evidence import CHANNELS, EvidenceNet, evidence_for, features, innovations
from tma2.segment.ownship import segment_ownship
from tma2.segment.segmenter import segment

P = default_parameters(search_penalty=20.0, glr_threshold=6.0)


def test_untrained_net_is_zero_and_causal() -> None:
    torch.manual_seed(0)
    net = EvidenceNet().double()
    x = torch.randn(2, CHANNELS, 200, dtype=torch.float64)
    assert float(net(x).abs().max()) == 0.0
    torch.nn.init.normal_(net.head.weight)
    y = net(x)
    x2 = x.clone()
    x2[:, :, 120:] = torch.randn(2, CHANNELS, 80, dtype=torch.float64)
    y2 = net(x2)
    assert torch.equal(y[:, :120], y2[:, :120]) and not torch.equal(y[:, 120:], y2[:, 120:])
    # a head gradient exists at zero output
    net2 = EvidenceNet().double()
    net2(x).sum().backward()
    assert net2.head.weight.grad is not None and float(net2.head.weight.grad.abs().max()) > 0


def test_untrained_l_equals_c(man2_pack: Path) -> None:
    """SC-003 on MAN2 prefixes (GLR and search nominators): identical segmentations and costs."""
    torch.set_default_dtype(torch.float64)
    data, metas, rows, feats = [], [], [], []
    for _, m, own, _tgt, obs in iter_pack_raw(man2_pack):
        n = int(m["samples"])
        if n > 420 or abs(float(m["parameters"]["noise_sigma_rad"]) - np.pi / 180) > 1e-6:
            continue
        d = bearing_data_from_arrays(m, own, obs)
        lst, lok = ls_states(d, classical_predict(d, "per_timestep")["rows"])
        oc = to_codes(segment_ownship(own[:, 3], own[:, 4], n - 1, P), n)
        feats.append(features(d, oc, innovations(d, lst, lok)))
        data.append(d)
        metas.append(m)
        rows.append([int(m["zig_index"]) + 30, n - 1 - ((n - 1 - int(m["zig_index"])) % 30)])
        if len(data) == 2:
            break
    assert len(data) == 2
    ev = evidence_for(EvidenceNet().double(), feats)
    assert all(float(np.abs(e).max()) == 0.0 for e in ev)
    layer = PhysicsLayer()
    c = segment(layer, data, metas, rows, P)
    lsg = segment(layer, data, metas, rows, P, evidence=ev)
    for a, b in zip(c, lsg, strict=True):
        for x, y in zip(a, b, strict=True):
            assert x.intervals == y.intervals and x.cost == y.cost and x.margin == y.margin
