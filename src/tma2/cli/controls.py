"""``tma2-controls``: tune and run Gate D's controls (spec 004 contracts/cli.md; research R6).

``tune`` computes the control's statistic on every σ = 1° held-leg G5 row of a validation split
(``eval.rows``: zig + 5/10/15/20 min where reached, ``settled_row``) and picks the threshold whose
false-alarm fraction there is closest to ``--target-far`` (the detector's at its declared
operating point). ``run`` writes per-row alarms (p_change 1 where the statistic exceeds the
threshold, else 0) in the detector-output format, one record per scenario.

The least-squares controls read the per-timestep batch least-squares predictions of the same
split (``tma2-solve --per-timestep``), streamed in step with the truth file.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from tma2.data.canonical import canonical_json
from tma2.data.f32pack import iter_pack_raw
from tma2.data.io import AtomicFile, file_digest
from tma2.detect.controls import (
    CUSUM_DRIFT,
    GLR_WINDOW,
    cusum_ekf_stat,
    cusum_ls_stat,
    glr_stat,
    imm_mode_stat,
    ls_states,
    parse_imm_name,
    tune_threshold,
)
from tma2.eval.predictions import iter_predictions_raw
from tma2.eval.rows import G5_GATE_MIN, G5_SLICE_SIGMA_RAD, settled_row
from tma2.references.classical import BearingData, bearing_data_from_arrays
from tma2.types import SCHEMA_VERSION, RecordError, dump_record, parse_record
from tma2.types.generated.tma import ControlKind, ControlSettings

NEEDS_LS = (ControlKind.cusum, ControlKind.glr)


def parse_ekf_name(name: str) -> tuple[float, float, float]:
    """(σ_a, p0 scale, r scale) from ``ekf_name`` (ekf-sa…[-p…][-r…])."""
    parts = name.split("-")
    if parts[0] != "ekf" or not parts[1].startswith("sa"):
        raise ValueError(f"not an EKF setting: {name}")
    vals = {"p": 1.0, "r": 1.0}
    for p in parts[2:]:
        vals[p[0]] = float(p[1:])
    return float(parts[1][2:]), vals["p"], vals["r"]


def statistic(
    s: ControlSettings, d: BearingData, ls_rows: list[dict[str, Any]] | None
) -> np.ndarray:
    kind = ControlKind(s.kind)
    if kind in NEEDS_LS:
        if ls_rows is None:
            raise ValueError(f"{kind.value} needs --least-squares")
        st, ok = ls_states(d, ls_rows)
        if kind == ControlKind.cusum:
            return cusum_ls_stat(
                d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, s.cusum_drift or CUSUM_DRIFT
            )
        return glr_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, s.glr_window or GLR_WINDOW)
    if kind == ControlKind.imm_mode:
        if not s.imm:
            raise ValueError("imm_mode needs --imm")
        return imm_mode_stat(d, parse_imm_name(s.imm))
    if not s.ekf:
        raise ValueError("cusum_ekf needs --ekf")
    return cusum_ekf_stat(d, *parse_ekf_name(s.ekf))


def scenarios(
    truth: Path, ls: Path | None, limit: int | None
) -> Iterator[tuple[dict[str, Any], BearingData, list[dict[str, Any]] | None]]:
    preds = iter_predictions_raw(ls) if ls is not None else None
    for n, (_, meta, own, _tgt, obs) in enumerate(iter_pack_raw(truth)):
        if limit is not None and n >= limit:
            return
        rows = None
        if preds is not None:
            _, p = next(preds)
            if int(p["scenario_index"]) != int(meta["index"]):
                raise ValueError(
                    f"{ls}: scenario {p['scenario_index']} where the truth has {meta['index']}"
                )
            rows = p["rows"]
        yield meta, bearing_data_from_arrays(meta, own, obs), rows


def held_g5_rows(meta: dict[str, Any]) -> list[int]:
    if abs(float(meta["parameters"]["noise_sigma_rad"]) - G5_SLICE_SIGMA_RAD) > 1e-6:
        return []
    dt = float(meta["parameters"]["dt_s"])
    ks = [int(meta["zig_index"]) + int(round(m * 60 / dt)) for m in G5_GATE_MIN]
    return [k for k in ks if k < int(meta["samples"]) and settled_row(meta, k)]


def tune(a: argparse.Namespace) -> int:
    s = ControlSettings(
        kind=ControlKind(a.kind),
        threshold=0.0,
        cusum_drift=CUSUM_DRIFT if a.kind in ("cusum", "cusum_ekf") else None,
        glr_window=GLR_WINDOW if a.kind == "glr" else None,
        imm=a.imm,
        ekf=a.ekf,
        target_false_alarm=a.target_far,
        tuned_on=file_digest(a.validation),
    )
    ls = Path(a.least_squares) if a.least_squares else None
    vals: list[float] = []
    for meta, d, rows in scenarios(Path(a.validation), ls, a.limit):
        ks = held_g5_rows(meta)
        if ks:
            st = statistic(s, d, rows)
            vals.extend(float(st[k]) for k in ks)
    h, f = tune_threshold(np.asarray(vals), a.target_far)
    s.threshold = h
    s.achieved_false_alarm = f
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dump_record(s), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"kind": a.kind, "threshold": h, "false_alarm": f, "rows": len(vals)}))
    return 0


def control_name(s: ControlSettings) -> str:
    kind = ControlKind(s.kind).value
    tag = {"imm_mode": s.imm, "cusum_ekf": s.ekf}.get(kind)
    return f"{kind}-h{s.threshold!r}" + (f"-{tag}" if tag else "")


def run(a: argparse.Namespace) -> int:
    s = parse_record(ControlSettings, json.loads(Path(a.settings).read_text()), str(a.settings), 1)
    truth = Path(a.truth)
    header = {
        "record": "header",
        "schema_version": SCHEMA_VERSION,
        "detector": control_name(s),
        "control": dump_record(s),
        "dataset_digest": file_digest(truth),
        "knot_threshold": 0.5,
        "max_knots": 0,
    }
    f = AtomicFile(Path(a.out))
    f.write((canonical_json(header) + "\n").encode("utf-8"))
    n = 0
    ls = Path(a.least_squares) if a.least_squares else None
    try:
        for meta, d, rows in scenarios(truth, ls, a.limit):
            st = statistic(s, d, rows)
            alarm = [1.0 if v > s.threshold else 0.0 for v in st]
            rec = {"record": "detector", "scenario_index": int(meta["index"]), "p_change": alarm}
            f.write((canonical_json(rec) + "\n").encode("utf-8"))
            n += 1
        f.commit()
    except BaseException:
        f.abort()
        raise
    print(json.dumps({"scenarios": n, "out": a.out, "detector": header["detector"]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-controls")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tune")
    t.add_argument("--kind", required=True, choices=[k.value for k in ControlKind])
    t.add_argument("--validation", required=True)
    t.add_argument("--least-squares", help="per-timestep least-squares predictions (cusum, glr)")
    t.add_argument("--imm", help="frozen IMM setting name (imm_mode)")
    t.add_argument("--ekf", help="frozen EKF setting name (cusum_ekf)")
    t.add_argument("--target-far", type=float, required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--limit", type=int)
    r = sub.add_parser("run")
    r.add_argument("--settings", required=True)
    r.add_argument("--truth", required=True)
    r.add_argument("--least-squares")
    r.add_argument("--out", required=True)
    r.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    try:
        return tune(a) if a.cmd == "tune" else run(a)
    except (OSError, ValueError, RecordError, StopIteration) as e:
        print(f"tma2-controls: {e or 'predictions end before the truth file'}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
