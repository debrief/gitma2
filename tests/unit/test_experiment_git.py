"""The experiment's own files do not make the record dirty (P0 run r3 recorded git_dirty: true
only because tma2-p0 had written into its folder before the manifest)."""

from __future__ import annotations

import shutil

from tma2.eval.experiment import ROOT, Experiment


def test_own_folder_does_not_dirty_the_record() -> None:
    folder = ROOT / "experiments" / "_test-git-state"
    shutil.rmtree(folder, ignore_errors=True)
    exp = Experiment(id="t", folder=folder)
    _, start_dirty = exp.git()
    folder.mkdir(parents=True)
    try:
        (folder / "artefact.json").write_text("{}")
        _, dirty = exp.git()
        assert dirty == start_dirty
    finally:
        shutil.rmtree(folder, ignore_errors=True)
