"""``python -m tma2.cli.hmerge``: join the shards of one ``tma2-hpredict`` estimator.

Shards are prediction files of the same estimator over consecutive ordinal ranges of one split.
Their headers must agree in everything but the range; the merged header states the whole range.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tma2.data.canonical import canonical_json

RANGE = ("ordinal_start", "ordinal_count")


def merge(paths: list[str], out: str) -> int:
    parts = []
    for p in paths:
        lines = Path(p).read_text(encoding="utf-8").splitlines()
        parts.append((json.loads(lines[0]), lines[1:]))
    parts.sort(key=lambda x: int(x[0]["ordinal_start"]))
    head = dict(parts[0][0])
    same = {k: v for k, v in head.items() if k not in RANGE}
    seen: set[int] = set()
    end = int(head["ordinal_start"])
    records: list[str] = []
    for h, lines in parts:
        if {k: v for k, v in h.items() if k not in RANGE} != same:
            raise ValueError("the shards' headers differ beyond their ordinal ranges")
        if int(h["ordinal_start"]) != end:
            raise ValueError("the shards' ordinal ranges are not consecutive")
        end += int(h["ordinal_count"])
        for line in lines:
            j = int(json.loads(line)["ordinal"])
            if j in seen:
                raise ValueError(f"ordinal {j} appears in two shards")
            seen.add(j)
            records.append(line)
    head["ordinal_count"] = end - int(head["ordinal_start"])
    Path(out).write_text(canonical_json(head) + "\n" + "".join(r + "\n" for r in records))
    return len(records)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tma2.cli.hmerge", description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("shards", nargs="+")
    a = ap.parse_args(argv)
    try:
        n = merge(a.shards, a.out)
    except (ValueError, KeyError, OSError) as e:
        print(f"hmerge: {e}", file=sys.stderr)
        return 2
    print(f"wrote {a.out}: {n} scenarios from {len(a.shards)} shards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
