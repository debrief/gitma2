"""Spec 021: live mode's install step (scenario files, graphs, manifest digests)."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from tma2.cli.viewer_dump import install


def test_install_writes_scenarios_graphs_and_digests(tmp_path: Path) -> None:
    viewer, dump, es, layer = (tmp_path / n for n in ("viewer", "dump", "es", "layer"))
    for d in (viewer, dump, es, layer):
        d.mkdir()
    for d, blob in ((es, b"es-graph"), (layer, b"layer-graph")):
        (d / "model.onnx").write_bytes(blob)
        (d / "python_leg.json").write_text(json.dumps({"max_rel_diff": {"x": 1e-9}}))
    (viewer / "manifest.json").write_text(
        json.dumps({"files": {}, "model": {}, "engagements": [{"id": 0, "ordinal": 7}]})
    )
    doc = {
        "ordinal": 7,
        "zig_index": 3,
        "sigma": 0.017,
        "own": [[0.0, 1.0, 2.0, 0.5, 5.0], [10.0, 1.0, 2.0, 0.5, 5.0]],
        "obs": [[0.0, 1.2, 1.0], [10.0, 1.3, 0.0]],
        "e": {"intervals": {"1": [[0, 0, 1, False]]}, "decisions": []},
    }
    (dump / "scenario-7.json.gz").write_bytes(gzip.compress(json.dumps(doc).encode(), mtime=0))
    install(dump, viewer, es, layer)
    man = json.loads((viewer / "manifest.json").read_text())
    assert man["engagements"][0]["scenario"] == "scenario-0.json.gz"
    for f in ("es.onnx", "layer.onnx", "scenario-0.json.gz"):
        assert man["files"][f] == hashlib.sha256((viewer / f).read_bytes()).hexdigest()
    scen = json.loads(gzip.decompress((viewer / "scenario-0.json.gz").read_bytes()))
    assert scen["dt_s"] == 10.0 and scen["python_e_intervals"] == {"1": [[0, 0, 1, False]]}
    assert scen["own"] == doc["own"] and scen["obs"] == doc["obs"]


def test_install_refuses_an_out_of_tolerance_graph(tmp_path: Path) -> None:
    import pytest

    viewer, dump, es, layer = (tmp_path / n for n in ("viewer", "dump", "es", "layer"))
    for d in (viewer, dump, es, layer):
        d.mkdir()
    (es / "model.onnx").write_bytes(b"x")
    (es / "python_leg.json").write_text(json.dumps({"max_rel_diff": {"x": 1e-3}}))
    (viewer / "manifest.json").write_text(json.dumps({"files": {}, "model": {}, "engagements": []}))
    with pytest.raises(SystemExit):
        install(dump, viewer, es, layer)
