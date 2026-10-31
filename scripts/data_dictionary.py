#!/usr/bin/env python3
"""Generate ``site/docs/data-dictionary.md`` from ``schema/tma.yaml`` (constitution I).

Mirrors gitma's ``site/scripts/prebuild.mjs`` data-dictionary step: ``gen-markdown-datadict``
output with its H1 and empty Mermaid blocks removed and slot anchors qualified by class, preceded
by a units table. Never hand-edited; the site's prebuild runs this.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "tma.yaml"
OUT = ROOT / "site" / "docs" / "data-dictionary.md"


def run(args: list[str]) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, cwd=ROOT).stdout


def units_table() -> str:
    schema = yaml.safe_load(SCHEMA.read_text())
    rows: list[tuple[str, str, str]] = []
    for cls_name, cls in (schema.get("classes") or {}).items():
        for slot_name, slot in (cls.get("attributes") or {}).items():
            unit = (slot or {}).get("unit") or {}
            code = unit.get("ucum_code")
            if code:
                rows.append((cls_name, slot_name, code))
    lines = ["| Class | Slot | Unit (UCUM) |", "| --- | --- | --- |"]
    lines += [f"| {c} | `{s}` | `{u}` |" for c, s, u in sorted(rows)]
    return "\n".join(lines)


def mdx_safe(md: str) -> str:
    """Escape ``<`` and ``{`` outside code spans so MDX does not read them as JSX/expressions."""
    parts = re.split(r"(`[^`\n]*`)", md)
    for i in range(0, len(parts), 2):
        # Keep the generator's own HTML (sub, a, br, ...); escape everything else that looks
        # like a tag, such as <split> or <x> placeholders in descriptions.
        parts[i] = re.sub(
            r"<(?!/?(?:sub|sup|a|br|b|i|em|strong|code|p|span|div)\b)", "&lt;", parts[i]
        )
        parts[i] = parts[i].replace("{", "&#123;").replace("}", "&#125;")
    return "".join(parts)


def main() -> None:
    md = run(["gen-markdown-datadict", "--anchor-style", "mkdocs", str(SCHEMA)])
    md = re.sub(r"^# .*\n", "", md, count=1, flags=re.M)
    md = re.sub(r"```mermaid\n(classDiagram|erDiagram)\n(\s*\w+ \{\s*\}\s*)*```\n?", "", md)
    md = re.sub(r"^## Class Diagram\s*\n(?=## )", "", md, flags=re.M)
    sections = re.split(r"(?=^### )", md, flags=re.M)
    out_sections = []
    for section in sections:
        m = re.match(r"^### (\w+)", section)
        if m is None:
            out_sections.append(section)
            continue
        cls = m.group(1).lower()

        def qualify(link: re.Match[str], cls: str = cls) -> str:
            slot = link.group(1)
            return f"](#{cls}__{slot})" if f'id="{cls}__{slot}"' in md else link.group(0)

        out_sections.append(re.sub(r"\]\(#([a-z0-9_]+)\)", qualify, section))
    front = "\n".join(
        [
            "---",
            "title: Data dictionary",
            "description: Every LinkML class and slot, generated from schema/tma.yaml.",
            "---",
            "",
            ":::info Generated",
            "Generated from `schema/tma.yaml` at build time by `scripts/data_dictionary.py`. "
            "Do not edit; change the schema.",
            ":::",
            "",
            "## Units",
            "",
            units_table(),
            "",
        ]
    )
    body = mdx_safe("".join(out_sections))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(front + body)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
