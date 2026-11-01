#!/usr/bin/env bash
# gitma's own seed-301 dataset and frozen-IMM predictions for P0's at-scale IMM check
# (`tma2-p0 --gitma-data <out> --gitma-imm <out>/validation-imm.ndjson`; P0 panel round 2).
# Requires a checkout of debrief/Gitma at the commit P0 names (d0aec60) with pnpm and Node 22.
# Usage: scripts/gitma_reference.sh <gitma checkout> <out dir>
set -euo pipefail
GITMA=$(cd "${1:?path to the gitma checkout}" && pwd)
OUT=$(mkdir -p "${2:?output directory}" && cd "$2" && pwd)
WANT=d0aec60a05b8664a586af87bf58232d0d1767c4a
HAVE=$(git -C "$GITMA" rev-parse HEAD)
[ "$HAVE" = "$WANT" ] || { echo "gitma checkout is at $HAVE, P0 needs $WANT" >&2; exit 2; }
(cd "$GITMA" && pnpm install --frozen-lockfile >/dev/null && pnpm build >/dev/null)
# gitma's generator refuses a dirty tree; the build writes only ignored files.
(cd "$GITMA" && pnpm -s tma-generate --seed 301 --count 100000 --out "$OUT" \
  --ranges configs/phase4-ranges.json --heldout-ranges configs/phase4-heldout-ranges.json \
  --format f32pack)
(cd "$GITMA" && pnpm -s tma-track --in "$OUT/validation.f32pack" --out "$OUT/validation-imm.ndjson" \
  --filter imm --sigma-cv 0.01 --sigma-ct 0.03 --sigma-omega 0.01 --switch 0.001 \
  --p0-scale 4 --r-scale 8)
printf 'gitma commit %s\ntma-generate --seed 301 --count 100000 --ranges configs/phase4-ranges.json --heldout-ranges configs/phase4-heldout-ranges.json --format f32pack\ntma-track --filter imm --sigma-cv 0.01 --sigma-ct 0.03 --sigma-omega 0.01 --switch 0.001 --p0-scale 4 --r-scale 8\n' "$WANT" > "$OUT/COMMANDS"
