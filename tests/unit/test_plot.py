"""tma2-plot: track and error figures with provenance sidecars (AGENTS.md, Reporting)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from tma2.cli import plot as cli
from tma2.cli.estimators import open_split
from tma2.eval.errors import Truth
from tma2.eval.predictions import PredictionWriter
from tma2.report.plots import EstimatorRows, ellipse_from_cov


def _first_truth(pack: Path) -> Truth:
    _, blocks = open_split(pack)
    _, meta, own, tgt, _ = next(iter(blocks))
    return Truth.from_block(meta, own, tgt)


def _write_predictions(pack: Path, out: Path, truth: Truth, offset_m: float, cov: bool) -> Path:
    """A per-timestep file whose rows sit ``offset_m`` east of the target, from the zig on; the
    row before the zig is deliberately implausible (range 0) and must be masked."""
    w = PredictionWriter(out, "shifted", "per_timestep", pack)
    rows = []
    for k in range(max(0, truth.zig_index - 1), truth.samples):
        o, g = truth.own[k], truth.tgt[k]
        x, y = g[1] + offset_m, g[2]
        row: dict[str, Any] = {
            "timestamp_s": float(o[0]),
            "range_m": math.hypot(x - o[1], y - o[2]) if k >= truth.zig_index else 0.0,
            "course_rad": float(g[3]),
            "speed_mps": float(g[4]),
            "x_m": float(x),
            "y_m": float(y),
            "converged": True,
        }
        if cov:
            row["cov_xyvv"] = [4e4, 1e4, 0, 0, 9e4, 0, 0, 1, 0, 1]
            row["cov_ok"] = True
        rows.append(row)
    w.write(
        {
            "record": "prediction",
            "scenario_index": truth.index,
            "estimator": "shifted",
            "mode": "per_timestep",
            "rows": rows,
        }
    )
    w.close()
    return out


def test_track_and_errors_figures(man2_pack: Path, tmp_path: Path) -> None:
    truth = _first_truth(man2_pack)
    a = _write_predictions(man2_pack, tmp_path / "a.ndjson", truth, 300.0, cov=True)
    b = _write_predictions(man2_pack, tmp_path / "b.ndjson", truth, -500.0, cov=False)
    at = f"{truth.zig_time_s + 300:.0f},{truth.zig_time_s + 600:.0f}"
    common = [
        "--truth",
        str(man2_pack),
        "--predictions",
        str(a),
        str(b),
        "--labels",
        "A,B",
        "--scenario",
        str(truth.index),
    ]
    out = tmp_path / "fig" / "track.svg"
    assert cli.main(["track", *common, "--at", at, "--out", str(out)]) == 0
    svg = out.read_text()
    assert "A @" in svg and "ownship zig" in svg  # the annotations and the legend are text
    side = json.loads(out.with_suffix(".svg.json").read_text())
    assert side["scenario_index"] == truth.index
    assert [p["path"] for p in side["predictions"]] == [str(a), str(b)]
    assert len(side["truth"]["sha256"]) == 64
    err = tmp_path / "fig" / "errors.svg"
    assert cli.main(["errors", *common, "--out", str(err)]) == 0
    assert err.exists() and err.with_suffix(".svg.json").exists()


def test_usage_and_data_errors(man2_pack: Path, tmp_path: Path, capsys: object) -> None:
    truth = _first_truth(man2_pack)
    a = _write_predictions(man2_pack, tmp_path / "a.ndjson", truth, 300.0, cov=True)
    base = [
        "track",
        "--truth",
        str(man2_pack),
        "--predictions",
        str(a),
        "--out",
        str(tmp_path / "x.svg"),
    ]
    assert cli.main([*base, "--scenario", "99999"]) == 2  # not in the split
    assert cli.main([*base, "--scenario", str(truth.index), "--labels", "a,b"]) == 2


def test_ellipse_from_cov() -> None:
    e = ellipse_from_cov({"cov_xyvv": [4e4, 0, 0, 0, 1e4, 0, 0, 1, 0, 1], "cov_ok": True})
    assert e is not None and math.isclose(e[0], 400.0) and math.isclose(e[1], 200.0)
    assert (
        ellipse_from_cov({"cov_xyvv": [4e4, 0, 0, 0, 1e4, 0, 0, 1, 0, 1], "cov_ok": False}) is None
    )
    assert ellipse_from_cov({}) is None
    assert ellipse_from_cov({"cov_xyvv": [math.nan] * 10}) is None


def test_at_picks_nearest_row() -> None:
    rows = [{"timestamp_s": float(t)} for t in (0, 10, 20)]
    e = EstimatorRows("x", rows)
    assert e.at(12.0, 5.0) == rows[1]
    assert e.at(16.0, 5.0) == rows[2]
    assert e.at(40.0, 5.0) is None


def test_demo_split_bound_to_parent(man2_pack: Path, tmp_path: Path) -> None:
    """Predictions bound to a parent split plot on a demo split cut from it only with --bound-to
    naming that parent (recorded in the sidecar); an E-style header (extra fields) is read too."""
    truth = _first_truth(man2_pack)
    a = _write_predictions(man2_pack, tmp_path / "a.ndjson", truth, 300.0, cov=True)
    lines = a.read_text().splitlines()
    h = json.loads(lines[0])
    h["code_sha256"] = "x"  # an EPredictionHeader-only field
    a.write_text("\n".join([json.dumps(h), *lines[1:]]) + "\n")
    import runpy
    import sys

    script = Path(__file__).resolve().parents[2] / "scripts/research/g3_demo_split.py"
    from tma2.segment.score import iter_selected

    j = next(j for j, m, *_ in iter_selected(man2_pack, 0, 10**6) if int(m["index"]) == truth.index)
    argv = sys.argv
    sys.argv = [
        "g3_demo_split",
        "--pack",
        str(man2_pack),
        "--ordinals",
        str(j),
        "--out",
        str(tmp_path),
    ]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as e:
        assert e.code == 0
    finally:
        sys.argv = argv
    demo = tmp_path / "demo.f32pack"
    base = ["track", "--truth", str(demo), "--predictions", str(a), "--scenario", str(truth.index)]
    assert cli.main([*base, "--out", str(tmp_path / "x.svg")]) == 2
    # --bound-to must be the split the demo split names as its parent
    assert cli.main([*base, "--bound-to", str(demo), "--out", str(tmp_path / "z.svg")]) == 2
    out = tmp_path / "y.svg"
    assert cli.main([*base, "--bound-to", str(man2_pack), "--out", str(out)]) == 0
    side = json.loads(out.with_suffix(".svg.json").read_text())
    assert side["bound_to"]["path"] == str(man2_pack)
