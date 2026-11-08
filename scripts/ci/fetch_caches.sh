#!/usr/bin/env bash
# Fetch a Gate 3 plan's feature caches from their g2predict results branches (spec 008).
#   scripts/ci/fetch_caches.sh <plan.json> <out dir>
# Writes <out>/train/*.npz and <out>/val/*.npz. Run from the checkout root (needs full history).
set -euo pipefail
PLAN=$1 OUT=$2
for split in train val; do
  read -r B D <<< "$(python3 -c "import json; c = json.load(open('$PLAN'))['caches']['$split']; print(c['branch'], c['dir'])")"
  git fetch -q origin "$B"
  mkdir -p "$OUT/$split"
  for f in $(git ls-tree --name-only FETCH_HEAD "$D/" | grep '\.npz$'); do
    git show "FETCH_HEAD:$f" > "$OUT/$split/$(basename "$f")"
  done
  n=$(ls "$OUT/$split"/*.npz | wc -l)
  echo "$split: $n caches from $B"
  test "$n" -gt 0
done
