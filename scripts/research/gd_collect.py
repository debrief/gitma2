"""Spec 038: copy a stage's scoring runs from their results branches into a record.

    uv run python scripts/research/gd_collect.py dev-a experiments/<record> [--errors-dir <dir>]

For each split and condition of the stage (configs/gd/protocol.json) the newest branch
``results/headroom-gd-<stage>-<split>-<condition>-plan-<run id>`` is fetched and its small
files copied to ``<record>/runs/<split>/<condition>/``. ``--errors-dir`` also saves each run's
errors.npz and C″ segmentation dump outside the repository (too large to commit).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMALL = ("decomp.json", "decomp-logs.npz", "headroom.json", "run.json", "data-digests.json")
LARGE = ("errors.npz", "segmentations/c2.ndjson.gz")


def git(*a: str, text: bool = True) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    return subprocess.run(["git", *a], check=True, capture_output=True, text=text, cwd=ROOT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("record")
    ap.add_argument("--errors-dir")
    ap.add_argument("--protocol", default="configs/gd/protocol.json")
    ap.add_argument("--name", default="gd", help="the plans' prefix: <name>-<stage>-<split>")
    a = ap.parse_args()
    proto = json.loads((ROOT / a.protocol).read_text())
    missing = []
    for split, conds in proto["stages"][a.stage]["splits"].items():
        for cond in conds:
            name = f"{a.name}-{a.stage}-{split}"
            pat = f"refs/heads/results/headroom-{name}-{cond}-plan-*"
            refs = [ln.split()[1] for ln in git("ls-remote", "origin", pat).stdout.splitlines()]
            if not refs:
                missing.append(f"{split}/{cond}")
                continue
            ref = sorted(refs, key=lambda r: int(r.rsplit("-", 1)[1]))[-1]
            run = ref.rsplit("-", 1)[1]
            git("fetch", "-q", "origin", ref)
            src = f"FETCH_HEAD:experiments/headroom-runs/{name}-{run}/{cond}/plan"
            out = ROOT / a.record / "runs" / split / cond
            out.mkdir(parents=True, exist_ok=True)
            for f in SMALL:
                r = subprocess.run(["git", "show", f"{src}/{f}"], capture_output=True, cwd=ROOT)
                if r.returncode == 0:
                    (out / f).write_bytes(r.stdout)
                elif f != "decomp-logs.npz":
                    missing.append(f"{split}/{cond}/{f}")
            if a.errors_dir:
                big = Path(a.errors_dir) / split / cond
                for f in LARGE:
                    r = subprocess.run(["git", "show", f"{src}/{f}"], capture_output=True, cwd=ROOT)
                    if r.returncode == 0:
                        (big / f).parent.mkdir(parents=True, exist_ok=True)
                        (big / f).write_bytes(r.stdout)
            print(split, cond, ref.removeprefix("refs/heads/"))
    if missing:
        raise SystemExit("missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()
