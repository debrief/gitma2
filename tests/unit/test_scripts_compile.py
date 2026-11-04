"""Every script under scripts/ compiles (mypy and the tests do not import them; a SyntaxError in
scripts/research/leg_spike.py once went unnoticed until review)."""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = sorted((ROOT / "scripts").rglob("*.py"))


@pytest.mark.parametrize("path", SCRIPTS, ids=[str(p.relative_to(ROOT)) for p in SCRIPTS])
def test_script_compiles(path: Path, tmp_path: Path) -> None:
    py_compile.compile(str(path), cfile=str(tmp_path / "out.pyc"), doraise=True)
