"""``tma2-plan``: the training workflow's plan helper (spec 003 T017; research R7).

    tma2-plan resolve --ref <branch or plan path>     key=value lines for $GITHUB_OUTPUT
    tma2-plan data --plan <plan.json> --out <dir> [--keep train.f32pack]
                                                      regenerate the validation split, check digest
    tma2-plan complete --checkpoint <dir>             exit 0 if the checkpoint is complete

``data`` regenerates the plan's validation split at the commit its header names (the header
records the generating commit, so only that commit reproduces the file's digest), with the
ranges files the header's command names by digest, and refuses a digest that differs from the
plan's. Only the validation split is kept: the training stream is generated on the fly and the
other splits are not needed (and must not be at hand) for training or validation scoring.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from tma2.data.io import file_digest
from tma2.models.train import load_plan
from tma2.types import RecordError, parse_record
from tma2.types.generated.tma import CheckpointMeta

SEARCH = ("configs", "tests/fixtures")


def find_plan(ref: str, root: Path) -> Path:
    """``train/<id>`` → the plan under ``configs/`` whose id is ``<id>``; a path is used as is."""
    if ref.endswith(".json"):
        return Path(ref)
    plan_id = ref.removeprefix("train/")
    hits = []
    for p in sorted((root / "configs").rglob("plan.json")):
        try:
            if json.loads(p.read_text()).get("id") == plan_id:
                hits.append(p)
        except json.JSONDecodeError:
            continue
    if len(hits) != 1:
        raise ValueError(f"{len(hits)} plans under configs/ have id {plan_id!r}")
    return hits[0].relative_to(root)


def _by_digest(digest: str, root: Path) -> Path:
    for top in SEARCH:
        for p in sorted((root / top).rglob("*.json")):
            if file_digest(p) == digest:
                return p.resolve()
    raise ValueError(f"no file under {', '.join(SEARCH)} has digest {digest}")


def regenerate(plan_path: Path, out: Path, root: Path, keep: tuple[str, ...] = ()) -> Path:
    plan, _ = load_plan(plan_path)
    header = plan.validation.header
    commit = header.generator_git_commit
    if not commit or header.generator_git_dirty:
        raise ValueError("the plan's validation split was not generated from a clean commit")
    args = shlex.split(header.created_by or "")
    if not args or args[0] != "tma2-generate":
        raise ValueError(f"unexpected created_by: {header.created_by!r}")
    cmd = []
    for a in args[1:]:
        cmd.append(
            str(_by_digest(a.removeprefix("sha256:"), root)) if a.startswith("sha256:") else a
        )
    if "--format" not in cmd:
        cmd += ["--format", "f32pack"]
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "gen"
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), commit], check=True)
        try:
            subprocess.run(
                ["uv", "run", "--quiet", "tma2-generate", *cmd, "--out", str(out.resolve())],
                cwd=wt,
                check=True,
            )
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], check=False)
    name = Path(plan.validation.path).name
    got = file_digest(out / name)
    if plan.validation.digest and got != plan.validation.digest:
        raise ValueError(f"{out / name}: digest {got} is not the plan's {plan.validation.digest}")
    for p in out.iterdir():
        if p.name != name and p.name not in keep:
            p.unlink()
    return out / name


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2-plan")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("--ref", required=True)
    d = sub.add_parser("data")
    d.add_argument("--plan", required=True)
    d.add_argument("--out", required=True)
    d.add_argument(
        "--keep", action="append", default=[], help="also keep this split file (e.g. train.f32pack)"
    )
    c = sub.add_parser("complete")
    c.add_argument("--checkpoint", required=True)
    a = ap.parse_args(argv)
    root = Path.cwd()
    try:
        if a.cmd == "resolve":
            path = find_plan(a.ref, root)
            plan, digest = load_plan(path)
            print(f"plan={path}")
            print(f"id={plan.id}")
            print(f"digest={digest}")
            print(f"models={json.dumps([m.id for m in plan.models])}")
        elif a.cmd == "data":
            print(regenerate(Path(a.plan), Path(a.out), root, tuple(a.keep)))
        else:
            meta = Path(a.checkpoint) / "meta.json"
            done = meta.exists() and bool(
                parse_record(CheckpointMeta, json.loads(meta.read_text()), str(meta), 1).complete
            )
            print("complete" if done else "incomplete")
            return 0 if done else 1
    except (OSError, ValueError, RecordError, subprocess.CalledProcessError) as e:
        print(f"tma2-plan: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
