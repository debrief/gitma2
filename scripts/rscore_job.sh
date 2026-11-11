#!/usr/bin/env bash
# Spec 012 scoring job (rscore.yml): fetch each regressor checkpoint from its results branch,
# write its prediction rows on $TRUTH, score with the existing scorer and compute the readings.
# Usage: rscore_job.sh man2|held   (env: PLAN, TRUTH, RUNNER_TEMP; man2 expects classical shard
# files under $RUNNER_TEMP/shards). Everything is written outside the checkout.
set -euo pipefail
KIND="$1"
W="$RUNNER_TEMP"
mkdir -p "$W/ck" "$W/pred" "$W/out"
if [ "$KIND" = man2 ]; then KEY=ordinals; else KEY=held_ordinals; fi
N=$(python3 -c "import json; print(json.load(open('$PLAN'))['$KEY'])")
REGS=""
while read -r NAME BRANCH DIR; do
  git fetch -q origin "$BRANCH"
  git show "FETCH_HEAD:$DIR/checkpoint.safetensors" > "$W/ck/$NAME.safetensors"
  git show "FETCH_HEAD:$DIR/plan.json" | python3 -c "import json, sys; json.dump(json.load(sys.stdin)['config'], open('$W/ck/$NAME.json', 'w'))"
  uv run tma2-rpredict --weights "$W/ck/$NAME.safetensors" --config "$W/ck/$NAME.json" \
    --in "$TRUTH" --out "$W/pred/$NAME.ndjson" --name "$NAME" --count "$N"
  REGS="${REGS:+$REGS,}$NAME"
done < <(python3 -c "
import json
for c in json.load(open('$PLAN'))['checkpoints']:
    print(c['name'], c['branch'], c['dir'])")
REFS=""
if [ "$KIND" = man2 ]; then
  for NAME in $(python3 -c "import json; print(' '.join(c['name'] for c in json.load(open('$PLAN'))['classical']))"); do
    uv run python -m tma2.cli.hmerge --out "$W/pred/$NAME.ndjson" "$W"/shards/"$NAME".[0-9]*.ndjson
  done
  REFS=$(python3 -c "import json; p = json.load(open('$PLAN')); print(','.join([c['name'] for c in p['classical']] + ['imm']))")
fi
read -r IMM EKF <<< "$(python3 -c "import json; p = json.load(open('$PLAN')); print(p['imm'], p['ekf'])")"
set +e
uv run tma2-gh --truth "$TRUTH" --out "$W/out" --start 0 --count "$N" --split tuning \
  --imm "$IMM" --ekf "$EKF" --predictions "$W"/pred/*.ndjson
rc=$?
set -e
echo "tma2-gh exit $rc"
[ "$rc" = 0 ] || [ "$rc" = 3 ]
uv run tma2-rread --truth "$TRUTH" --errors "$W/out/errors.npz" --regressors "$REGS" \
  --check oracle --references "$REFS" --out "$W/out/reading.json"
sha256sum "$TRUTH" > "$W/out/truth.sha256"
