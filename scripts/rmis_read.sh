#!/usr/bin/env bash
# Spec 037 (headroom.yml, score job): the paired readings of the plan's regressors against its
# "read_controls" on this condition's scoring run, and any further readings in "read_extra"
# ([{systems, controls, out}], e.g. the hybrid's). Env: PLAN, TRUTH, RUNNER_TEMP, OUT, COND.
set -euo pipefail
python3 - "$PLAN" "$OUT" "$RUNNER_TEMP" "$TRUTH" "$COND" > "$RUNNER_TEMP/readcmds" <<'PY'
import json, os, shlex, sys

plan, out, tmp, truth, cond = sys.argv[1:]
p = json.load(open(plan))
regs = [c["name"] for c in p["checkpoints"]]
base = ["--errors", f"{out}/errors.npz", "--truth", truth, "--condition", cond]
a = base + ["--systems", ",".join(regs), "--controls", ",".join(p["read_controls"]),
            "--stated", *[f"{n}={tmp}/pred/{n}.ndjson" for n in regs], "--out", f"{out}/reading.json"]
if p.get("interval_fit"):
    a += ["--temperature", p["interval_fit"]]
print(shlex.join(a))
have = set(json.load(open(f"{out}/headroom.json")).get("predictions", {})) | {"imm", "ekf", "one_leg", "oracle"}
for x in p.get("read_extra", []):
    systems = [s for s in x["systems"] if s in have]
    controls = [s for s in x["controls"] if s in have]
    if systems and controls:
        print(shlex.join(base + ["--systems", ",".join(systems), "--controls", ",".join(controls), "--out", f"{out}/{x['out']}"]))
PY
while read -r ARGS; do
  echo "tma2-rmread $ARGS"
  eval uv run tma2-rmread $ARGS
done < "$RUNNER_TEMP/readcmds"
