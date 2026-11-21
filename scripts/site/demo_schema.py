#!/usr/bin/env python3
"""The demonstrator's JSON Schema for DemoScenario (spec 035 FR-043).

Usage: ``uv run python scripts/site/demo_schema.py [--check]``. Extracts ``DemoScenario`` and the
classes it uses from the LinkML-generated ``src/tma2/types/generated/tma.schema.json`` into
``site/static/demo-data/demo-scenario.schema.json``, the schema the page validates imports
against. ``--check`` writes nothing and exits 1 when the committed file is stale.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "tma2" / "types" / "generated" / "tma.schema.json"
OUT = ROOT / "site" / "static" / "demo-data" / "demo-scenario.schema.json"
TOP = "DemoScenario"


def refs(node: Any) -> set[str]:
    if isinstance(node, dict):
        out = {node["$ref"].split("/")[-1]} if "$ref" in node else set()
        for v in node.values():
            out |= refs(v)
        return out
    if isinstance(node, list):
        return set().union(*(refs(v) for v in node)) if node else set()
    return set()


def build() -> str:
    full = json.loads(SRC.read_text())
    defs = full["$defs"]
    need, todo = set(), [TOP]
    while todo:
        name = todo.pop()
        if name in need:
            continue
        need.add(name)
        todo.extend(refs(defs[name]) - need)
    top = defs[TOP]
    schema = {
        "$schema": full["$schema"],
        "$id": full["$id"] + "/DemoScenario",
        "title": TOP,
        "description": top["description"],
        "version": full["version"],
        "type": "object",
        "additionalProperties": False,
        "properties": top["properties"],
        "required": top["required"],
        "$defs": {n: defs[n] for n in sorted(need - {TOP})},
    }
    return json.dumps(schema, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = build()
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(
                f"stale: {OUT.relative_to(ROOT)} (run scripts/site/demo_schema.py)", file=sys.stderr
            )
            return 1
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
