#!/usr/bin/env bash
# Spec 038 (headroom.yml, score job): the decomposition's readings of this condition's scoring
# run, from the plan's "decomp" block (tma2-rdecomp's names, plus "split" and "segments": the
# run whose dumped segmentation classifies C″'s structure). Env: PLAN, TRUTH, SIDE, OUT, COND.
set -euo pipefail
python3 - "$PLAN" > "$RUNNER_TEMP/decomp-names.json" <<'PY'
import json, sys

d = json.load(open(sys.argv[1]))["decomp"]
json.dump({k: v for k, v in d.items() if k not in ("split", "segments")}, sys.stdout)
PY
SPLIT=$(python3 -c "import json; print(json.load(open('$PLAN'))['decomp'].get('split', ''))")
SEG=$(python3 -c "import json; print(json.load(open('$PLAN'))['decomp'].get('segments', ''))")
ARGS=(--errors "$OUT/errors.npz" --truth "$TRUTH" --names "$RUNNER_TEMP/decomp-names.json"
  --condition "$COND" --split "$SPLIT" --out "$OUT/decomp.json")
if [ "$COND" != "off" ]; then ARGS+=(--mismatch-truth "$SIDE"); fi
if [ -n "$SEG" ] && [ -f "$OUT/segmentations/$SEG.ndjson.gz" ]; then
  ARGS+=(--segments "$OUT/segmentations/$SEG.ndjson.gz")
fi
echo "tma2-rdecomp ${ARGS[*]}"
uv run tma2-rdecomp "${ARGS[@]}"
