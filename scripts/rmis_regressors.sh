#!/usr/bin/env bash
# Spec 037 (headroom.yml, score job): for a plan with "checkpoints", fetch each regressor from
# its results branch, check its digest, and write its prediction rows with stated intervals on
# $TRUTH into $RUNNER_TEMP/pred/<name>.ndjson. Env: PLAN, TRUTH, RUNNER_TEMP, N (ordinals),
# START. Everything is written outside the checkout.
set -euo pipefail
W="$RUNNER_TEMP"
PRED="${PRED_DIR:-$W/pred}"
mkdir -p "$W/ck" "$PRED"
SCALE=$(python3 -c "import json; print(json.load(open('$PLAN')).get('interval_scale') or '1,1,1')")  # 'r,c,s' or an interval-fit.json
while read -r NAME BRANCH DIR SHA; do
  git fetch -q origin "$BRANCH"
  git show "FETCH_HEAD:$DIR/checkpoint.safetensors" > "$W/ck/$NAME.safetensors"
  GOT=$(sha256sum "$W/ck/$NAME.safetensors" | cut -d' ' -f1)
  echo "$NAME $GOT"
  if [ "$SHA" != "-" ] && [ "$GOT" != "$SHA" ]; then echo "checkpoint digest: plan says $SHA"; exit 1; fi
  git show "FETCH_HEAD:$DIR/plan.json" | python3 -c "import json, sys; json.dump(json.load(sys.stdin)['config'], open('$W/ck/$NAME.json', 'w'))"
  uv run tma2-rpredict --weights "$W/ck/$NAME.safetensors" --config "$W/ck/$NAME.json" \
    --in "$TRUTH" --out "$PRED/$NAME.ndjson" --name "$NAME" --start "$START" --count "$N" \
    --intervals "$SCALE"
done < <(python3 -c "
import json
for c in json.load(open('$PLAN')).get('checkpoints', []):
    print(c['name'], c['branch'], c['dir'], c.get('sha256', '-'))")
