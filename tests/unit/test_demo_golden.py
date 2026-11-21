"""Spec 035: the committed golden least-squares vectors are Python's reference solutions.

The problems are rebuilt by the page's own code in Node (``conformance/onnx/demo_problems.mjs``);
the test is skipped where Node is missing. ``demo_node.mjs`` checks the JavaScript port against
the same file.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONF = ROOT / "conformance" / "onnx"


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node")
def test_golden_ls_is_pythons(tmp_path: Path) -> None:
    import importlib.util

    raw = subprocess.run(
        ["node", "demo_problems.mjs"], cwd=CONF, capture_output=True, check=True
    ).stdout
    (tmp_path / "problems.json").write_bytes(raw)
    spec = importlib.util.spec_from_file_location("demo_golden", CONF / "demo_golden.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main([str(tmp_path / "problems.json"), str(tmp_path / "golden.json")])
    fresh = json.loads((tmp_path / "golden.json").read_text())
    committed = json.loads((CONF / "demo" / "golden-ls.json").read_text())
    assert fresh["problems_sha256"] == committed["problems_sha256"]
    for k, g in committed["solutions"].items():
        f = fresh["solutions"][k]
        assert f["iterations"] == g["iterations"] and f["converged"] == g["converged"], k
        for a, b in zip(f["theta"], g["theta"], strict=True):
            assert abs(a - b) <= 1e-7 * max(1.0, abs(b)), k


def test_golden_spans_are_pythons(tmp_path: Path) -> None:
    """The committed golden spans are spans_from_logit on the committed golden logits."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("demo_spans_golden", CONF / "demo_spans_golden.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main([str(CONF / "demo" / "golden-tlm.json"), str(tmp_path / "spans.json")])
    fresh = json.loads((tmp_path / "spans.json").read_text())
    committed = json.loads((CONF / "demo" / "golden-spans.json").read_text())
    assert fresh == committed
    assert sum(len(c["spans"]) for c in committed["cases"].values()) > 0
