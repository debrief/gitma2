#!/usr/bin/env bash
# Regenerate a plan's data split at its generating commit and check its committed digest.
#   scripts/ci/regen_split.sh <plan.json> <python expression for the data block> <out dir>
# e.g. scripts/ci/regen_split.sh configs/gate2/g2-a.json "p['stream']['data']" "$RUNNER_TEMP/stream"
# Prints the split's path on the last line. Run from the checkout root (needs full history).
set -euo pipefail
PLAN=$1 EXPR=$2 OUT=$3
read -r SEED COUNT RANGES HELDOUT GEN SPLIT DIGESTS <<< "$(python3 -c "
import json; p = json.load(open('$PLAN')); d = $EXPR
print(d['seed'], d['count'], d['ranges'], d['heldout'], d['commit'], d['split'], d['digests'])")"
WT="$(mktemp -d)/gen"
git worktree add -q "$WT" "$GEN"
(cd "$WT" && uv sync -q && uv run tma2-generate --seed "$SEED" --count "$COUNT" \
  --ranges "$RANGES" --heldout-ranges "$HELDOUT" --format f32pack --out "$OUT" >&2)
git worktree remove --force "$WT"
want=$(python3 -c "import json; print(json.load(open('$DIGESTS'))['$SPLIT.f32pack'])")
got=$(sha256sum "$OUT/$SPLIT.f32pack" | cut -d' ' -f1)
echo "$OUT/$SPLIT.f32pack: $got (committed $want)" >&2
[ "$got" = "$want" ]
echo "$OUT/$SPLIT.f32pack"
