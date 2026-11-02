"""Gate D's downstream estimate (spec 004 FR-027)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tests.conftest import fixture_dir
from tma2.cli.oracle import predict_split as oracle_predict
from tma2.data.canonical import canonical_json
from tma2.data.f32pack import iter_pack_raw
from tma2.data.io import file_digest
from tma2.detect.downstream import downstream_split
from tma2.eval.errors import Truth, row_error
from tma2.eval.predictions import iter_predictions_raw

D = fixture_dir("phase4-seed777")
TRUTH = D / "test.f32pack"


def _detector_file(path: Path, truth_knots: bool, n: int = 12) -> None:
    hdr = {
        "record": "header",
        "schema_version": "0.21.0",
        "detector": "truth" if truth_knots else "none",
        "variant": "causal",
        "dataset_digest": file_digest(TRUTH),
        "knot_threshold": 0.5,
        "max_knots": 8,
    }
    lines = [canonical_json(hdr)]
    for i, (_, meta, *_r) in enumerate(iter_pack_raw(TRUTH)):
        if i >= n:
            break
        sets = []
        for m in (5, 10, 15, 20):
            k = int(meta["zig_index"]) + 6 * m
            if k >= int(meta["samples"]):
                continue
            knots = []
            if truth_knots:
                for s in meta.get("manoeuvres") or []:
                    for r in (s["start_index"], s["end_index"]):
                        if 0 < r <= k:
                            pk = 1.0 if s["kind"] == "course" else 0.0
                            knots.append({"row": r, "weight": 1.0, "p_kind": pk})
            sets.append({"query_row": k, "knots": knots})
        rec = {"record": "detector", "scenario_index": int(meta["index"]), "knot_sets": sets}
        rec["p_change"] = [0.0] * int(meta["samples"])
        lines.append(canonical_json(rec))
    path.write_text("\n".join(lines) + "\n")


def _errors(path: Path) -> list[float]:
    truths = {int(m["index"]): Truth.from_block(m, o, t) for _, m, o, t, _ in iter_pack_raw(TRUTH)}
    out = []
    for _, p in iter_predictions_raw(path):
        for r in p["rows"]:
            out.append(row_error(truths[int(p["scenario_index"])], r).range_rel)
    return out


def test_no_knots_is_batch_least_squares_in_the_layer(tmp_path: Path) -> None:
    _detector_file(tmp_path / "none.ndjson", False)
    downstream_split(tmp_path / "none.ndjson", TRUTH, tmp_path / "none-pred.ndjson", limit=12)
    oracle_predict(str(TRUTH), str(tmp_path / "triv.ndjson"), False, False, 100, 8, trivial=True)
    a = [r for _, p in iter_predictions_raw(tmp_path / "none-pred.ndjson") for r in p["rows"]]
    b = [r for _, p in iter_predictions_raw(tmp_path / "triv.ndjson") for r in p["rows"]][: len(a)]
    assert a == b


def test_truth_knots_beat_no_knots(tmp_path: Path) -> None:
    _detector_file(tmp_path / "truth.ndjson", True)
    _detector_file(tmp_path / "none.ndjson", False)
    downstream_split(tmp_path / "truth.ndjson", TRUTH, tmp_path / "t.ndjson", limit=12)
    downstream_split(tmp_path / "none.ndjson", TRUTH, tmp_path / "n.ndjson", limit=12)
    header = json.loads((tmp_path / "t.ndjson").read_text().splitlines()[0])
    assert header["estimator"] == "truth-downstream"
    assert np.median(_errors(tmp_path / "t.ndjson")) < np.median(_errors(tmp_path / "n.ndjson"))
