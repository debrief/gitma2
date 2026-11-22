#!/usr/bin/env bash
# Spec 037 (headroom.yml, score job): the paired readings of the plan's regressors against its
# "read_controls" on this condition's scoring run. Env: PLAN, TRUTH, RUNNER_TEMP, OUT, COND.
set -euo pipefail
read -r REGS CTLS <<< "$(python3 -c "
import json
p = json.load(open('$PLAN'))
print(','.join(c['name'] for c in p['checkpoints']), ','.join(p['read_controls']))")"
STATED=""
for n in ${REGS//,/ }; do STATED="$STATED $n=$RUNNER_TEMP/pred/$n.ndjson"; done
# shellcheck disable=SC2086
uv run tma2-rmread --errors "$OUT/errors.npz" --truth "$TRUTH" --systems "$REGS" \
  --controls "$CTLS" --stated $STATED --condition "$COND" --out "$OUT/reading.json"
