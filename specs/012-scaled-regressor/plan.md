# Implementation Plan: The scaled end-to-end regressor control

**Branch**: `012-scaled-regressor` (developed on `claude/keen-wozniak-77td7j`) |
**Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-scaled-regressor/spec.md`.

## Summary

A causal transformer regresses the target's state at each prefix end directly from the
bearings and the ownship track (research R1, R2). It trains on scenarios drawn on the fly from
seed 326 by the existing generator, on a Modal T4 started from an Actions job that waits for it
(R4), inside a cap of 50 T4-hours split between a pilot, three seeds and two controls (R5). The
pilot measures throughput first: the data budget is what the hours buy, with 10⁷ scenarios as
the target, not a promise (R3). Predictions are written in the existing prediction format and
scored on CPU by the existing scorer beside batch least squares, C″, the IMM, the EKF, one leg,
the oracle and the bound; a small reading module turns the scores into the pre-registered
readings (R6). Everything up to the first GPU run is built and tested on CPU at toy size.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: PyTorch 2.x (float32, mixed precision on GPU), NumPy, numba (the
generator); new: the `modal` client, in an optional dependency group used only by the GPU
workflow.

**Storage**: checkpoints (`safetensors`) and run records on `results/gputrain-*` branches; a
Modal volume holds checkpoints between the segments of one run; prediction NDJSON; `errors.npz`.

**Testing**: `pytest` (causality by prefix truncation, frame invariance, the data stream's
determinism, a toy CPU training run that lowers its loss, resume equals an uninterrupted toy run
to tolerance on CPU), `ruff`, `mypy --strict`.

**Target Platform**: Modal (T4) for training; CI runners for prediction and scoring.

**Project Type**: research library and CLIs.

**Performance Goals**: at least 250 training scenarios a second on a T4 (the pilot's first
measurement; below 80 the model is reduced, R3); prediction of the 5,000-scenario test split in
minutes on 4 CPU cores.

**Constraints**: 50 T4-hours in total, enforced per run and by a ledger check; no GPU run before
the owner's account, spending limit and secrets exist; secrets only in this repository's
workflows on its own branches; the model is a control and is not exported.

**Scale/Scope**: about 6 million parameters; up to 10⁷ scenarios per seed; validation seed 327
(1,000 scenarios), test seed 328 (5,000 scenarios).

## Constitution Check

- **I. Types once (LinkML)**: `RegressorConfig`, `RegressorRunRecord`, `RegressorDecision` in
  `schema/tma.yaml`; predictions use the existing row types. Pass.
- **II. Determinism**: data from a seeded stream, model seeds recorded. GPU training is not
  bit-reproducible: recorded as a known limit (FR-011), mitigated by three seeds and the
  hardware and versions in every run record. Pass with the stated limit.
- **III. Physics does the numerics**: **deviation, justified.** The model has no physics layer.
  It is a control whose purpose is to test whether the layer is needed; it is never carried,
  exported or reported as the project's estimate (FR-032). See Complexity Tracking.
- **IV. Honest measurement**: every reference on the same rows; efficiency per slice; three
  seeds; readings and controls registered before any GPU run. Pass.
- **V. Fail fast through gates**: no gate; a decision record with readings and forecasts before
  the first GPU run, the test seed scored once per trained seed, the panel reviews. Pass.
- **VI. Portable artefact**: not applicable (a control is not exported).
- **Classification**: simulated data only. Pass.
- **Owner-only**: spending and secrets are the owner's; the cap is their decision of 2026-11-10.

## Project Structure

```
specs/012-scaled-regressor/     spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
schema/tma.yaml                 RegressorConfig, RegressorRunRecord, RegressorDecision
src/tma2/regress/frame.py       inputs and targets in the canonical frame; inverse map to rows
src/tma2/regress/data.py        the on-the-fly stream (seed, indices → padded tensors)
src/tma2/regress/model.py       patch front-end, causal transformer, output head
src/tma2/regress/train.py       loss, schedule, checkpoints, resume, time limit, run record
src/tma2/regress/predict.py     weights + split → prediction rows at the scored prefixes
src/tma2/regress/reading.py     held-course and manoeuvring readings from a scoring run
src/tma2/cli/rtrain.py, rpredict.py, rread.py      tma2-rtrain, tma2-rpredict, tma2-rread
scripts/modal_train.py          the Modal app: image, volume, one function with a hard timeout
.github/workflows/gputrain.yml  gputrain/** → ledger check, modal run, results branch
configs/regress/                toy.json (CPU), pilot.json, r-a.json (bound by the decision)
experiments/                    decision record, pilot, validation, test
```

## Phases

1. **CPU build**: frame, stream, model, training loop with resume and a time limit, prediction,
   reading; toy run and tests; `tma2-rpredict` output scored by the existing scorer on a small
   split.
2. **GPU plumbing**: the Modal app and `gputrain.yml`, exercised in a dry mode that needs no
   secrets (the app's function run locally on CPU with the toy plan).
3. **Decision record**: configuration, budget split, readings, controls, forecasts. Then wait
   for the owner's account and secrets if they are not yet there.
4. **Pilot** (at most 8 T4-hours): throughput, then learning curves for the planned model; one
   reduction allowed, recorded.
5. **Three seeds and two controls**; predictions and scoring on validation, then the test seed
   once per trained seed; readings; panel review; write-up and slides post.

## Complexity Tracking

| Deviation | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Principle III: an estimate with no physics layer | The experiment asks whether the layer is needed for precision; only a model without it can answer | A hybrid cannot test the question; the deviation is confined to a control that is never carried |
| A new external service (Modal) | No free GPU on GitHub's runners; the owner chose Modal's free credit | CPU runners cannot reach the data budget (gitma's 300 CPU-hours is the result being questioned) |
