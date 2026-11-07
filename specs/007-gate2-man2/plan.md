# Implementation Plan: Gate 2 on MAN2

**Branch**: `007-gate2-man2` (developed on `claude/inspiring-curie-j192v9`) | **Date**: 2026-11-06 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-gate2-man2/spec.md`

## Summary

Gate 2 asks whether a learned model, E, trained end to end through the physics layer, beats the
classical segmenter C on MAN2. C has the Gate S panel's fixes and is frozen by digest.

E has two learned parts. Both start at zero, so an untrained E is C exactly.

- **E-w (weights):** the Gate 1 encoder's heads give a per-bearing log-weight, added to C's
  hand-over mask, and a correction to the initial state. They run on C's segmentation, through
  the physics layer with knots, trained by implicit differentiation on the
  bound-normalised downstream error. This is the SRD's "fine-tuned end to end" model, and it acts
  directly on the open-at-k rows, where Gate S found C weakest.
- **E-s (segmentation, owner 2026-11-05, form b):** per-bearing evidence that shifts C's
  confirmation threshold. It is trained through confirmation's decisions by a relaxed acceptance
  over precomputed decision tables: the downstream error at the affected scored rows with and
  without each candidate. Form (a), a learned nominator, is built only if a cheap ceiling
  experiment (R1) shows that recall is a lever.

The gated model is E = E-w + E-s. E-w alone is a reported ablation, which attributes any gain.
G2-d, E − C, is the learning claim (owner 2026-11-06).

Everything long runs on CI: segmentation of the training stream, decision tables, training and
scoring.

## Technical Context

**Language/Version**: Python 3.12 (uv), as specs 001–006.

**Primary Dependencies**:
- PyTorch CPU, in double (the physics layer must; AGENTS.md);
- NumPy and numba (C, the cost tables);
- LinkML → Pydantic for every persisted type;
- onnxruntime for the export check.

**Storage**: files. Packs (f32pack), NDJSON segmentations and predictions, npz decision tables and
example tables, safetensors weights. Results branches on GitHub.

**Testing**:
- pytest: unit tests, the "untrained E = C" golden test, causal cut tests, and gradient finiteness;
- ruff and mypy --strict;
- CI for every PR.

**Target Platform**: free 4-core GitHub runners (ubuntu-latest). The session container is used
only for runs of a few minutes, because restarts kill longer jobs (AGENTS.md).

**Project Type**: research pipeline of CLIs (`tma2-*`) and workflows (`segment.yml`,
`segtrain.yml` pattern, `score.yml`).

**Performance Goals** (measured, R4):
- the physics layer with knots on 720-row windows takes 57 ms per prefix on 1 thread (29 ms on 4);
  with implicit differentiation the backward pass is under 1 ms;
- an epoch over 10,000 training scenarios, at about 4 sampled prefixes each, fits within a 345-min
  runner job;
- C's segmentation takes about 10 s per scenario, once, on CI shards.

**Constraints**:
- causal per prefix;
- seeded randomness only;
- C frozen by parameter and code digest;
- seeds 305 and 315 untouched;
- test seed 319 generated only after the decision record;
- the physics layer's knot cap raised from 8 to 12. R5 measured that 0.18% of validation G5
  prefixes need more than 8 knots, for the oracle and for C alike.

**Scale/Scope**:
- validation: 1,000 scoring scenarios (3,934 G5 rows) and 500 tuning scenarios;
- training: 10,000 σ = 1° scenarios from stream seed 318;
- test: all σ = 1° scenarios of seed 319's 10,000-scenario test split (about 5,000).

## Constitution Check

*Gate: must pass before Phase 0. Re-checked after Phase 1 (below).*

| Principle | How this plan meets it |
| --- | --- |
| I. Types once | New persisted types in `schema/tma.yaml`: Gate2Decision, EModelConfig, ETrainingPlan, DecisionTable header, Gate2Record and verdict. Generated, with `gen_types.py --check` in CI |
| II. Determinism | Seeded streams (318 training, 319 test); CI regenerates data at its commit and checks digests. Training is byte-reproducible per CPU family, and runs record the CPU model |
| III. Physics does the numerics | E's estimate is always the physics layer's. Its heads change only weights, initialisation and the confirmation threshold. Untrained E = C (tested) |
| IV. Honest measurement | Naive, one leg, IMM/EKF, GLR + confirm, C, E, E-w and the oracle on the same rows. Gross rates, finite-row medians, efficiency and strata. Three seeds plus a shuffled control. Paired clustered bootstrap at 97.5% |
| V. Gates | Decision record before training; validation rule; fresh test seed; panel verdict; follow-on stated in the write-up |
| VI. Portable artefact | E-w exports to ONNX: the encoder and heads plus the physics layer with knot inputs, in standard operators. C's segmentation is classical code and an input to the graph. E-s's evidence network exports as in spec 005 (MatMulNet). Three-runtime conformance as spec 005 |

No violations; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/007-gate2-man2/
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── cli.md           # tma2-g2train, tma2-g2predict, tma2-dtables, tma2-g2 (gate)
│   └── decision-record.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
src/tma2/
├── gate2/
│   ├── model.py         # E: encoder + heads (E-w) on C's hand-over inputs; E-s evidence
│   ├── inputs.py        # per-prefix physics inputs from C's segmentation (+ learned weights)
│   ├── tables.py        # decision tables: candidates, cost drops, errors with / without
│   ├── loss.py          # bound-normalised downstream loss, robust (clip / exclude absurd prefixes)
│   ├── train.py         # chained resumable training, robust early stopping, checkpoints
│   ├── predict.py       # E's per-row predictions (state, covariance) for scoring
│   └── gate.py          # G2-a…G2-d, shuffled rule, validation rule, refusals
├── cli/
│   ├── g2train.py       # tma2-g2train (tables | train)
│   ├── g2predict.py     # tma2-g2predict
│   ├── dtables.py       # tma2-dtables (E-s decision tables)
│   └── g2.py            # tma2-g2 (scoring + gate mode)
└── segment/             # C (unchanged after the decision record; code digest bound)
.github/workflows/
├── g2train.yml          # g2train/** → training jobs (chained, ≤ 345 min each)
└── (segment.yml, score.yml reused)
configs/gate2/           # training plans, score plans
experiments/<date>-g2-*/ # research, decision, validation, gate records
tests/unit/test_gate2_*.py
```

**Structure Decision**: a new `tma2.gate2` package beside `tma2.segment`, reusing:
- `models.gate1` (encoder, heads);
- `physics.layer` (knots);
- `segment.inputs` (hand-over);
- `segment.score` (references, strata, efficiency).

The scoring CLI follows `tma2-gs`, and E enters it as a prediction file.

## Phases

- **Phase 0 (research.md):** R1–R7 settled; R1's ceiling and R5's hand-over choice measured on CI.
- **Phase 1 (design):** data-model.md, contracts, quickstart.md.
- **Phase 2 (tasks.md):** `/speckit-tasks`.

## Constitution Check (post-design)

Re-checked against the design: unchanged, no violations. The design adds no new estimator outside
the physics layer, and every model output is a weight, an initialisation or a threshold shift.
