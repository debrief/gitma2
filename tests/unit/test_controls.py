"""Controls on fixture manoeuvres (spec 004 FR-022–FR-024, R6)."""

from __future__ import annotations

import json

import numpy as np

from tests.conftest import fixture_dir
from tma2.data.f32pack import iter_pack_raw
from tma2.detect.controls import (
    GLR_WINDOW,
    cusum_ekf_stat,
    cusum_ls_stat,
    glr_stat,
    imm_mode_stat,
    ls_states,
    parse_imm_name,
    tune_threshold,
)
from tma2.eval.rows import settled_row
from tma2.references.classical import bearing_data_from_arrays

D = fixture_dir("phase4-seed777")


def _lsq() -> dict[int, list[dict[str, object]]]:
    out = {}
    with open(D / "predictions" / "test-lsq.ndjson", encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = json.loads(line)
            out[int(p["scenario_index"])] = p["rows"]
    return out


def test_statistics_rise_around_manoeuvres() -> None:
    lsq = _lsq()
    imm = parse_imm_name("imm-cv0.01-ct0.03-w0.01-s0.001-p4-r8")
    near: dict[str, list[float]] = {"cusum_ekf": [], "glr": [], "imm": []}
    held: dict[str, list[float]] = {"cusum_ekf": [], "glr": [], "imm": []}
    for _, meta, own, _tgt, obs in iter_pack_raw(D / "test.f32pack"):
        d = bearing_data_from_arrays(meta, own, obs)
        st, ok = ls_states(d, lsq[int(meta["index"])])
        stats = {
            "cusum_ekf": cusum_ekf_stat(d, 0.03, 4.0, 8.0),
            "glr": glr_stat(d.t, d.ox, d.oy, d.z, d.valid, d.sigma, st, ok, GLR_WINDOW),
            "imm": imm_mode_stat(d, imm),
        }
        for v in stats.values():
            assert v.shape == (d.n,) and np.isfinite(v).all() and (v >= 0).all()
        spans = meta.get("manoeuvres") or []
        for i in range(d.zig_index + 30, d.n):
            close = any(s["start_index"] <= i <= s["end_index"] + 30 for s in spans)
            for k, v in stats.items():
                if close:
                    near[k].append(float(v[i]))
                elif settled_row(meta, i):
                    held[k].append(float(v[i]))
    # Fraction of rows near a manoeuvre above the held legs' 90th percentile: above 10% means
    # the statistic separates (a per-span detection rate is higher still; seed 304: GLR 57% of
    # spans at a 5% false-alarm rate).
    for k in near:
        h = np.quantile(held[k], 0.9)
        assert np.mean(np.array(near[k]) > h) > 0.1, k


def test_least_squares_cusum_recursion() -> None:
    """S_k = max(0, S_{k−1} + ν² − 1 − δ) from the previous row's state; a bearing exactly on the
    prediction lowers S by 1 + δ, one 3σ off raises it by 9 − 1.5."""
    n = 4
    t = np.arange(n) * 10.0
    ox = np.zeros(n)
    oy = np.zeros(n)
    state = np.tile([0.0, 10_000.0, 0.0, 0.0], (n, 1))  # due north, stationary
    sigma = 0.01
    z = np.array([0.0, 0.0, 3 * sigma, 0.0])
    s = cusum_ls_stat(t, ox, oy, z, np.ones(n), sigma, state, np.ones(n, dtype=bool), 0.5)
    np.testing.assert_allclose(s, [0.0, 0.0, 7.5, 6.0], atol=1e-9)


def test_tune_threshold_matches_target() -> None:
    v = np.arange(1000, dtype=np.float64)
    h, f = tune_threshold(v, 0.05)
    assert f == 0.05 and h == 949.0
    h0, f0 = tune_threshold(np.zeros(10), 0.0)
    assert f0 == 0.0 and h0 == 0.0


def test_controls_cli_tunes_and_runs(tmp_path: object) -> None:
    from pathlib import Path

    from tma2.cli.controls import main
    from tma2.types import parse_record
    from tma2.types.generated.tma import ControlSettings, DetectorHeader, DetectorRecord

    tmp = Path(str(tmp_path))
    ls = str(D / "predictions" / "test-lsq.ndjson")
    for kind, extra in (
        ("cusum", ["--least-squares", ls]),
        ("glr", ["--least-squares", ls]),
        ("imm_mode", ["--imm", "imm-cv0.01-ct0.03-w0.01-s0.001-p4-r8"]),
        ("cusum_ekf", ["--ekf", "ekf-sa0.03-p4-r8"]),
    ):
        st = tmp / f"{kind}.json"
        args = ["tune", "--kind", kind, "--validation", str(D / "test.f32pack"), *extra]
        assert main([*args, "--target-far", "0.1", "--out", str(st)]) == 0
        s = parse_record(ControlSettings, json.loads(st.read_text()), str(st), 1)
        assert s.achieved_false_alarm is not None and abs(s.achieved_false_alarm - 0.1) < 0.1
        out = tmp / f"{kind}.ndjson"
        run = ["run", "--settings", str(st), "--truth", str(D / "test.f32pack"), "--out", str(out)]
        if "--least-squares" in extra:
            run += ["--least-squares", ls]
        assert main(run) == 0
        lines = out.read_text().splitlines()
        hdr = parse_record(DetectorHeader, json.loads(lines[0]), str(out), 1)
        assert hdr.control is not None and hdr.control.threshold == s.threshold
        for i, line in enumerate(lines[1:]):
            rec = parse_record(DetectorRecord, json.loads(line), str(out), i + 2)
            assert set(rec.p_change) <= {0.0, 1.0}
