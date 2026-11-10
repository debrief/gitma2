"""Dataset generation: splits, headers, writers and digests (gitma ``generate.ts``)."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import numpy as np

from tma2.sim import mismatch as mm
from tma2.sim.generate import KernelBuffers, kernel_arrays, kernel_metadata, run_kernel
from tma2.sim.ranges import flatten_ranges, rows_for
from tma2.sim.version import GENERATOR_VERSION
from tma2.types import SCHEMA_VERSION, DatasetHeader

from .canonical import canonical_json, scenario_json_arrays
from .f32pack import PackWriter, encode_block_arrays
from .io import AtomicFile, file_digest
from .ndjson import NdjsonWriter

Format = Literal["ndjson", "f32pack", "both"]
SPLITS = ("train", "validation", "test", "heldout")


@dataclass
class SplitPlan:
    split: str
    start: int
    end: int
    ranges: dict[str, Any]


def plan_splits(count: int, ranges: dict[str, Any], heldout: dict[str, Any]) -> list[SplitPlan]:
    """Train/validation/test 80/10/10 by index; held-out gets count/10 indices after the rest."""
    a = int(np.floor(0.8 * count))
    b = int(np.floor(0.9 * count))
    return [
        SplitPlan("train", 0, a, ranges),
        SplitPlan("validation", a, b, ranges),
        SplitPlan("test", b, count, ranges),
        SplitPlan("heldout", count, count + count // 10, heldout),
    ]


@dataclass
class GenerateOptions:
    seed: np.uint64
    count: int
    out_dir: Path
    ranges: dict[str, Any]
    heldout_ranges: dict[str, Any]
    format: Format
    created_by: str
    generator_git_commit: str
    generator_git_dirty: bool
    schema_version: str = SCHEMA_VERSION
    """Header schema version; tests regenerating gitma fixtures pass the fixture's (0.16.0)."""
    generator_version: str = GENERATOR_VERSION
    """Header generator version; tests regenerating gitma fixtures pass the fixture's (0.5.0).
    Generator 0.6.0 reproduces 0.5.0 byte for byte for ranges without its fields, so only this
    label differs."""
    mismatch: dict[str, Any] | None = None
    """Spec 010: a ``MismatchCondition`` dict. When it enables any kind, the bearings are rebuilt
    by the overlay, the header records the condition and generator 0.7.0, and each split gets a
    truth side file ``<split>.mismatch.npz``. ``None`` or an all-off condition changes nothing."""


@dataclass
class SplitSummary:
    split: str
    scenarios: int
    redraws: int
    files: list[str] = field(default_factory=list)


