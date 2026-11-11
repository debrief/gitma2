#!/usr/bin/env bash
# Spec 012 (rscore.yml): commit one scoring job's outputs to results/rscore-<name>-<kind>-<run id>.
set -euo pipefail
KIND="$1"
OUT="experiments/rscore-runs/$NAME-$GITHUB_RUN_ID/$KIND"
mkdir -p "$OUT/predictions"
cp -r "$RUNNER_TEMP/out/." "$OUT/"
for f in "$RUNNER_TEMP"/pred/*.ndjson; do gzip -c "$f" > "$OUT/predictions/$(basename "$f").gz"; done
cp "$PLAN" "$OUT/plan.json"
cp "$RUNNER_TEMP/data/digests.json" "$OUT/data-digests.json"
CPU=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ *//')
printf '{"run_id": "%s", "commit": "%s", "cpu_model": "%s", "kind": "%s"}\n' "$GITHUB_RUN_ID" "$GITHUB_SHA" "$CPU" "$KIND" > "$OUT/run.json"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
BR="results/rscore-$NAME-$KIND-$GITHUB_RUN_ID"
git checkout -b "$BR"
git add -f "$OUT"
git commit -qm "experiments: regressor scoring $NAME, $KIND (run $GITHUB_RUN_ID, $GITHUB_SHA)"
git push origin "$BR"
