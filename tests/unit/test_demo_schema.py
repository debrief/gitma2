"""Spec 035: the demonstrator's DemoScenario schema and its presets' types."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tma2.types.generated.tma import DemoScenario

ROOT = Path(__file__).resolve().parents[2]


def test_site_schema_is_current() -> None:
    r = subprocess.run(
        [sys.executable, "scripts/site/demo_schema.py", "--check"], cwd=ROOT, capture_output=True
    )
    assert r.returncode == 0, r.stderr.decode()


def test_site_schema_names_demo_classes() -> None:
    s = json.loads((ROOT / "site/static/demo-data/demo-scenario.schema.json").read_text())
    assert s["title"] == "DemoScenario"
    assert set(s["$defs"]) == {"DemoLeg", "DemoTrack", "DemoWindow"}
    assert s["properties"]["sigma_deg"]["maximum"] == 5


def test_pydantic_accepts_a_scenario() -> None:
    leg = {"course_deg": 10.0, "speed_kt": 8.0, "duration_s": 600.0, "turn_rate_dps": 1.0}
    sc = DemoScenario.model_validate(
        {
            "schema_version": "0.39.0",
            "ownship": {"start_x_nm": 0.0, "start_y_nm": 0.0, "legs": [leg]},
            "target": {"start_x_nm": 1.0, "start_y_nm": 9.0, "legs": [leg]},
            "sigma_deg": 1.0,
            "interval_s": 5.0,
            "seed": 1,
            "window": {"start_s": 0.0, "end_s": 600.0},
            "solver": "ls-js",
        }
    )
    assert sc.target.legs[0].speed_kt == 8.0
