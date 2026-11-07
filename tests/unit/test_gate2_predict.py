"""E's predictions (spec 007 T020): untrained weights reproduce C. Untrained E-w gives C's
physics-layer errors on C's segmentation (the scorer's path); untrained E-s gives C's
segmentation (zero evidence through the confirmation's evidence path)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from tma2.data.f32pack import iter_pack_raw
from tma2.eval.errors import Truth, row_error
from tma2.gate2 import KNOTS
from tma2.gate2.es import ESSettings, make_net
from tma2.gate2.model import EWeights
from tma2.gate2.predict import e_rows, es_segmentations
from tma2.physics.layer import PhysicsLayer
from tma2.physics.reference import ITERATIONS
from tma2.references.classical import bearing_data_from_arrays
from tma2.segment import STEADY, TRANSITION, Interval
from tma2.segment.evidence import CHANNELS
from tma2.segment.score import Row, from_segmentations, g5_rows, layer_errors
from tma2.segment.segmenter import segment
from tma2.types.generated.tma import PhysicsModelConfig, SegmentParameters

ROOT = Path(__file__).resolve().parents[2]
ENCODER = {
    "head": "physics",
    "causal": True,
    "width": 8,
    "layers": 1,
    "heads": 2,
    "feedforward": 16,
    "weight_bound": 3.0,
    "scale_bound": 2.0,
    "iterations": ITERATIONS,
    "head_activation": "tanh",
    "loss_init_weight": 0.1,
    "loss_nll_weight": 0.0,
    "nll_beta": 0.5,
    "loss_cap": 100.0,
    "rows_per_scenario": 4,
    "noise_draws": 1,
    "batch_scenarios": 4,
    "learning_rate": 1e-3,
    "weight_decay": 0.0,
    "epochs": 2,
    "patience": 3,
    "shuffle_labels": False,
    "threads": 1,
    "id": "e",
    "seed": 1,
}


def _params() -> SegmentParameters:
    plan = ROOT / "configs" / "segment" / "gs-plan.json"
    return SegmentParameters(**json.loads(plan.read_text())["segmenter"]["parameters"])


def test_untrained_ew_is_c(man2_pack: Path) -> None:
    torch.set_default_dtype(torch.float64)
    p = _params()
    data, metas, rows, segs, truths, owns = [], [], [], {}, {}, []
    for j, (_, m, own, tgt, obs) in enumerate(iter_pack_raw(man2_pack)):
        if j >= 3:
            break
        d = bearing_data_from_arrays(m, own, obs)
        ks = g5_rows(m, d.n)
        if not ks:
            continue
        for q, k in enumerate(ks):  # a transition open at the second row exercises the hand-over
            z = int(m["zig_index"])
            segs[(j, k)] = (
                [Interval(STEADY, 0, z - 1), Interval(TRANSITION, z, k, True)]
                if q == 1 and k - z < 30
                else [Interval(STEADY, 0, k)]
            )
        data.append((j, d))
        metas.append(m)
        rows.append(ks)
        owns.append(own)
        truths[j] = Truth.from_block(m, own, tgt)
    model = EWeights(PhysicsModelConfig.model_validate(ENCODER)).double()
    ds = [d for _, d in data]
    sg = [{k: segs[(j, k)] for k in ks} for (j, _), ks in zip(data, rows, strict=True)]
    got = e_rows(model, ds, rows, sg, p.mode, p.open_handover)
    want = layer_errors(
        PhysicsLayer(knots=KNOTS),
        [Row(j, k, False) for (j, _), ks in zip(data, rows, strict=True) for k in ks],
        dict(data),
        {j: m for (j, _), m in zip(data, metas, strict=True)},
        truths,
        from_segmentations(segs, p.mode, True, p.open_handover),
    )
    flat = [
        row_error(truths[j], r, "plausible")
        for (j, _), rs in zip(data, got, strict=True)
        for r in rs
    ]
    e = np.array([(x.range_rel, x.course_deg, x.speed_kt) for x in flat])
    assert e.shape == want.shape and np.isfinite(want).any()
    fin = np.isfinite(want)
    assert (np.isfinite(e) == fin).all()
    np.testing.assert_allclose(e[fin], want[fin], rtol=1e-9, atol=1e-9)


def test_untrained_es_is_c(man2_pack: Path) -> None:
    torch.set_default_dtype(torch.float64)
    p = _params()
    _, m, own, _tgt, obs = next(
        x for x in iter_pack_raw(man2_pack) if int(x[1]["samples"]) <= 420 and x[1]["manoeuvres"]
    )
    d = bearing_data_from_arrays(m, own, obs)
    ks = g5_rows(m, d.n)[:2]
    assert ks
    want = segment(PhysicsLayer(), [d], [m], [ks], p)[0]
    net = make_net(ESSettings(width=8, dilations=(1, 2)), CHANNELS)
    got = es_segmentations(net, [d], [own], [ks], p)[0]
    assert [got[s.k] for s in want] == [s.intervals for s in want]


@pytest.mark.parametrize("kind,given,ok", [("e", ("es",), False), ("ew", ("ew", "es"), False)])
def test_g2predict_refuses_wrong_weights(
    tmp_path: Path, kind: str, given: tuple[str, ...], ok: bool
) -> None:
    from tma2.cli.g2predict import main
    from tma2.segment.codeid import code_digest

    seg = tmp_path / "c.ndjson"
    seg.write_text(json.dumps({"segmenter_sha256": "a", "code_sha256": code_digest()}) + "\n")
    plan = tmp_path / "plan.json"
    c = {"parameters_sha256": "a", "code_sha256": code_digest(), "mode": "gap"}
    plan.write_text(json.dumps({"c": c, "models": {"m": {"kind": kind, "seed": 1}}}))
    w = tmp_path / "w.safetensors"
    w.write_bytes(b"x")
    args = ["--in", "x", "--segmentations", str(seg), "--plan", str(plan), "--model", "m"]
    for g in given:
        args += [f"--{g}-weights", str(w)]
    out = tmp_path / "p.ndjson"
    assert main([*args, "--start", "0", "--count", "1", "--out", str(out)]) == 2
    assert not out.exists()


def test_zig_veto_control(man2_pack: Path) -> None:
    """The control C′ (Gate 2 panel, round 1): the evidence covers exactly the zig ± window
    rows; an empty window is C. (The veto is E-s's largest shift, +τ/2, not a ban.)"""
    from tma2.gate2.predict import veto_segmentations, zig_veto_evidence

    p = _params()
    _, m, own, _tgt, obs = next(
        x for x in iter_pack_raw(man2_pack) if int(x[1]["samples"]) <= 420 and x[1]["manoeuvres"]
    )
    d = bearing_data_from_arrays(m, own, obs)
    ks = g5_rows(m, d.n)[:2]
    assert ks
    e = zig_veto_evidence(d, 6)
    z = int(d.zig_index)
    assert (e[z - 6 : z + 7] > 0).all() and e[: z - 6].sum() == 0 and e[z + 7 :].sum() == 0
    want = segment(PhysicsLayer(), [d], [m], [ks], p)[0]
    got = veto_segmentations([d], [ks], p, -1)[0]
    assert [got[s.k] for s in want] == [s.intervals for s in want]
    assert set(veto_segmentations([d], [ks], p, 6)[0]) == set(ks)
