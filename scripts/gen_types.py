#!/usr/bin/env python3
"""Generate Pydantic models and JSON Schema from ``schema/tma.yaml`` (constitution I).

Usage: ``uv run python scripts/gen_types.py [--check]``. With ``--check`` nothing is written: the
generators run into a temporary directory and the result is compared with the committed files;
exit 1 names any stale file. CI runs the check; developers run without it after a schema edit.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "tma.yaml"
OUT_DIR = ROOT / "src" / "tma2" / "types" / "generated"
FILES = ("tma.py", "tma.schema.json", "version.py")

HEADER = "# Generated from schema/tma.yaml by scripts/gen_types.py. Do not edit.\n"


def run(args: list[str]) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, cwd=ROOT).stdout


def schema_version() -> str:
    m = re.search(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", SCHEMA.read_text(), re.M)
    if m is None:
        raise SystemExit("schema/tma.yaml has no version line")
    return m.group(1)


def generate(into: Path) -> None:
    into.mkdir(parents=True, exist_ok=True)
    pyd = run(["gen-pydantic", str(SCHEMA)])
    # The generator records the schema's absolute path; make it repository-relative so the
    # committed output is the same on every machine (CI's staleness check).
    pyd = pyd.replace(str(SCHEMA), "schema/tma.yaml").replace(str(ROOT) + "/", "")
    (into / "tma.py").write_text(HEADER + pyd)
    js = run(["gen-json-schema", str(SCHEMA)])
    (into / "tma.schema.json").write_text(js if js.endswith("\n") else js + "\n")
    (into / "version.py").write_text(HEADER + f'SCHEMA_VERSION = "{schema_version()}"\n')


def check() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp)
        generate(fresh)
        stale = 0
        for name in FILES:
            committed = OUT_DIR / name
            if not committed.exists():
                print(f"stale: {committed.relative_to(ROOT)} is missing", file=sys.stderr)
                stale += 1
                continue
            a = committed.read_text().splitlines(keepends=True)
            b = (fresh / name).read_text().splitlines(keepends=True)
            if a != b:
                stale += 1
                print(f"stale: {committed.relative_to(ROOT)}", file=sys.stderr)
                sys.stderr.writelines(difflib.unified_diff(a, b, "committed", "fresh", n=1))
        if stale:
            print(f"{stale} generated file(s) stale; run scripts/gen_types.py", file=sys.stderr)
            return 1
    print("generated types are up to date")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        return check()
    generate(OUT_DIR)
    for name in FILES:
        print(f"wrote {(OUT_DIR / name).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
