"""Detector targets on fixture spans (spec 004 FR-011, R3)."""

from __future__ import annotations

from typing import Any

import numpy as np

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.eval.rows import settled_row
from tma2.features.batch import KIND_COURSE, KIND_SPEED
from tma2.models.detector_labels import pair_labels, row_labels


def _fixture(n: int = 40) -> tuple[list[dict[str, Any]], np.ndarray, np.ndarray, np.ndarray, int]:
    metas = []
    for _, meta, *_ in iter_pack_raw(fixture_dir("phase4-seed777") / "validation.f32pack"):
        metas.append(meta)
        if len(metas) >= n:
            break
    rows = max(int(m["samples"]) for m in metas)
    spans = np.full((len(metas), 4, 3), -1, dtype=np.int32)
    for i, m in enumerate(metas):
        for j, s in enumerate(m.get("manoeuvres") or []):
            kind = KIND_COURSE if s["kind"] == "course" else KIND_SPEED
            spans[i, j] = (kind, s["start_index"], s["end_index"])
    samples = np.array([int(m["samples"]) for m in metas])
    dt = np.array([float(m["parameters"]["dt_s"]) for m in metas])
    return metas, spans, samples, dt, rows


def test_held_matches_settled_row() -> None:
    metas, spans, samples, dt, rows = _fixture()
    lab = row_labels(spans, samples, dt, rows)
    assert any(m.get("manoeuvres") for m in metas)
    for i, m in enumerate(metas):
        for k in range(int(m["samples"])):
            assert lab.held[i, k] == settled_row(m, k), (i, k)
        assert not lab.held[i, int(m["samples"]) :].any()


def test_now_and_boundary() -> None:
    spans = np.array([[[KIND_COURSE, 20, 30], [KIND_SPEED, 60, 63], [-1, -1, -1]]])
    lab = row_labels(spans, np.array([100]), np.array([10.0]), 120)
    # in progress 20..29 or begun within 60 s (6 rows at dt 10 s): 20..29 and 60..65
    expect = np.zeros(120)
    expect[20:30] = 1
    expect[60:66] = 1
    np.testing.assert_array_equal(lab.now[0], expect)
    assert lab.boundary[0, 20] == 1 and lab.boundary[0, 30] == 1
    assert lab.boundary[0, 23] == 0.5 and lab.boundary[0, 13] == 0  # ±6 rows triangular
    assert lab.boundary[0, 100:].sum() == 0  # padded rows
    assert lab.held[0, :20].all() and not lab.held[0, 20:93].any() and lab.held[0, 93:100].all()
    assert not lab.settled[0, :20].any() and lab.settled[0, 93:100].all()


def test_pair_targets_only_for_past_boundaries() -> None:
    spans = np.array([[[KIND_COURSE, 20, 30], [KIND_SPEED, 33, 36], [-1, -1, -1]]])
    ks = np.array([[25, 40, -1]])
    p = pair_labels(spans, np.array([10.0]), ks, 60)
    assert p.w_target[0, 0, 20] == 1 and p.w_target[0, 0, 30] == 0  # end not yet reached
    assert p.w_target[0, 0, 26:].sum() == 0  # j > k
    assert p.w_target[0, 1, 30] == 1 and p.w_target[0, 1, 36] == 1
    assert p.w_target[0, 2].sum() == 0
    assert p.kind[0, 1, 30] == 1  # nearest boundary is the course span's end
    assert p.kind[0, 1, 34] == 0  # nearest is the speed span's start (33) or end (36)
    np.testing.assert_array_equal(p.kind_weight, p.w_target)
