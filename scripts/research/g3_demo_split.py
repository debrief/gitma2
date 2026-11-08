"""Spec 008 slides: a small demo split of chosen validation scenarios, and the matching rows of
prediction files, for ``tma2-plot`` figures.

    uv run python scripts/research/g3_demo_split.py --pack <validation.f32pack> --ordinals 514,648 \
        --out <dir> [--predictions NAME=PATH ...]

Writes ``<dir>/demo.f32pack`` (the scenarios at those σ = 1° ordinals, in that order; the source
header kept but for the count and ``created_by``, which names this script and the parent's
SHA-256, so ``tma2-plot --bound-to`` can check the cut) and ``<dir>/<NAME>.ndjson`` (each
prediction file's header and its records of those scenarios, by ``scenario_index``). Prints each
ordinal's scenario index, which ``tma2-plot --scenario`` takes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--ordinals", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--predictions", nargs="*", default=[], metavar="NAME=PATH")
    a = ap.parse_args(argv)

    from tma2.data.f32pack import PackWriter, encode_block_arrays, read_pack_header
    from tma2.data.io import file_digest
    from tma2.segment.score import iter_selected

    want = [int(x) for x in a.ordinals.split(",")]
    if len(set(want)) != len(want):
        raise SystemExit("--ordinals lists an ordinal twice")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = {}
    for j, meta, own, tgt, obs in iter_selected(a.pack, min(want), max(want) - min(want) + 1):
        if j in want:
            blocks[j] = (meta, own, tgt, obs)
    missing = [j for j in want if j not in blocks]
    if missing:
        raise SystemExit(f"ordinals not in {a.pack}: {missing}")
    parent = file_digest(a.pack)
    header = read_pack_header(a.pack).model_copy(
        update={
            "scenario_count": len(want),
            "created_by": f"scripts/research/g3_demo_split.py ordinals {a.ordinals} of {parent}",
        }
    )
    w = PackWriter(out / "demo.f32pack", header)
    index = {}
    try:
        for j in want:
            meta, own, tgt, obs = blocks[j]
            index[j] = int(meta["index"])
            w.write_block(encode_block_arrays(meta, own, tgt, obs))
        w.close()
    except Exception:
        w.abort()
        raise
    keep = set(index.values())
    for spec in a.predictions:
        name, _, path = spec.partition("=")
        with open(path, encoding="utf-8") as fi, open(out / f"{name}.ndjson", "w") as fo:
            fo.write(fi.readline())
            for line in fi:
                if int(json.loads(line)["scenario_index"]) in keep:
                    fo.write(line)
    print(json.dumps({"scenario_index": {str(j): i for j, i in index.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
