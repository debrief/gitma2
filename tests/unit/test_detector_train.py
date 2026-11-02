"""Detector training: resumes to the same weights; heads come alive; throughput (FR-019–FR-021)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from tests.conftest import fixture_dir
from tests.unit.test_detector import config
from tma2.data.f32pack import read_pack_header
from tma2.data.io import file_digest
from tma2.models.detector_train import scored_rows
from tma2.models.train import Checkpoint, batch_from_pack
from tma2.types import dump_record
from tma2.types.generated.tma import DatasetRef, DetectorVariant, TrainingPlan

DATA = fixture_dir("phase4-seed777")


def _plan(tmp: Path, variant: DetectorVariant = DetectorVariant.causal) -> Path:
    ranges = json.loads((DATA / "ranges.json").read_text())
    pack = DATA / "validation.f32pack"
    det = config(variant).model_copy(
        update={"iterations": 10, "train_iterations": 5, "epochs": 2, "patience": 5, "threads": 1}
    )
    plan = TrainingPlan(
        id="det-plan",
        ranges=ranges,
        train_seed=99,
        scenarios_per_epoch=8,
        validation=DatasetRef(
            path=str(pack), header=read_pack_header(pack), digest=file_digest(pack)
        ),
        validation_scenarios=6,
        detectors=[det],
        decision="none",
    )
    p = tmp / "plan.json"
    p.write_text(json.dumps(dump_record(plan)))
    return p


def test_scored_rows_include_a_g5_row() -> None:
    b = batch_from_pack(Path(DATA / "validation.f32pack"), 20)
    rows = scored_rows(b, np.random.default_rng(0), 2)
    for s in range(len(b)):
        zig, n = int(b.zig_index[s]), int(b.samples[s])
        ks = [int(k) for k in rows[s] if k >= 0]
        assert all(zig < k < n for k in ks) and ks == sorted(set(ks))
        g5 = {zig + 30 * m for m in (1, 2, 3, 4)} & set(range(n))
        if g5:
            assert set(ks) & g5


def _train_in_process(plan: Path, ck: Path, epochs: int) -> None:
    """One training job in a fresh interpreter, as a chained runner job is: within one process,
    a second run can differ from the first in the last bits (allocator state; measured 1e-16 in
    layer-norm weights), while separate processes are byte-identical."""
    code = (
        "import sys; from tma2.models.detector_train import train_detector; "
        "train_detector(sys.argv[1], 'det-test', sys.argv[2], sys.argv[3], "
        "epochs=int(sys.argv[4]), log=lambda *_: None)"
    )
    subprocess.run(
        [sys.executable, "-c", code, str(plan), str(ck), str(DATA), str(epochs)], check=True
    )


def test_detector_resumed_run_equals_uninterrupted(tmp_path: Path) -> None:
    for variant in (DetectorVariant.causal, DetectorVariant.time_late):
        plan = _plan(tmp_path, variant)
        a, b = tmp_path / f"a-{variant.value}", tmp_path / f"b-{variant.value}"
        _train_in_process(plan, a, 2)
        _train_in_process(plan, b, 1)  # stops after one epoch
        _train_in_process(plan, b, 2)  # resumes
        meta = Checkpoint(b).load_meta()
        assert meta.epoch == 2 and len(meta.jobs or []) == 2
        assert meta.weights_digest == file_digest(b / "best.safetensors")
        assert all(np.isfinite(v) for v in meta.val_losses or [])
        assert file_digest(a / "weights.safetensors") == file_digest(b / "weights.safetensors")
        names = {h.head for h in meta.liveness or []}
        assert names == {"now", "w_change", "p_kind"}


def test_local_step_throughput(tmp_path: Path, capsys: object) -> None:
    """Records the local cost of one training batch at the plan's shape (8 knots, K = 50, two
    downstream rows); the runner budget is checked by the bench workflow (T021)."""
    import torch

    from tma2.features.batch import generate_batch
    from tma2.models.detector import Detector
    from tma2.models.detector_train import detector_batch, step_loss
    from tma2.physics.layer import PhysicsLayer

    ranges = json.loads((DATA / "ranges.json").read_text())
    cfg = config().model_copy(update={"width": 64, "layers": 2, "heads": 4, "feedforward": 128})
    torch.manual_seed(0)
    model = Detector(cfg).double()
    layer = PhysicsLayer(iterations=50, knots=8, implicit=True)
    batch = generate_batch(311, 0, 16, ranges)
    t0 = time.time()
    xb = detector_batch(batch, cfg, np.random.default_rng(0))
    t1 = time.time()
    lp, _ = step_loss(model, layer, xb, cfg)
    lp.total.backward()  # type: ignore[no-untyped-call]
    t2 = time.time()
    print(
        f"\nper scenario: inputs {1000 * (t1 - t0) / 16:.1f} ms, "
        f"step {1000 * (t2 - t1) / 16:.1f} ms ({lp.downstream_rows} downstream rows)"
    )
    assert lp.downstream_rows > 0
