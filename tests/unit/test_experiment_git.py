"""The record's git state (P0 run r3; spec 003 FR-003): the experiment's own files do not make it
dirty; an edit outside the folder, or a commit made during the run, does."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tma2.eval.experiment import ROOT, Experiment


def _clone(tmp: Path) -> Path:
    dst = tmp / "repo"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{ROOT}", str(dst)], check=True)
    for k, v in (("user.email", "t@example.invalid"), ("user.name", "test")):
        subprocess.run(["git", "-C", str(dst), "config", k, v], check=True)
    return dst


def test_git_state_of_a_record(tmp_path: Path) -> None:
    repo = _clone(tmp_path)
    folder = repo / "experiments" / "_t"
    exp = Experiment(id="t", folder=folder, root=repo)
    start, dirty = exp.git()
    assert not dirty
    folder.mkdir(parents=True)
    (folder / "artefact.json").write_text("{}")
    assert exp.git() == (start, False)  # its own files: still clean
    readme = repo / "README.md"
    original = readme.read_text()
    readme.write_text(original + "edit\n")
    assert exp.git() == (start, True)  # an edit outside the folder
    readme.write_text(original)
    assert exp.git() == (start, False)
    (repo / "x.txt").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "x.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "during"], check=True)
    commit, dirty = exp.git()
    assert commit == start and dirty  # a commit during the run: dirty, the starting commit kept
