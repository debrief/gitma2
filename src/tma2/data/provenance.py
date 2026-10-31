"""Git provenance of the code that produced a file (gitma ``packages/data/src/provenance.ts``)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class GitProvenance:
    commit: str
    dirty: bool
    in_git: bool


def read_git_provenance(cwd: Path = PACKAGE_DIR) -> GitProvenance:
    """Commit and tree state together, read once before any output is written."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return GitProvenance(commit="unknown", dirty=True, in_git=False)
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=cwd, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = status != ""
    except (OSError, subprocess.CalledProcessError):
        dirty = True
    return GitProvenance(commit=commit, dirty=dirty, in_git=True)


class ProvenanceError(ValueError):
    """A refusal on provenance grounds (exit 2, like any refused input)."""


def generator_provenance(p: GitProvenance, allow_dirty: bool) -> tuple[str, bool]:
    """(commit, dirty) to record; refuses a dirty tree or a non-git checkout unless allowed."""
    if not allow_dirty and not p.in_git:
        raise ProvenanceError(
            "not in a git checkout: dataset provenance cannot be recorded; pass --allow-dirty to "
            "generate anyway (recorded as generator_git_dirty: true)"
        )
    if not allow_dirty and p.dirty:
        raise ProvenanceError(
            "working tree has uncommitted changes: commit first, or pass --allow-dirty "
            "(recorded as generator_git_dirty: true)"
        )
    return p.commit, p.dirty or not p.in_git