def generate_dataset(opts: GenerateOptions) -> list[SplitSummary]:
    """Write every split in the requested formats plus ``digests.json``; returns the summary."""
    opts.out_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[SplitSummary] = []
    written: list[Path] = []
    cond = mm.flatten_condition(opts.mismatch) if opts.mismatch is not None else None
    if cond is not None and cond.off:
        cond = None
    for plan in plan_splits(opts.count, opts.ranges, opts.heldout_ranges):
        R = flatten_ranges(plan.ranges)
        buf = KernelBuffers.for_rows(rows_for(plan.ranges))
        # Count redraws first so the header (written before any scenario) is exact.
        redraws = 0
        for i in range(plan.start, plan.end):
            redraws += run_kernel(opts.seed, i, R, buf)
        n_split = plan.end - plan.start
        rmax = rows_for(plan.ranges)
        truth_eng = np.zeros((n_split, mm.E_LEN)) if cond is not None else None
        truth_comp = np.zeros((n_split, rmax, 4), dtype=np.float32) if cond is not None else None
        truth_out = np.zeros((n_split, rmax), dtype=np.bool_) if cond is not None else None
        header = DatasetHeader.model_validate(
            {
                "record": "header",
                "schema_version": opts.schema_version,
                "generator_version": (
                    mm.MISMATCH_VERSION if cond is not None else opts.generator_version
                ),
                **({"mismatch": opts.mismatch} if cond is not None else {}),
                "dataset_seed": str(int(opts.seed)),
                "split": plan.split,
                "scenario_count": plan.end - plan.start,
                "index_start": plan.start,
                "index_end": plan.end,
                "parameter_ranges": plan.ranges,
                "redraw_count": redraws,
                "created_by": opts.created_by,
                "generator_git_commit": opts.generator_git_commit,
                "generator_git_dirty": opts.generator_git_dirty,
            }
        )
        files: list[Path] = []
        ndjson: NdjsonWriter | None = None
        pack: PackWriter | None = None
        if opts.format != "f32pack":
            files.append(opts.out_dir / f"{plan.split}.ndjson")
            ndjson = NdjsonWriter(files[-1], header)
        if opts.format != "ndjson":
            files.append(opts.out_dir / f"{plan.split}.f32pack")
            pack = PackWriter(files[-1], header)
        try:
            for i in range(plan.start, plan.end):
                run_kernel(opts.seed, i, R, buf, cond)
                metadata = kernel_metadata(opts.seed, i, buf)
                own, tgt, obs = kernel_arrays(buf)
                if truth_eng is not None and truth_comp is not None and truth_out is not None:
                    n = int(metadata["samples"])
                    truth_eng[i - plan.start] = buf.eng
                    truth_comp[i - plan.start, :n] = buf.comp[:n]
                    truth_out[i - plan.start, :n] = buf.outlier[:n]
                if ndjson is not None:
                    ndjson.write_text(scenario_json_arrays(metadata, own, tgt, obs))
                if pack is not None:
                    pack.write_block(
                        encode_block_arrays(
                            metadata,
                            own.astype(np.float32),
                            tgt.astype(np.float32),
                            obs.astype(np.float32),
                        )
                    )
            if ndjson is not None:
                ndjson.close()
            if pack is not None:
                pack.close()
        except BaseException:
            if ndjson is not None:
                ndjson.abort()
            if pack is not None:
                pack.abort()
            raise
        if truth_eng is not None and truth_comp is not None and truth_out is not None:
            side = opts.out_dir / f"{plan.split}.mismatch.npz"
            write_mismatch_truth(
                side,
                opts,
                plan.split,
                plan.start,
                truth_eng,
                truth_comp,
                truth_out,
            )
            files.append(side)
        written.extend(files)
        summaries.append(
            SplitSummary(plan.split, header.scenario_count, redraws, [str(f) for f in files])
        )
    digests = {f.name: file_digest(f) for f in written}
    out = AtomicFile(opts.out_dir / "digests.json")
    out.write((json.dumps(digests, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    out.commit()
    return summaries


def mismatch_truth_digest(eng: np.ndarray, comp: np.ndarray, outlier: np.ndarray) -> str:
    """SHA-256 over the truth arrays' bytes (an ``.npz`` carries zip timestamps, so the file's own
    digest is not reproducible; this one is)."""
    h = hashlib.sha256()
    for a in (
        np.ascontiguousarray(eng, dtype="<f8"),
        np.ascontiguousarray(comp, dtype="<f4"),
        np.ascontiguousarray(outlier, dtype=np.uint8),
    ):
        h.update(a.tobytes())
    return h.hexdigest()


def write_mismatch_truth(
    path: Path,
    opts: GenerateOptions,
    split: str,
    index_start: int,
    eng: np.ndarray,
    comp: np.ndarray,
    outlier: np.ndarray,
) -> None:
    """The mismatch truth side file (spec 010 data model): read by the oracle ceilings only."""
    meta = {
        "record": "mismatch_truth",
        "condition": opts.mismatch,
        "dataset_seed": str(int(opts.seed)),
        "split": split,
        "index_start": index_start,
        "scenario_count": int(eng.shape[0]),
        "generator_version": mm.MISMATCH_VERSION,
        "generator_git_commit": opts.generator_git_commit,
        "generator_git_dirty": opts.generator_git_dirty,
        "eng_columns": [
            "sigma_true_rad",
            "sigma_w_rad",
            "sigma_c_rad",
            "tau_c_s",
            "sigma_b_rad",
            "tau_b_s",
            "outlier_rate",
            "outlier_sd_rad",
        ],
        "comp_columns": ["white_rad", "correlated_rad", "bias_rad", "outlier_rad"],
        "truth_sha256": mismatch_truth_digest(eng, comp, outlier),
    }
    tmp = path.with_suffix(".tmp.npz")
    np.savez_compressed(
        tmp, meta=np.array(json.dumps(meta, sort_keys=True)), eng=eng, comp=comp, outlier=outlier
    )
    tmp.replace(path)


def timed_generate(opts: GenerateOptions) -> dict[str, Any]:
    """``generate_dataset`` with gitma's JSON summary shape."""
    t0 = time.perf_counter()
    summaries = generate_dataset(opts)
    seconds = time.perf_counter() - t0
    total = sum(s.scenarios for s in summaries)
    return {
        "out": str(opts.out_dir),
        "splits": [
            {"split": s.split, "scenarios": s.scenarios, "redraws": s.redraws, "files": s.files}
            for s in summaries
        ],
        "seconds": seconds,
        "scenarios_per_s": int(round(total / seconds)) if seconds > 0 else 0,
    }


def dump_canonical(value: Any) -> str:
    """Convenience for callers that need canonical text (re-exported for tests)."""
    return canonical_json(value)
