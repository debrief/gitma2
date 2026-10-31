"""``tma2-generate``: write a dataset's splits (contract: specs/001 contracts/cli-tma2-generate.md).

Mirrors gitma's ``tma-generate`` options, refusals, exit codes and summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from tma2.data.dataset import Format, GenerateOptions, timed_generate
from tma2.data.io import file_digest
from tma2.data.provenance import ProvenanceError, generator_provenance, read_git_provenance
from tma2.sim.prng import parse_seed
from tma2.sim.ranges import DEFAULT_RANGES, HELDOUT_RANGES, RangesError, noise_free, validate_ranges
from tma2.types import ParameterRanges, dump_record, parse_record

USAGE = (
    "usage: tma2-generate --seed <uint64> --count <n> --out <dir> [--ranges f] "
    "[--heldout-ranges f] [--noise-free] [--allow-dirty] [--format f32pack|ndjson|both]"
)


class UsageError(Exception):
    pass


def load_ranges(path: str) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    model = parse_record(ParameterRanges, raw, path, "ranges")
    ranges = dump_record(model)
    validate_ranges(ranges)
    return ranges


def run(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tma2-generate", usage=USAGE, add_help=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--count", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ranges")
    ap.add_argument("--heldout-ranges")
    ap.add_argument("--noise-free", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--format", default="both")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code not in (0, None) else 0
    try:
        try:
            seed = parse_seed(args.seed)
        except ValueError as e:
            raise UsageError(str(e)) from e
        if not args.count.isdigit() or int(args.count) <= 0:
            raise UsageError("--count must be a positive integer")
        count = int(args.count)
        if args.format not in ("ndjson", "f32pack", "both"):
            raise UsageError("bad --format")
        try:
            ranges = load_ranges(args.ranges) if args.ranges else dict(DEFAULT_RANGES)
            heldout = (
                load_ranges(args.heldout_ranges) if args.heldout_ranges else dict(HELDOUT_RANGES)
            )
        except (RangesError, ValueError, OSError) as e:
            raise UsageError(str(e)) from e
        has_manoeuvre = (
            ranges.get("target_manoeuvre_fraction") is not None
            or ranges.get("target_course_change_count_weights") is not None
        )
        if has_manoeuvre and not args.heldout_ranges:
            raise UsageError("--ranges with a target manoeuvre needs --heldout-ranges")
        if args.noise_free:
            ranges = noise_free(ranges)
            heldout = noise_free(heldout)
        # Provenance is read once, before any output exists, from this package's checkout.
        commit, dirty = generator_provenance(read_git_provenance(), args.allow_dirty)
        created_by = "".join(
            [
                f"tma2-generate --seed {args.seed} --count {count}",
                " --noise-free" if args.noise_free else "",
                f" --ranges sha256:{file_digest(args.ranges)}" if args.ranges else "",
                (
                    f" --heldout-ranges sha256:{file_digest(args.heldout_ranges)}"
                    if args.heldout_ranges
                    else ""
                ),
            ]
        )
        summary = timed_generate(
            GenerateOptions(
                seed=seed,
                count=count,
                out_dir=Path(args.out),
                ranges=ranges,
                heldout_ranges=heldout,
                format=cast(Format, args.format),
                created_by=created_by,
                generator_git_commit=commit,
                generator_git_dirty=dirty,
            )
        )
        print(json.dumps(summary))
        return 0
    except (UsageError, ProvenanceError) as e:
        print(f"tma2-generate: {e}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
