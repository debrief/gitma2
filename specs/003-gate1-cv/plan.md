# Implementation Plan: Gate 1, a learned model on constant-velocity data

**Branch**: `claude/inspiring-curie-j192v9` (feature `003-gate1-cv`) | **Date**: 2026-11-01 |
**Spec**: [spec.md](spec.md)

## Summary

Train the first gitma2 model on constant-velocity data and gate it. A small causal transformer
reads the bearings and supplies per-bearing weights, a correction to the classical grid start and
a covariance scale to the declared physics layer, which computes the estimate. Training runs on
free GitHub runners with implicit differentiation through the solve (R1), sampled scored rows and
on-the-fly data (R4, R5). Gate 1 is scored on a fresh test seed against naive, batch least squares,
the re-tuned EKF and IMM and the oracle, decided by the agent panel after a pre-registered
decision record. The trained model exports with the iteration as an ONNX Loop (R2). The P0 entry
conditions are met first.

## Technical Context

**Language/Version**: Python 3.12 (uv)

**Primary Dependencies**: PyTorch 2.15 CPU (double), NumPy, numba, LinkML → Pydantic, onnx and
onnxruntime 1.31.1 (Python, web, Java), safetensors

**Storage**: files: validation and test splits (f32pack, committed digests), checkpoints and
results on branches, experiment records under `experiments/`

**Testing**: pytest (unit, golden, conformance), ruff, mypy --strict

**Target Platform**: GitHub-hosted ubuntu-latest, 4 cores, 16 GB

**Project Type**: research pipeline of CLIs

**Performance Goals**: one epoch over 10⁵ scenarios under an hour on 4 cores (measured 4 ms + 0.03 ms
per scored row for the solve; R4)

**Constraints**: double precision; no unrolled backward; standard operators only; deterministic
training per CPU family; jobs ≤ 6 h

**Scale/Scope**: three seeds × one carried configuration + three controls; test split 10⁴
scenarios (the 10% test split of a 10⁵ dataset, seed 303)

## Constitution Check

| Principle | Check | Status |
| --- | --- | --- |
| I Types | Model configuration, training plan, checkpoint metadata, model manifest and the Gate 1 decision record are LinkML classes (schema 0.18.0), generated and validated on read and write | pass |
| II Determinism | Training data from seeded streams (generator seed 310; re-noise keyed by seed, index, draw); deterministic per CPU family; manifests record seeds, versions, device, threads, digests; the verdict is reproduced by re-scoring the committed weights | pass |
| III Physics layer | The estimate is the physics layer's output; the direct head is control (a), never carried; trivial inputs and the oracle sit beside every result (on CV the oracle is the trivial-input layer) | pass |
| IV Measurement | Naive, batch LS, re-tuned EKF/IMM, oracle on the same rows; efficiency per slice; three seeds, carried by a rule named in advance (R8); shuffled-label control at naive level; time-late control at least as good as causal; normalisation by fixed constants only | pass |
| V Gates | P0 passed; Gate 1 pre-registered with its follow-on (SRD §5: one pre-registered iteration, then stop and publish); test seed 303 fresh | pass |
| VI Portable artefact | One ONNX graph with the iteration as a Loop, safetensors and a manifest, three-runtime conformance to 1e-5 (R2) | pass, contingent on R2 holding at full size |
| Constraints | Free CPU runners only; public repo, mock data | pass |
| Workflow | PR, CI, decision record before training, panel on the gate, site notes | pass |

**Post-design re-check**: unchanged. The implicit mode adds a Newton step whose Hessian uses
autograd (P backward passes); that is a training-time computation, not exported, and the
exported forward pass is the same iteration as the eager one.

## Project Structure

### Documentation (this feature)

```text
specs/003-gate1-cv/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md
├── contracts/   cli.md, plan-and-decision.md, model-artefact.md
└── checklists/requirements.md
```

### Source Code

```text
schema/tma.yaml                    0.18.0: PhysicsModelConfig, TrainingPlan, CheckpointMeta,
                                   PhysicsModelManifest, Gate1Decision
src/tma2/physics/layer.py          implicit mode; scriptable iteration body (Loop export); cov_ok
src/tma2/models/
  rows.py                          re-noised scenario tensors, sampled scored rows, grid start, CRB
  features.py                      per-timestep features (fixed scales)
  encoder.py                       causal transformer (fast path off)
  gate1.py                         heads + physics layer; direct-head control; time-late variant
  loss.py                          CRB-normalised squared errors, β-NLL, auxiliary init loss
  train.py                         epochs, checkpoints with optimiser and RNG state, resume
  predict.py                       per-timestep predictions on a split (gitma prediction format)
  export.py                        ONNX (Loop), safetensors, manifest, conformance golden batch
src/tma2/cli/
  train.py (tma2-train), predict.py (tma2-predict), tune.py (tma2-tune), g1.py (tma2-g1)
src/tma2/eval/g1.py                Gate 1 rows, ratios, gross-error difference, efficiency, verdict
configs/gate1/                     plan.json, model configs (carried + controls)
.github/workflows/train.yml        plan branches, chained jobs, checkpoints, results
experiments/<date>-g1-tune/        EKF/IMM tuning on validation
experiments/<date>-g1-decision/    the pre-registered decision record
experiments/<date>-g1/             the gate record and review
site/docs/algorithms/gate1-model.md; site/blog/<date>-gate-1.md
```

**Structure Decision**: models live in `src/tma2/models/` beside the physics layer they feed;
each stage is a CLI reading and writing files, as in specs 001–002.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Exact-Hessian implicit step | the Gauss–Newton implicit gradient was up to 25% off on flat rows | GN step is wrong exactly where the model has most to gain |
| TorchScript Loop in the export | 100 unrolled iterations do not load | unrolled export is infeasible; host-side loop breaks the one-graph rule |
