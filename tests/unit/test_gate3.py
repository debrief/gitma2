"""Gate 3's criteria (spec 008 T027)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from tma2.calib.gate import FAIL, INCONCLUSIVE, PASS, all_of, below, criteria, inside, shuffled_rule

BANDS = {"coverage95": [0.92, 0.98], "nees_median_ratio": [0.8, 1.25]}


def _cal(n: int, scale: float, seed: int) -> np.ndarray:
    """Calibrated rows (true sd 1) stated with sd = scale; NEES consistent with the scale."""
    rng = np.random.default_rng(seed)
    e = np.abs(rng.normal(size=(n, 3)))
    cal = np.zeros((n, 9))
    cal[:, 0:3] = e
    cal[:, 3:6] = scale
    cal[:, 6] = rng.chisquare(4, n) / scale**2
    cal[:, 7:9] = 1.0
    return cal


def test_verdict_helpers() -> None:
    assert inside({"value": 0.95, "lo": 0.94, "hi": 0.96}, 0.92, 0.98) == PASS
    assert inside({"value": 0.80, "lo": 0.78, "hi": 0.82}, 0.92, 0.98) == FAIL
    assert inside({"value": 0.95, "lo": 0.90, "hi": 0.97}, 0.92, 0.98) == INCONCLUSIVE
    assert below({"value": -1, "lo": -2, "hi": -0.5}, 0) == PASS
    assert all_of([PASS, INCONCLUSIVE]) == INCONCLUSIVE and all_of([PASS, FAIL]) == FAIL
    assert shuffled_rule({"value": -1, "lo": -2, "hi": -0.5}) == FAIL
    assert shuffled_rule({"value": -1, "lo": -2, "hi": 0.5}) == PASS


def test_calibrated_e_passes_and_overconfident_fails() -> None:
    n = 3000
    cluster = np.arange(n) // 4
    good = _cal(n, 1.0, 1)
    tight = _cal(n, 0.5, 1)  # the same errors stated with half the sd
    err = np.zeros((n, 3))
    out = criteria(good, tight, err, err.copy(), cluster, BANDS, PASS, 0.975, 300)
    assert out["g3a"] == PASS and out["g3b"] == PASS
    assert out["g3c"] == PASS  # the calibrated rows score better than the overconfident ones
    assert out["g3d"] == PASS and out["overall"] == PASS
    worse = criteria(tight, good, err, err + 1e-9, cluster, BANDS, PASS, 0.975, 300)
    assert worse["g3a"] == FAIL and worse["g3c"] == FAIL and worse["g3d"] == FAIL
    void = criteria(good, tight, err, err.copy(), cluster, BANDS, FAIL, 0.975, 300)
    assert void["g3c"] == FAIL


def _scoring(tmp_path: Path, n: int, ordinals: np.ndarray) -> dict[str, Any]:
    """A fake scoring run: errors.npz, inputs.json and three prediction files."""
    from tma2.segment.gate import sha256_file

    d = tmp_path / "score"
    d.mkdir()
    files = {}
    for name, w in (("head", "E"), ("temp", "E"), ("raw", "E"), ("shuf", "E")):
        f = tmp_path / f"{name}.ndjson"
        cal = {"weights_sha256": "H"} if name == "head" else {}
        f.write_text(json.dumps({"weights_sha256": w, "calibration": cal}) + "\n")
        files[name] = f
    err = np.zeros((n, 3))
    np.savez(
        d / "errors.npz",
        ordinal=ordinals,
        k=np.zeros(n, dtype=np.int64),
        cal_head=_cal(n, 1.0, 1),
        cal_temp=_cal(n, 0.5, 1),
        cal_raw=_cal(n, 0.5, 1),
        cal_shuf=_cal(n, 0.5, 2),
        err_head=err,
        err_temp=err,
        err_raw=err,
        err_shuf=err,
    )
    inputs = {"truth": "T", "predictions": {k: sha256_file(v) for k, v in files.items()}}
    (d / "inputs.json").write_text(json.dumps(inputs))
    dec = tmp_path / "decision" / "decision.json"
    dec.parent.mkdir()
    dec.write_text(
        json.dumps(
            {
                "validation_digest": "T",
                "criteria": BANDS,
                "bootstrap_level": 0.975,
                "bootstrap_resamples": 200,
                "carried_e_weights": "E",
            }
        )
    )
    return {"dir": d, "files": files, "decision": dec}


def test_g3_cli_validation_then_test(tmp_path: Path) -> None:
    from tma2.cli.g3 import main

    n = 2000
    s = _scoring(tmp_path, n, np.arange(n) // 4)
    f = s["files"]
    roles = [
        "--head", f"head={f['head']}",
        "--temperature", f"temp={f['temp']}",
        "--raw", f"raw={f['raw']}",
    ]  # fmt: skip
    base = ["--scoring", str(s["dir"]), "--decision", str(s["decision"]), *roles]
    vout = tmp_path / "val"
    args = [*base, "--split", "validation", "--shuffled", f"shuf={f['shuf']}"]
    assert main([*args, "--out", str(vout)]) == 0
    v = json.loads((vout / "validation.json").read_text())
    assert v["shuffled_rule"] == PASS and v["overall"] == PASS
    # test: refused without the test digest and carried.json, then passes with them
    tout = tmp_path / "test"
    assert main([*base, "--split", "test", "--out", str(tout)]) == 2
    dd = s["decision"].parent
    (dd / "test-digest.json").write_text(
        json.dumps({"dataset_digest": "T", "sigma1_scenarios": n // 4})
    )
    vrec = dd / "validation.json"
    vrec.write_bytes((vout / "validation.json").read_bytes())
    carried = {
        "head_weights_sha256": "H",
        "validation_record": "validation.json",
        "validation_sha256": hashlib.sha256(vrec.read_bytes()).hexdigest(),
    }
    (dd / "carried.json").write_text(json.dumps(carried))
    assert main([*base, "--split", "test", "--out", str(tout)]) == 0
    assert json.loads((tout / "verdict.json").read_text())["overall"] == PASS
    # a partial split is refused (FR-032)
    (dd / "test-digest.json").write_text(
        json.dumps({"dataset_digest": "T", "sigma1_scenarios": n // 4 + 1})
    )
    assert main([*base, "--split", "test", "--out", str(tout)]) == 2
