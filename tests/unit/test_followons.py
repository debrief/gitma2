"""The Gate 2 panel's process follow-ons (spec 008 T033): the test-coverage assertion (G10), the
merge counts (G11), the shuffled rule's source (G9) and the settings prediction headers bind."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tma2.calib.gate import shuffled_rule_from
from tma2.cli.g2 import coverage_errors
from tma2.cli.g2predict import bound_settings
from tma2.data.merge import ordinal_errors


def test_test_scoring_must_cover_the_split() -> None:
    td = {"dataset_digest": "d", "sigma1_scenarios": 4983}
    assert coverage_errors(td, 0, 4983) == []
    assert len(coverage_errors(td, 0, 4000)) == 1
    assert len(coverage_errors(td, 10, 4973)) == 2
    assert coverage_errors({"dataset_digest": "d"}, 0, 1) != []


def test_merge_refuses_gaps_duplicates_and_strays() -> None:
    assert ordinal_errors("m", range(5, 10), 5, 10) == []
    assert "missing" in ordinal_errors("m", [5, 6, 8, 9], 5, 10)[0]
    assert "duplicate" in ordinal_errors("m", [5, 6, 7, 7, 8, 9], 5, 10)[0]
    assert "outside" in ordinal_errors("m", [*range(5, 10), 11], 5, 10)[0]


def test_shuffled_rule_is_read_by_digest(tmp_path: Path) -> None:
    v = tmp_path / "validation.json"
    v.write_text(json.dumps({"shuffled_rule": "pass"}))
    sha = hashlib.sha256(v.read_bytes()).hexdigest()
    assert shuffled_rule_from(v, sha) == "pass"
    with pytest.raises(ValueError, match="SHA-256"):
        shuffled_rule_from(v, "0" * 64)
    v.write_text(json.dumps({"shuffled_rule": "maybe"}))
    with pytest.raises(ValueError, match="pass or fail"):
        shuffled_rule_from(v, hashlib.sha256(v.read_bytes()).hexdigest())


def test_headers_bind_control_settings(tmp_path: Path) -> None:
    seg = tmp_path / "c.ndjson"
    seg.write_text("{}\n")
    a = bound_settings({"kind": "veto", "veto_window": 6, "fade": [0.73, -0.0079]}, seg)
    b = bound_settings({"fade": [0.73, -0.0079], "veto_window": 6, "kind": "veto"}, seg)
    assert a == b  # canonical: key order does not matter
    assert a["segmentation_sha256"] == hashlib.sha256(b"{}\n").hexdigest()
    c = bound_settings({"kind": "veto", "veto_window": 7, "fade": [0.73, -0.0079]}, seg)
    assert c["model_settings"] != a["model_settings"]
