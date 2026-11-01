"""Evaluation and naive baseline reproduce gitma (spec 002 FR-001, FR-013..015, SC-005)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tests.conftest import fixture_dir
from tma2.cli import estimators, evaluate
from tma2.eval.bootstrap import bootstrap_clustered_quantile_ratio, bootstrap_median

P4 = fixture_dir("phase4-seed777")
PRED = P4 / "predictions"


def test_metrics_equal_gitma_tma_eval(tmp_path: Path) -> None:
    preds = [str(PRED / f"test-{e}.ndjson") for e in ("naive", "lsq", "imm", "ekf")]
    assert (
        evaluate.main(
            [
                "--truth",
                str(P4 / "test.f32pack"),
                "--predictions",
                *preds,
                "--points",
                "300,600",
                "--out",
                str(tmp_path),
            ]
        )
        == 0
    )
    gitma = {
        (r["estimator"], r["slice"], r["point"]): r
        for r in json.loads((PRED / "test-tma-eval-metrics.json").read_text())
    }
    mine = {
        (r["estimator"], r["slice"], r["point"]): r
        for r in json.loads((tmp_path / "metrics.json").read_text())
    }
    assert set(gitma) == set(mine)
    for k, g in gitma.items():
        for f, v in g.items():
            if isinstance(v, float):
                assert abs(mine[k][f] - v) <= 1e-9 * max(abs(v), 1e-12), (k, f)
            else:
                assert mine[k][f] == v, (k, f)
    # curves: gitma's columns are a prefix of ours, values equal
    g_lines = (PRED / "test-tma-eval-curves.csv").read_text().splitlines()
    m_lines = (tmp_path / "curves.csv").read_text().splitlines()
    assert len(g_lines) == len(m_lines)
    for a, b in zip(g_lines[1:], m_lines[1:], strict=True):
        ga, mb = a.split(","), b.split(",")
        for x, y in zip(ga, mb[: len(ga)], strict=True):
            if x == y:
                continue
            assert abs(float(x) - float(y)) <= 1e-9 * max(abs(float(x)), 1e-12)


def test_naive_matches_gitma(tmp_path: Path) -> None:
    model = tmp_path / "naive.json"
    assert (
        estimators.naive_main(["fit", "--train", str(P4 / "train.f32pack"), "--out", str(model)])
        == 0
    )
    mine = json.loads(model.read_text())
    theirs = json.loads((PRED / "naive-model.json").read_text())
    assert mine["final"] == theirs["final"] and mine["per_timestep"] == theirs["per_timestep"]
    out = tmp_path / "naive.ndjson"
    assert (
        estimators.naive_main(
            [
                "predict",
                "--model",
                str(model),
                "--in",
                str(P4 / "test.f32pack"),
                "--out",
                str(out),
                "--per-timestep",
            ]
        )
        == 0
    )
    a = out.read_text().splitlines()[1:]
    b = (PRED / "test-naive.ndjson").read_text().splitlines()[1:]
    assert a == b  # prediction records byte-identical (headers differ only in schema version)


def test_bootstrap_is_seeded_and_brackets_the_point() -> None:
    rng = np.random.default_rng(0)
    a = rng.lognormal(size=500)
    b = rng.lognormal(size=500) * 1.2
    cluster = np.repeat(np.arange(125), 4)
    r1 = bootstrap_clustered_quantile_ratio(a, b, cluster, 0.5, 0.975, 300)
    r2 = bootstrap_clustered_quantile_ratio(a, b, cluster, 0.5, 0.975, 300)
    assert (r1.lo, r1.hi) == (r2.lo, r2.hi)
    assert r1.lo <= r1.ratio <= r1.hi and r1.clusters == 125
    m = bootstrap_median(a, 300)
    assert m.lo <= m.median <= m.hi
