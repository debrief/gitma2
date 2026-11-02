# CLI contracts (spec 004)

```
tma2-train --plan configs/gate-d/plan.json --model <id> --checkpoint <dir> [--max-wall-s N]
    As spec 003; a detector configuration in the plan trains the detector. Checkpoint metadata
    carries weights_digest and each job record git_dirty. Early stopping counts an epoch as an
    improvement only if the validation loss falls by at least min_improvement (relative). After
    every epoch the liveness figures (alive share, output sd per head) go to the log and the
    metadata.

tma2-detect --plan <plan> --model <id> --checkpoint <dir> --truth <split.f32pack> --out <rows.ndjson>
    Per-timestep detector outputs (p_change; exported knots with weights and kinds as of each row)
    at every row; header names the detector id and the weights digest; refuses a missing
    best.safetensors.

tma2-controls tune --kind cusum|glr|imm_mode --validation <split> --target-far <f> --out <settings.json>
tma2-controls run  --settings <settings.json> --truth <split> --out <rows.ndjson>
    The CUSUM, linearised GLR and IMM mode-probability detectors (research R6), tuned to a held-leg
    false-alarm fraction on validation, and run per timestep in the detector-output format.

tma2-tune ... --criterion g5
    As spec 003, scored on the median range error over all σ = 1° G5 rows.

tma2-gd --decision <decision.json> --plan <plan.json> --carried <id>... --model-meta <meta.json>...
        --test <split.f32pack> --detector <rows.ndjson>... --controls <rows.ndjson>...
        --least-squares <pred> --imm <pred> --ekf <pred> --naive <pred> --oracle <pred>
        --experiment experiments/<id>
    Refuses a decision record, plan, carried model, weights digest, test seed or count, prediction
    binding or ancestry that does not match. Computes Annex A §A.3's metrics and Gate D's checks
    with scenario-clustered paired bootstraps at 97.5%; writes the experiment record (manifest with
    weights and amendment digests), detection records and the machine verdict. Exit 3: not passed.

python -m tma2.models.detector_export --out <dir> [--plan p --model id --checkpoint c]
    The detector alone as ONNX (360-row window, dynamic batch), safetensors, manifest, golden batch,
    Python leg; the browser and Java legs as spec 003, with a one-second limit per window in WASM.
```
