from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import fixture_dir
from tma2.cli import generate as cli
from tma2.data.ndjson import read_ndjson
from tma2.data.provenance import GitProvenance


def _clean(monkeypatch: pytest.MonkeyPatch, dirty: bool = False, in_git: bool = True) -> None:
    monkeypatch.setattr(
        cli, "read_git_provenance", lambda: GitProvenance("abc123", dirty=dirty, in_git=in_git)
    )


def test_generates_splits_and_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _clean(monkeypatch)
    d = fixture_dir("iter4-seed777")
    code = cli.run(
        [
            "--seed",
            "5",
            "--count",
            "10",
            "--out",
            str(tmp_path),
            "--ranges",
            str(d / "ranges.json"),
            "--heldout-ranges",
            str(d / "heldout-ranges.json"),
            "--noise-free",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert [s["split"] for s in summary["splits"]] == ["train", "validation", "test", "heldout"]
    assert [s["scenarios"] for s in summary["splits"]] == [8, 1, 1, 1]
    header = read_ndjson(tmp_path / "test.ndjson").header
    assert header.generator_git_commit == "abc123" and header.generator_git_dirty is False
    assert header.created_by.startswith(
        "tma2-generate --seed 5 --count 10 --noise-free --ranges sha256:"
    )
    assert header.parameter_ranges.noise_sigma_rad_values == [0]
    assert (tmp_path / "digests.json").exists()


def test_refuses_dirty_tree_unless_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _clean(monkeypatch, dirty=True)
    args = ["--seed", "5", "--count", "10", "--out", str(tmp_path), "--format", "f32pack"]
    assert cli.run(args) == 2
    assert "uncommitted changes" in capsys.readouterr().err
    assert cli.run([*args, "--allow-dirty"]) == 0
    capsys.readouterr()


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--seed", "x", "--count", "1", "--out", "o"], "decimal integer"),
        (["--seed", "1", "--count", "0", "--out", "o"], "positive integer"),
        (["--seed", "1", "--count", "1", "--out", "o", "--format", "csv"], "bad --format"),
    ],
)
def test_usage_errors(
    args: list[str],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _clean(monkeypatch)
    assert cli.run(args) == 2
    assert message in capsys.readouterr().err


def test_manoeuvre_ranges_need_heldout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _clean(monkeypatch)
    d = fixture_dir("phase4-seed777")
    code = cli.run(
        ["--seed", "1", "--count", "10", "--out", str(tmp_path), "--ranges", str(d / "ranges.json")]
    )
    assert code == 2
    assert "needs --heldout-ranges" in capsys.readouterr().err


def test_p0_noise_free_check_ignores_default_dtype() -> None:
    """The noise-free check gives the same value whatever default dtype an earlier check left
    (P0 panel round 2: 2.383024e-6 alone against 2.383046e-6 after the physics check)."""
    import torch

    from tma2.cli import p0
    from tma2.eval.experiment import ROOT, Experiment

    values = []
    for dt in (torch.float32, torch.float64):
        before = torch.get_default_dtype()
        torch.set_default_dtype(dt)
        try:
            exp = Experiment(id="x", folder=ROOT / "experiments" / "_test-noise-free")
            p0.check_noise_free(exp)
            values.append(exp.checks[0].value)
        finally:
            torch.set_default_dtype(before)
    assert values[0] == values[1]
