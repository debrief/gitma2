"""IMM and EKF covariances (spec 008 T010): ``cov=True`` adds the filter's covariance to each
plausible row and changes no other field."""

from __future__ import annotations

from pathlib import Path

from tma2.data.f32pack import iter_pack_raw
from tma2.detect.controls import parse_imm_name
from tma2.references.classical import bearing_data_from_arrays
from tma2.references.ekf import ekf_predict
from tma2.references.imm import imm_predict

IMM = "imm-cv0.03-ct1-w0.01-s0.0003-p4-r2"
COV_KEYS = {"cov_ok", "cov_xyvv", "log_range_sd", "course_sd_rad", "speed_sd_mps"}


def test_tracker_points_unchanged_with_covariance(man2_pack: Path) -> None:
    seen = 0
    for i, (_, m, own, _tgt, obs) in enumerate(iter_pack_raw(man2_pack)):
        if i >= 4:
            break
        d = bearing_data_from_arrays(m, own, obs)
        for f in (
            lambda c: imm_predict(d, parse_imm_name(IMM), cov=c),
            lambda c: ekf_predict(d, 0.00003, 4.0, 0.03125, cov=c),
        ):
            plain, rich = f(False)["rows"], f(True)["rows"]
            assert len(plain) == len(rich)
            for a, b in zip(plain, rich, strict=True):
                assert {k: b[k] for k in a} == a
                if a["converged"] and b.get("cov_ok"):
                    assert COV_KEYS <= set(b)
                    seen += 1
                else:
                    assert set(b) - set(a) <= {"cov_ok", "cov_xyvv"}
    assert seen > 0
