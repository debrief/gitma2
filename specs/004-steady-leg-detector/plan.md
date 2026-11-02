# Implementation Plan: Steady-leg detector and Gate D

**Branch**: `claude/inspiring-curie-j192v9` (feature `004-steady-leg-detector`) | **Date**: 2026-11-02 |
**Spec**: [spec.md](spec.md)

## Summary

Train a learned steady-leg detector on manoeuvring data and gate it (SRD Annex A). The detector
shares the Gate 1 encoder; its heads give a "now" probability, soft changepoint weights over
earlier rows and the kind of each change, which feed the declared physics layer as its knots and
speed prior (R2–R4). It is trained on classification losses plus the downstream error of the
piecewise solve, through the physics layer by implicit differentiation (R5), on free runners with
spec 003's workflows. Gate D compares it with CUSUM, a linearised GLR and the IMM's mode
probability at matched false-alarm rates, and its downstream estimate with the re-tuned IMM, batch
least squares and the oracle (R6–R8). First, the Gate 1 panel's follow-ups: heads that cannot die
with a liveness check, a minimum improvement in early stopping, weights and amendments bound by
digest, one median convention and one convergence definition (R1, R11).

## Technical Context

**Language/Version**: Python 3.12 (uv)

**Primary Dependencies**: PyTorch 2.15 CPU (double), NumPy, numba, LinkML → Pydantic, onnx and
onnxruntime 1.31.1 (Python, web, Java), safetensors

**Storage**: validation and test splits as f32pack files with pinned digests; checkpoints and
results on branches; experiment records under `experiments/`

**Testing**: pytest (unit, golden, conformance), ruff, mypy --strict

**Target Platform**: GitHub-hosted ubuntu-latest, 4 cores, 16 GB

**Project Type**: research pipeline of CLIs

**Performance Goals**: one epoch over 10⁵ manoeuvring scenarios under an hour on a 4-core runner
(budget 36 ms per scenario; R5); detector export under one second per 360-row window in WASM

**Constraints**: double precision for the physics layer; implicit backward; standard operators;
deterministic per CPU family; jobs ≤ 6 h; no paid compute

**Scale/Scope**: two variants × three seeds + a classification-only control; validation and test
splits 10⁴ scenarios each (the 10% splits of seeds 304 and 305)

## Constitution Check

| Principle | Check | Status |
| --- | --- | --- |
| I Types | New LinkML classes (detector configuration, Gate D decision, detection records, control settings) and fields (`head_activation`, `min_improvement`, `weights_digest`, `git_dirty`, manifest amendments), generated and validated | pass |
| II Determinism | Seeded training stream 311 with keyed noise draws; validation 304 and test 305 as files with pinned digests; weights bound by digest; verdicts reproduced by re-scoring | pass |
| III Physics layer | The detector supplies segmentation and kinds; the estimate scored at Gate D is the physics layer's with trivial weights; the classification-only detector is a declared control; trivial inputs and the oracle sit beside every result | pass |
| IV Measurement | Naive, batch LS, re-tuned EKF/IMM and the oracle on the same rows; efficiency per slice; three seeds per carried variant with a named carried rule (R10); controls at matched operating points (R6); the shuffled-label check is not used for the detector (no physics-layer-blind check); time-late variant carried; every registered check reviewed against the architecture (FR-035) | pass |
| V Gates | P0 and Gate 1 passed; Gate D pre-registered with Annex A §A.6's follow-on; fresh seeds 304/305/311 | pass |
| VI Portable artefact | The detector exports alone with three-runtime conformance and a WASM speed limit (R12) | pass |
| Constraints | Free runners; public repo; mock data | pass |
| Workflow | PR, CI, decision record before training, panel on the gate, site pages | pass |

**Post-design re-check**: unchanged. The pairwise heads export as matrix products; the
liveness check is a training-time diagnostic, not part of the exported graph.

## Project Structure

### Documentation (this feature)

```text
specs/004-steady-leg-detector/
├── spec.md
├── plan.md              # this file
├── research.md          # R1–R12
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── decision-record.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
schema/tma.yaml                    0.20.0: detector config, Gate D decision, records, new fields
src/tma2/models/
  heads.py                         head MLPs (relu | tanh), liveness diagnostics
  gate1.py                         uses heads.py (relu kept for Gate 1's weights)
  detector.py                      encoder (13 channels) + p_change, w_change, p_kind heads
  detector_labels.py               now / boundary / kind targets, held and settled flags
  detector_loss.py                 classification losses + downstream physics loss
  train.py                         detector models in plans; min_improvement; git_dirty; weights digest
  predict.py                       weights digest in headers; no fallback to non-best weights
  detector_export.py               ONNX export of the detector alone
src/tma2/detect/
  controls.py                      CUSUM, linearised GLR, IMM mode probability (numba)
  matching.py                      alarms, detection, delays, misses, held-leg false alarms, F1, ECE
  downstream.py                    exported knots and kinds → physics layer estimates at G5 rows
src/tma2/references/imm.py         μ_CT per row exposed
src/tma2/eval/gd.py                Gate D checks and intervals
src/tma2/cli/
  detect.py                        tma2-detect: per-timestep detector outputs and alarms
  controls.py                      tma2-controls: CUSUM / GLR / IMM-mode alarms, tuning
  gd.py                            tma2-gd: the gate
  tune.py                          --criterion g5
.github/workflows/                 gd-validation.yml, gd-gate.yml (spec 003's pattern)
tests/unit/                        heads liveness, labels, losses, controls, matching, gd checks, export
site/docs/algorithms/detector.md   algorithm note; glossary; blog write-up
```

**Structure Decision**: the existing single-package layout; detector-specific evaluation lives in
a new `tma2.detect` package so the gate code (`eval/gd.py`) stays parallel to `eval/g1.py`.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Pairwise heads [B, R, R] | Changepoint evidence arrives after the changepoint (R2) | A per-row score from a causal encoder cannot use the bearings after j |
| Linearised GLR | Annex A requires a one-versus-two-leg control | A literal refit costs about 33 h per split (R6) |
| Head activation as a config field | New heads must not die; Gate 1's weights must still re-score | Changing the activation for all models would break re-scoring Gate 1 |
