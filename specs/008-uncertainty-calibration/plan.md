# Implementation Plan: Uncertainty calibration of the Gate 2 estimator (Gate 3)

**Branch**: `008-uncertainty-calibration` (developed on `claude/happy-galileo-ksybjj`) |
**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-uncertainty-calibration/spec.md`

## Summary

The carried Gate 2 estimator E (e-s3) learns to state its uncertainty honestly. The plan has five
steps:

1. **Report covariances.** Every physics-layer prediction row, and the IMM and EKF rows, carries
   the 4 × 4 state covariance and the derived log-range, course and speed standard deviations
   (research R1–R3). The schema is extended additively.
2. **Measure.** The scorer measures calibration on validation for every estimator on the same
   rows: coverage at 68% and 95%, NEES, the 95% interval score and sharpness, per slice (R4).
   This is the baseline for the decision record.
3. **Calibrate.** A scalar log-scale head on E-w's frozen encoder state corrects the covariance
   only (R5), trained by β-NLL (R6) on cached features (R7). Three seeds, a shuffled control, and
   a classical per-slice temperature as the learning bar (R8).
4. **Gate.** Gate 3 is proposed as an SRD amendment (R11), then a decision record is committed,
   validation rules applied, fresh seed 320 scored, and the panel decides.
5. **Follow-ons.** The time-late variant and the Gate 2 panel's process follow-ons (R9, R10).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: PyTorch 2.x, NumPy, numba, LinkML → Pydantic (existing stack; nothing
new)

**Storage**: files. NDJSON prediction files, `.npz` feature caches and error stores, and results
branches on GitHub.

**Testing**: `pytest` (unit and golden), `ruff`, `mypy --strict`, three-runtime ONNX conformance
for the head's export.

**Target Platform**: free 4-core GitHub runners (CI) for anything over a few minutes; the session
container for short checks.

**Project Type**: research library and CLIs (`src/tma2`, `tma2-*` commands).

**Performance Goals**:
- feature caching over the stream (9,930 scenarios) in under about 2 h on 16 shards;
- head training in minutes per epoch from the cache;
- scoring validation in under 1 h.

**Constraints**:
- E's point estimates bit-identical with and without calibration;
- Gate 2's references frozen by name;
- gitma-ported reference numerics byte-identical (the f32 point rows);
- the scorer's re-solves are CPU-family dependent (Gate 2), so errors are stored.

**Scale/Scope**:
- validation scoring ordinals 500–1499 (3,934 G5 rows);
- test seed 320, all σ = 1° scenarios (about 5,000; about 19,600 rows);
- 3 head seeds + shuffled + temperature control + one time-late E-w.

## Constitution Check

*Gate: must pass before Phase 0. Re-checked after Phase 1 (below).*

| Principle | How this plan meets it |
| --- | --- |
| I. Types once | New `PredictionRow` fields (covariance, standard deviations, `cov_ok`), `CalibrationHeadConfig`, `Gate3Decision`, `Gate3Record` and the calibration metrics record in `schema/tma.yaml`; generated, with `gen_types.py --check` in CI |
| II. Determinism | Seeds 314/318/320; data regenerated at its commit and digest-checked; feature caches and head training seeded; CPU model recorded; re-solved errors stored for reuse (R10) |
| III. Physics does the numerics | The estimate stays the physics layer's. The head changes only the covariance's scale and never the state (tested bit for bit) |
| IV. Honest measurement | All estimators on the same rows; missing estimates count as not covered; gross and non-gross reported separately; sharpness beside coverage; three seeds, a shuffled control (best and last epoch), a classical control; the time-late variant (R9) |
| V. Gates | SRD amendment and decision record before calibration training; validation rule; fresh seed 320; panel verdict; follow-on in the write-up |
| VI. Portable artefact | The head is a small MLP on E-w's encoder state; it exports with E-w's graph as a fifth output (calibrated covariance), with three-runtime conformance |

No violations; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/008-uncertainty-calibration/
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── cli.md           # changed and new CLIs
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
schema/tma.yaml                    # PredictionRow covariance fields; Gate 3 types
src/tma2/
  eval/calibration.py              # NEW: coverage, NEES, interval score, sharpness, slices (R4)
  physics/uncertainty.py           # NEW: covariance → log-range/course/speed sds (R2)
  references/imm.py, ekf.py        # covariance out-arrays (R3), points unchanged
  segment/score.py                 # rows carry covariance; calibration arrays in errors.npz; reuse (R10)
  gate2/predict.py                 # rows carry covariance; --features cache (R7)
  calib/                           # NEW package
    head.py                        # scalar log-scale head (R5)
    loss.py                        # β-NLL (R6)
    train.py                       # training from the feature cache, three seeds, shuffled, last epoch
    temperature.py                 # per-slice classical control (R8)
    predict.py                     # calibrated prediction files (state copied, covariance scaled)
    gate.py                        # G3-a…G3-d
  gate2/export.py                  # E-w graph gains the calibrated covariance output
  cli/
    g2predict.py                   # --features
    g3.py                          # NEW: tma2-g3 (calibration scoring, gate mode)
    g3train.py                     # NEW: tma2-g3train {head,temperature}
.github/workflows/
  g2features.yml                   # NEW: feature caches on CI
  g3train.yml                      # NEW
  score.yml                        # kind "g3"
tests/unit/
  test_uncertainty.py, test_calibration_metrics.py, test_calib_head.py,
  test_calib_identity.py (untrained = raw; state unchanged), test_score_reuse.py,
  test_gate3.py, test_followons.py (coverage assertion, merge counts, shuffled source)
```

**Structure Decision**: one project, extending `src/tma2`. The calibration code is a new package,
`calib/`, beside `gate2/`, because it is trained and gated separately from E.

## Phases and order

1. **US1 (covariances in rows):** R1–R3; existing files stay valid. Then re-make the Gate 2
   validation prediction files with covariances (CI), and check point identity.
2. **US2 (baseline):** the calibration scorer (R4) and the validation calibration record for C,
   E, E-w, C″, IMM, EKF and the oracle. This sets the forecast and informs the proposed bands.
3. **Amendment and decision:** open the SRD amendment PR (Gate 3 row; owner merges). Commit the
   decision record (`experiments/<date>-g3-decision/`) once the amendment is merged, or after
   two working days without objection (AGENTS.md).
4. **US3 (calibration):** feature caches (CI), head training (three seeds + shuffled),
   temperature fit, validation scoring, carried-seed and shuffled rules, `carried.json`.
5. **US4 (gate):** seed 320; C segmentation, E predictions with features, calibrated
   predictions, scoring with `--reuse` where possible, panel, write-up.
6. **US5 (follow-ons):** R9 (time-late, CI training in parallel with step 4) and R10 (process,
   before step 5's gate scoring).

## Constitution Check (post-design)

Re-checked against the design: unchanged, no violations. The only new learned output is a scalar
on the covariance. The estimate remains the physics layer's.

## Complexity Tracking

None.
