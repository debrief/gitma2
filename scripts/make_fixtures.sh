#!/usr/bin/env bash
# How the conformance fixtures under tests/fixtures/gitma/ were produced (spec 001, research R8).
# Requires a built checkout of debrief/Gitma at the commit named in each fixture's COMMIT file.
# Usage: scripts/make_fixtures.sh <path to gitma checkout>
set -euo pipefail
GITMA=${1:?path to the gitma checkout}
HERE=$(cd "$(dirname "$0")/.." && pwd)
COMMIT=$(git -C "$GITMA" rev-parse HEAD)
TMP=$(mktemp -d)
for f in phase4 iter4; do
  d="$HERE/tests/fixtures/gitma/$f-seed777"
  mkdir -p "$d"
  pnpm -C "$GITMA" -s tma-generate --seed 777 --count 100 --out "$TMP/$f" \
    --ranges "$GITMA/configs/$f-ranges.json" --heldout-ranges "$GITMA/configs/$f-heldout-ranges.json" \
    --format both >/dev/null
  cp "$TMP/$f"/*.f32pack "$TMP/$f/test.ndjson" "$d/"
  cp "$GITMA/configs/$f-ranges.json" "$d/ranges.json"
  cp "$GITMA/configs/$f-heldout-ranges.json" "$d/heldout-ranges.json"
  (cd "$TMP/$f" && python3 -c '
import hashlib, json, glob
files = sorted(glob.glob("*.ndjson") + glob.glob("*.f32pack"))
print(json.dumps({f: hashlib.sha256(open(f, "rb").read()).hexdigest() for f in files}, indent=2))
') > "$d/digests.json"
  printf 'gitma commit %s\ncommand: pnpm -s tma-generate --seed 777 --count 100 --out <dir> --ranges configs/%s-ranges.json --heldout-ranges configs/%s-heldout-ranges.json --format both\nkept: the four .f32pack splits, test.ndjson, digests.json (all eight generated files), ranges.json, heldout-ranges.json\n' "$COMMIT" "$f" "$f" > "$d/COMMIT"
done
# iteration-1 golden: gitma's own committed files; ranges materialised from the header.
d="$HERE/tests/fixtures/gitma/iter1-seed1"
mkdir -p "$d"
cp "$GITMA/packages/data/test/golden/seed1-count10-test.ndjson" "$d/test.ndjson"
cp "$GITMA/packages/data/test/golden/digests.json" "$d/digests.json"
python3 - "$d" <<'EOF'
import json, sys
d = sys.argv[1]
h = json.loads(open(f"{d}/test.ndjson").readline())
r = h["parameter_ranges"]
json.dump(r, open(f"{d}/ranges.json", "w"), indent=2)
hr = dict(r); hr["target_range0_m"] = {"min": 20000, "max": 30000}
json.dump(hr, open(f"{d}/heldout-ranges.json", "w"), indent=2)
EOF
printf 'gitma commit %s: packages/data/test/golden/{seed1-count10-test.ndjson,digests.json}\nproduced by the golden test with DEFAULT_RANGES / HELDOUT_RANGES (packages/sim/src/ranges.ts), count 10, created_by "tma-generate --seed 1 --count 10", provenance commit 0123456789abcdef0123456789abcdef01234567 dirty false\n' "$COMMIT" > "$d/COMMIT"
echo "fixtures written under tests/fixtures/gitma/ from gitma $COMMIT"
