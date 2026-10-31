"""Output is a pure function of (seed, index, ranges): batch size, workers and order don't matter,
and a batch row equals the decoded file row (spec 001 SC-002, batch-interface contract)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tests.conftest import fixture_ranges
from tma2.data.dataset import GenerateOptions, generate_dataset
from tma2.data.f32pack import read_pack_raw
from tma2.features.batch import Batch, generate_batch, generate_indices


def _same(a: Batch, b: Batch) -> bool:
    return all(
        np.array_equal(getattr(a, f), getattr(b, f))
        for f in (
            "index",
            "samples",
            "zig_index",
            "sigma",
            "dropout",
            "redraws",
            "t",
            "mask",
            "own",
            "tgt",
            "bearing",
            "valid",
            "manoeuvring",
            "last_kind",
            "since_zig_s",
            "since_manoeuvre_end_s",
            "spans",
        )
    )


def test_batch_size_and_workers_do_not_change_output() -> None:
    ranges, _ = fixture_ranges("phase4-seed777")
    whole = generate_batch(777, 0, 64, ranges, end=64, workers=4)
    ones = [generate_batch(777, i, 1, ranges, end=64, workers=1) for i in range(64)]
    for i, one in enumerate(ones):
        sub = generate_indices(777, np.array([i]), ranges, workers=1)
        assert _same(one, sub)
        for f in ("own", "tgt", "bearing", "valid", "mask", "spans", "manoeuvring"):
            assert np.array_equal(getattr(whole, f)[i : i + 1], getattr(one, f))
    reverse = generate_indices(777, np.arange(63, -1, -1), ranges, workers=3)
    assert np.array_equal(reverse.own[::-1], whole.own)
    assert np.array_equal(reverse.redraws[::-1], whole.redraws)


def test_batch_rows_equal_file_rows(tmp_path: Path) -> None:
    ranges, heldout = fixture_ranges("phase4-seed777")
    generate_dataset(
        GenerateOptions(
            seed=np.uint64(321),
            count=20,
            out_dir=tmp_path,
            ranges=ranges,
            heldout_ranges=heldout,
            format="f32pack",
            created_by="test",
            generator_git_commit="test",
            generator_git_dirty=True,
        )
    )
    batch = generate_batch(321, 0, 16, ranges, end=16)
    _, blocks = read_pack_raw(tmp_path / "train.f32pack")
    for i, meta, own, tgt, obs in blocks:
        n = meta["samples"]
        assert batch.samples[i] == n
        assert batch.zig_index[i] == meta["zig_index"]
        assert np.array_equal(batch.own[i, :n], own[:, 1:5])
        assert np.array_equal(batch.tgt[i, :n], tgt[:, 1:5])
        assert np.array_equal(batch.t[i, :n], own[:, 0])
        assert np.array_equal(batch.bearing[i, :n], obs[:, 1])
        assert np.array_equal(batch.valid[i, :n], obs[:, 2] != 0)
        assert not batch.mask[i, n:].any()
        spans = [s for s in batch.spans[i].tolist() if s[0] != -1]
        assert spans == [
            [0 if m["kind"] == "course" else 1, m["start_index"], m["end_index"]]
            for m in meta.get("manoeuvres", [])
        ]
        for s in spans:
            assert batch.manoeuvring[i, s[1] : s[2]].all()
        assert batch.since_zig_s[i, meta["zig_index"]] == 0.0


def test_two_cli_runs_are_byte_identical(tmp_path: Path) -> None:
    ranges, heldout = fixture_ranges("iter4-seed777")
    outs = []
    for k in range(2):
        d = tmp_path / str(k)
        generate_dataset(
            GenerateOptions(
                seed=np.uint64(9),
                count=10,
                out_dir=d,
                ranges=ranges,
                heldout_ranges=heldout,
                format="both",
                created_by="test",
                generator_git_commit="test",
                generator_git_dirty=True,
            )
        )
        outs.append((d / "digests.json").read_text())
    assert outs[0] == outs[1]
