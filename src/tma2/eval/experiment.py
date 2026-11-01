"""Experiment folders: manifest, checks and verdict (gitma's ``experiment.ts`` layout)."""

from __future__ import annotations

import datetime as dt
import json
import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tma2.data.canonical import canonical_json
from tma2.data.io import AtomicFile, file_digest
from tma2.sim.version import GENERATOR_VERSION
from tma2.types import SCHEMA_VERSION

from .generated_types import ExperimentManifest, GateVerdict

ROOT = Path(__file__).resolve().parents[3]
PACKAGES = ("numpy", "numba", "torch", "onnx", "onnxruntime", "pydantic", "onnxscript")


def run_environment() -> dict[str, Any]:
    """Package versions, the uv.lock digest, CPU model and thread counts."""
    from importlib import metadata

    pkgs = []
    for name in PACKAGES:
        try:
            pkgs.append({"name": name, "version": metadata.version(name)})
        except metadata.PackageNotFoundError:
            continue
    env: dict[str, Any] = {"packages": pkgs, "cpu_count": os.cpu_count() or 0}
    lock = ROOT / "uv.lock"
    if lock.exists():
        env["lockfile_digest"] = file_digest(lock)
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                env["cpu_model"] = line.split(":", 1)[1].strip()
                break
    except OSError:
        env["cpu_model"] = platform.processor() or "unknown"
    try:
        import torch

        env["torch_threads"] = torch.get_num_threads()
    except ImportError:
        pass
    return env


@dataclass
class Check:
    name: str
    result: str  # pass | fail | inconclusive | skipped
    detail: str
    value: float | None = None
    threshold: float | None = None
    threshold_low: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    ci_level: float | None = None

    def as_record(self) -> dict[str, Any]:
        rec: dict[str, Any] = {"name": self.name, "result": self.result, "detail": self.detail}
        for key in ("value", "threshold", "threshold_low", "ci_low", "ci_high", "ci_level"):
            v = getattr(self, key)
            if v is not None:
                rec[key] = float(v)
        return rec


@dataclass
class Experiment:
    id: str
    folder: Path
    datasets: list[dict[str, Any]] = field(default_factory=list)
    estimators: list[dict[str, str]] = field(default_factory=list)
    command_lines: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    artefacts: list[dict[str, str]] = field(default_factory=list)

    def add_artefact(self, path: str | Path, role: str) -> str:
        """Record a file the experiment read or wrote (prediction caches, conformance results)."""
        digest = file_digest(path)
        shown = Path(path).resolve()
        try:
            shown = shown.relative_to(ROOT)
        except ValueError:
            pass
        self.artefacts.append({"path": str(shown), "digest": digest, "role": role})
        return digest

    def add_dataset(self, path: str | Path, header: Any) -> None:
        shown = Path(path).resolve()
        try:
            shown = shown.relative_to(ROOT)
        except ValueError:
            pass
        self.datasets.append({"path": str(shown), "header": header, "digest": file_digest(path)})

    def add_estimator(self, name: str, settings: dict[str, Any]) -> None:
        self.estimators.append(
            {"name": name, "settings_json": json.dumps(settings, sort_keys=True)}
        )

    def __post_init__(self) -> None:
        # The tree's state when the run starts; files the run writes into its own experiment
        # folder do not make it dirty (P0 run r3 recorded dirty only because of those).
        self._start = self._git_now()

    def git(self) -> tuple[str, bool]:
        """(commit, dirty): dirty if the tree was dirty at the start or anything outside this
        experiment's folder changed since."""
        commit, dirty = self._git_now()
        start_commit, start_dirty = self._start
        return start_commit, start_dirty or dirty or commit != start_commit

    def _git_now(self) -> tuple[str, bool]:
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            ).stdout.strip()
            dirty = (
                subprocess.run(
                    ["git", "status", "--porcelain", "--", ".", *self._exclude()],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=ROOT,
                ).stdout.strip()
                != ""
            )
            return commit, dirty
        except (OSError, subprocess.CalledProcessError):
            return "unknown", True

    def _exclude(self) -> list[str]:
        try:
            rel = Path(self.folder).resolve().relative_to(ROOT)
        except ValueError:
            return []
        return [f":(exclude){rel}"]

    def verdict_result(self) -> str:
        gated = [c for c in self.checks if c.result != "skipped"]
        if any(c.result == "fail" for c in gated):
            return "fail"
        if any(c.result == "inconclusive" for c in gated):
            return "inconclusive"
        return "pass"

    def write(self, gate: str, decided_by: str = "machine") -> dict[str, Any]:
        self.folder.mkdir(parents=True, exist_ok=True)
        commit, dirty = self.git()
        manifest = {
            "id": self.id,
            "created": dt.datetime.now(dt.UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "git_commit": commit,
            "git_dirty": dirty,
            "python_version": platform.python_version(),
            "schema_version": SCHEMA_VERSION,
            "generator_version": GENERATOR_VERSION,
            "datasets": self.datasets,
            "estimators": self.estimators,
            "command_lines": self.command_lines,
            "environment": run_environment(),
            "artefacts": self.artefacts,
        }
        try:
            import torch

            manifest["torch_version"] = torch.__version__
        except ImportError:
            pass
        ExperimentManifest.model_validate(manifest)
        verdict = {
            "gate": gate,
            "result": self.verdict_result(),
            "checks": [c.as_record() for c in self.checks],
            "decided_by": decided_by,
        }
        GateVerdict.model_validate(verdict)
        for name, obj in (
            ("manifest.json", manifest),
            ("verdict.json", verdict),
            ("metrics.json", self.metrics),
        ):
            f = AtomicFile(self.folder / name)
            f.write((json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            f.commit()
        lines = ["name,result,value,threshold,threshold_low,ci_low,ci_high,detail"]
        for c in self.checks:
            cells = [c.name, c.result] + [
                "" if v is None else repr(float(v))
                for v in (c.value, c.threshold, c.threshold_low, c.ci_low, c.ci_high)
            ]
            detail = '"' + c.detail.replace('"', '""') + '"'
            lines.append(",".join(cells + [detail]))
        f = AtomicFile(self.folder / "checks.csv")
        f.write(("\n".join(lines) + "\n").encode("utf-8"))
        f.commit()
        return verdict


__all__ = ["Check", "Experiment", "canonical_json"]
