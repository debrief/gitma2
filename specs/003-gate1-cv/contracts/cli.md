# CLI contracts (spec 003)

All commands read and write files; exit 2 on bad input, 3 when a gate is not passed.

```
tma2-tune --validation <split.f32pack> --out experiments/<id> [--filters imm,ekf]
    EKF/IMM grids of research R6 on validation; writes grid.csv, choice.json (frozen settings),
    and the manifest. Deterministic.

tma2-train --plan configs/gate1/plan.json --model <id> --checkpoint <dir> [--max-wall-s N]
           [--epochs N] [--scenarios N]
    Trains or resumes one model; checkpoints after every epoch (weights, optimiser and RNG state,
    CheckpointMeta); stops at the wall-clock cap after the epoch in progress, or when complete.
    Refuses a plan whose validation digest does not match, and a checkpoint from another plan.

tma2-predict --model <checkpoint dir or artefact> --truth <split.f32pack> --out <pred.ndjson>
    Per-timestep predictions (gitma's prediction format, estimator = model id) at every post-zig
    row; refuses a model whose plan names other data.

tma2-g1 --decision experiments/<id>/decision.json --plan configs/gate1/plan.json
        --models <dir with carried and control predictions> --test <split.f32pack>
        --validation <split.f32pack> --experiment experiments/<id>
    Checks the decision record's commit is an ancestor of the models' training commit, the test
    seed is the record's and unused elsewhere; scores model, naive, batch LS, EKF, IMM and oracle
    on the same rows; writes the experiment record and the machine verdict.

python -m tma2.models.export --model <checkpoint> --out <dir>
    ONNX (Loop), safetensors, manifest, golden batch; the Python leg; the browser and Java legs
    are the conformance harness of spec 002.
```
