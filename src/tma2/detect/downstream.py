"""Gate D's downstream estimate (spec 004 FR-027, FR-028; research R4, R8).

At each G5 row of each scenario, the physics layer with trivial per-bearing weights and the grid
start, fed the detector's exported knots (weight 1 each) and kinds (a course change gets the
speed-continuity prior and its skip, a speed change neither). The causal detector's knots are those
of the question asked at the row; the time-late detector's are those of its one question at the
last row, and its solve uses the whole window and reports the state at the row (``k_state``), as
the time-late Gate 1 control did. The output is an ordinary per-timestep prediction file, scored
beside batch least squares, the IMM, the EKF and the oracle on the same rows.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import torch

from tma2.cli.oracle import empty_row, inputs_for, row_from_output, rows_for
from tma2.data.f32pack import iter_pack_raw
from tma2.eval.predictions import PredictionWriter
from tma2.models.detector_inputs import Knot, knot_arrays
from tma2.physics.layer import PhysicsLayer
from tma2.physics.segmentation import LayerInputs, trivial_inputs
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.types import parse_record
from tma2.types.generated.tma import DetectorHeader, DetectorVariant

ITERATIONS = 100


def read_detector_file(path: str | Path) -> tuple[DetectorHeader, Any]:
    f = open(path, encoding="utf-8")  # noqa: SIM115 (closed by the generator)
    header = parse_record(DetectorHeader, json.loads(f.readline()), str(path), 1)

    def records() -> Any:
        with f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    return header, records()


def knots_for(rec: dict[str, Any], query_row: int) -> list[Knot]:
    for s in rec.get("knot_sets") or []:
        if int(s["query_row"]) == query_row:
            return [Knot(int(k["row"]), float(k["weight"]), float(k["p_kind"])) for k in s["knots"]]
    return []


def downstream_split(
    detector_file: str | Path,
    truth: str | Path,
    out: str | Path,
    batch: int = 256,
    limit: int | None = None,
) -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    header, recs = read_detector_file(detector_file)
    late = (
        header.variant is not None and DetectorVariant(header.variant) == DetectorVariant.time_late
    )
    layer = PhysicsLayer(iterations=ITERATIONS, knots=header.max_knots or 8)
    name = f"{header.detector}-downstream"
    writer = PredictionWriter(
        out, name, "per_timestep", truth, weights_digest=header.weights_digest
    )
    t0 = time.perf_counter()
    pending: list[tuple[BearingData, int, LayerInputs]] = []
    k_state: list[int] = []
    scen: list[tuple[int, list[tuple[int, int | None]], BearingData]] = []
    r_max = 0
    n = 0

    def flush() -> None:
        nonlocal r_max
        o: Any = None
        if pending:
            x = inputs_for(pending, r_max)
            x = replace(x, k_state=torch.tensor(k_state, dtype=torch.int64))
            with torch.no_grad():
                o = layer(x)
        for idx, rows, d in scen:
            out_rows = [
                empty_row(d, k) if j is None else row_from_output(d, k, o, j) for k, j in rows
            ]
            writer.write(
                {
                    "record": "prediction",
                    "scenario_index": idx,
                    "estimator": name,
                    "mode": "per_timestep",
                    "rows": out_rows,
                }
            )
        pending.clear()
        k_state.clear()
        scen.clear()
        r_max = 0

    try:
        for _, meta, own, _tgt, obs in iter_pack_raw(truth):
            if limit is not None and n >= limit:
                break
            rec = next(recs)
            if int(rec["scenario_index"]) != int(meta["index"]):
                raise ValueError(
                    f"{detector_file}: scenario {rec['scenario_index']} where the truth has "
                    f"{meta['index']}"
                )
            d = bearing_data_from_arrays(meta, own, obs)
            last = d.n - 1
            rows: list[tuple[int, int | None]] = []
            for k in rows_for(meta, False):
                solve_k = last if late else k
                base = trivial_inputs(d.t, d.ox, d.oy, d.z, d.valid, solve_k)
                if base is None:
                    rows.append((k, None))
                    continue
                cp, kind = knot_arrays(knots_for(rec, solve_k), d.n)
                pending.append(
                    (d, solve_k, LayerInputs(cp, kind, base.log_weight, base.theta0, kind))
                )
                k_state.append(k)
                rows.append((k, len(pending) - 1))
            r_max = max(r_max, d.n)
            scen.append((int(meta["index"]), rows, d))
            n += 1
            if len(pending) >= batch:
                flush()
        flush()
        writer.close()
    except BaseException:
        writer.abort()
        raise
    return {"out": str(out), "estimator": name, "scenarios": n, "seconds": time.perf_counter() - t0}
