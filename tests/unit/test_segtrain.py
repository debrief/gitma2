"""Spec 005 T033: L's training data and training. Separate processes give byte-identical weights,
a resumed run equals an uninterrupted one, and the head comes alive after a short run."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from safetensors.torch import load_file

from tma2.cli.segtrain import main as segtrain
from tma2.segment import UNKNOWN
from tma2.segment.evidence import EvidenceNet, evidence_for
from tma2.segment.train import load_examples, shuffled_codes

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def plan(tmp_path_factory: pytest.TempPathFactory) -> Path:
    p = json.loads((ROOT / "configs/segment/gs-plan.json").read_text())
    p["id"] = "gs-plan-test"
    p["segmenter"]["parameters"]["mode"] = "chord"
    p["training"]["max_epochs"] = 2
    p["training"]["learning_rate"] = 0.001
    p["training"]["batch_scenarios"] = 2
    out = tmp_path_factory.mktemp("segtrain") / "plan.json"
    out.write_text(json.dumps(p))
    return out


@pytest.fixture(scope="module")
def tables(man2_pack: Path, plan: Path) -> Path:
    out = plan.parent / "tables.npz"
    args = ["tables", "--in", str(man2_pack), "--plan", str(plan), "--start", "0"]
    assert segtrain([*args, "--count", "4", "--out", str(out), "--workers", "2"]) == 0
    return out


def _train(plan: Path, tables: Path, ck: Path, epochs: int, model: str = "segL-s1") -> None:
    cmd = [sys.executable, "-m", "tma2.cli.segtrain", "train", "--plan", str(plan)]
    cmd += ["--model", model, "--train", str(tables), "--val", str(tables)]
    cmd += ["--checkpoint", str(ck), "--epochs", str(epochs)]
    subprocess.run(cmd, check=True, cwd=ROOT, capture_output=True)


def test_tables_round_trip(tables: Path) -> None:
    header, exs = load_examples(tables)
    assert header["examples"] == len(exs) > 0
    for ex in exs:
        g = ex.grid.shape[0]
        assert ex.cost.shape == (g, g) and ex.features.shape[1] == ex.valid.shape[0]
        assert all(int(k) in set(ex.grid.tolist()) for k in ex.ks)
        assert all(c.shape == (k + 1,) for k, c in zip(ex.ks, ex.codes, strict=True))


def test_shuffled_codes_are_seeded_and_fit(tables: Path) -> None:
    _, exs = load_examples(tables)
    a, b = shuffled_codes(exs, 1), shuffled_codes(exs, 1)
    for ex, ca, cb in zip(exs, a, b, strict=True):
        for k, x, y in zip(ex.ks, ca, cb, strict=True):
            assert x.shape == (k + 1,) and np.array_equal(x, y)
            assert set(np.unique(x).tolist()) <= {0, 1, UNKNOWN}


def test_separate_processes_identical_and_resume(plan: Path, tables: Path, tmp_path: Path) -> None:
    _train(plan, tables, tmp_path / "a", 2)
    _train(plan, tables, tmp_path / "b", 2)
    _train(plan, tables, tmp_path / "c", 1)
    _train(plan, tables, tmp_path / "c", 2)  # resumes from epoch 1
    for name in ("weights.safetensors", "best.safetensors"):
        da = (tmp_path / "a" / name).read_bytes()
        assert da == (tmp_path / "b" / name).read_bytes()
        assert da == (tmp_path / "c" / name).read_bytes()
    meta = json.loads((tmp_path / "a" / "meta.json").read_text())
    assert meta["epoch"] == 2 and meta["complete"] and meta["weights_digest"]
    assert meta["jobs"][0]["git_dirty"] in (True, False)
    # the head is alive: evidence non-zero and varying across rows
    torch.set_default_dtype(torch.float64)
    net = EvidenceNet().double()
    net.load_state_dict(load_file(str(tmp_path / "a" / "best.safetensors")))
    _, exs = load_examples(tables)
    ev = evidence_for(net, [ex.features.astype(np.float64) for ex in exs])
    assert all(float(np.abs(e).max()) > 0 and float(np.std(e)) > 0 for e in ev)
    assert meta["val_losses"][-1] < meta["val_losses"][0]


def test_refuses_tables_of_other_parameters(plan: Path, tables: Path, tmp_path: Path) -> None:
    p = json.loads(plan.read_text())
    p["segmenter"]["parameters"]["search_penalty"] = 31.0
    other = tmp_path / "plan.json"
    other.write_text(json.dumps(p))
    args = ["train", "--plan", str(other), "--model", "segL-s1", "--train", str(tables)]
    assert segtrain([*args, "--val", str(tables), "--checkpoint", str(tmp_path / "ck")]) == 2
