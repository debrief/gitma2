"""E-w's training data and training (spec 007 T015): tables round-trip, one epoch trains and
writes a checkpoint bound by SHA-256, and a second job resumes it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from tma2.gate2.train import build_prefixes, load_prefixes, save_prefixes, shuffled_truth
from tma2.segment import STEADY, Interval
from tma2.segment.score import g5_rows, iter_selected

ENCODER = {
    "head": "physics",
    "causal": True,
    "width": 8,
    "layers": 1,
    "heads": 2,
    "feedforward": 16,
    "weight_bound": 3.0,
    "scale_bound": 2.0,
    "iterations": 30,
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
}


def _segs(pack: Path, n: int) -> dict[tuple[int, int], list[Interval]]:
    out = {}
    for j, m, _o, _t, _ob in iter_selected(pack, 0, n):
        for k in g5_rows(m, int(m["samples"])):
            out[(j, k)] = [Interval(STEADY, 0, k)]  # one leg: enough to exercise the path
    return out


def test_tables_round_trip_and_shuffle(man2_pack: Path, tmp_path: Path) -> None:
    xs = build_prefixes(man2_pack, _segs(man2_pack, 3), 0, 3, "gap", None)
    assert xs
    save_prefixes(tmp_path / "t.npz", xs, {"plan_sha256": "x"})
    h, ys = load_prefixes(tmp_path / "t.npz")
    assert h["plan_sha256"] == "x" and len(ys) == len(xs)
    np.testing.assert_array_equal(xs[0].lw, ys[0].lw)
    np.testing.assert_array_equal(xs[-1].bound_cov, ys[-1].bound_cov)
    sh = shuffled_truth(xs, 1)
    assert sh.shape == (len(xs), 4)


def test_train_and_resume(man2_pack: Path, tmp_path: Path) -> None:
    import hashlib

    plan = {
        "c": {"parameters_sha256": "p", "code_sha256": "c", "mode": "gap"},
        "encoder": ENCODER,
        "training": {"learning_rate": 1e-3, "batch": 4, "max_epochs": 2, "patience": 3},
        "models": {"ew-s1": {"seed": 1}},
    }
    pp = tmp_path / "plan.json"
    pp.write_text(json.dumps(plan))
    sha = hashlib.sha256(pp.read_bytes()).hexdigest()
    xs = build_prefixes(man2_pack, _segs(man2_pack, 3), 0, 3, "gap", None)
    save_prefixes(tmp_path / "train.npz", xs, {"plan_sha256": sha})
    save_prefixes(tmp_path / "val.npz", xs[:4], {"plan_sha256": sha})
    ck = tmp_path / "ck"
    cmd = [
        sys.executable,
        "-m",
        "tma2.cli.g2train",
        "train",
        "--plan",
        str(pp),
        "--model",
        "ew-s1",
        "--train",
        str(tmp_path / "train.npz"),
        "--val",
        str(tmp_path / "val.npz"),
        "--checkpoint",
        str(ck),
        "--epochs",
        "1",
    ]
    for _ in range(2):  # a fresh interpreter per job (AGENTS.md: within-process last bits)
        r = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert r.returncode == 0, r.stderr
    meta = json.loads((ck / "meta.json").read_text())
    assert meta["epoch"] == 2 and len(meta["jobs"]) == 2
    assert all(np.isfinite(e["val_trimmed"]) for e in meta["log"])
    assert (
        meta["weights_sha256"] == hashlib.sha256((ck / "best.safetensors").read_bytes()).hexdigest()
    )
