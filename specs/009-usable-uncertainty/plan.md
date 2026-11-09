# Implementation Plan: Usable uncertainty for the carried estimator (Gate 4)

**Branch**: `009-usable-uncertainty` (developed on `claude/happy-galileo-ksybjj`) |
**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-usable-uncertainty/spec.md` (re-scoped by the owner
to a probabilistic course statement).

## Summary

E's points stay as they are. Each scored row gains a usable statement:
- **course**: "within ±X° with probability P, otherwise unknown", from a mixture of a von Mises
  centred on E's course (spread scaled from its stated sd) and a uniform (research R2);
- **range and speed**: 95% intervals scaled from the stated sds, trained on the interval score of
  the exact errors (R3, R4).

A learned head (R6) and a classical per-slice temperature in the same form produce the statement; a
shared isotonic map recalibrates P. Gate 4 (R7) is proposed as an SRD amendment, then a decision
record, training, validation, and seed 320 only if the validation rule is met.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: PyTorch 2.x, NumPy (existing stack; nothing new: no SciPy)

**Storage**: files: NDJSON prediction files, `.npz` feature caches (spec 008's, reused), results
branches.

**Testing**: `pytest`, `ruff`, `mypy --strict`.

**Target Platform**: CI runners for training and scoring; the session for seconds-long steps.

**Project Type**: research library and CLIs.

**Performance Goals**: training minutes per seed from the cache; validation scoring with `--reuse`
under 30 min on CI.

**Constraints**: E's points bit-identical; every design setting chosen on tuning ordinals 0–499;
references frozen by name; scoring from stored arrays.

**Scale/Scope**: validation scoring ordinals 500–1499 (3,934 rows); test seed 320 (about 5,000
scenarios) only if validation passes; 3 seeds + shuffled + temperature.

## Constitution Check

- **I. Types once (LinkML)**: the course statement and interval fields are added to the schema
  (`PredictionRow`: `course_arc_rad`, `course_arc_prob`, `range_ratio_q95`, `speed_q95_mps`); the
  configs and the gate's decision as new classes. Pass.
- **II. Determinism**: seeded training, cached features, plan digests, decision record before
  training; provenance read before writing (spec 008 minors). Pass.
- **III. Physics does the numerics**: the estimate is the physics layer's (E); the learned part only
  states uncertainty. Pass.
- **IV. Honest measurement**: references on the same rows; classical control in the same form;
  shuffled control at best and last epoch; three seeds; settings from tuning rows only; the
  scoping result that motivated the re-scope is recorded (R1). Pass.
- **V. Fail fast through gates**: pre-registered Gate 4 with a validation rule and a fresh seed.
  Pass.
- **VI. Portable artefact**: the head's statement exports with E-w's graph as spec 008's did
  (deferred unless carried; noted in tasks). Pass with a note.

## Project Structure

```
specs/009-usable-uncertainty/   spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
src/tma2/calib/statement.py     course mixture, arc and probability; interval scale; isotonic map
src/tma2/calib/data.py          exact errors from the cache (wrapped course, log range ratio, speed)
src/tma2/calib/{head,loss,train,temperature,predict}.py   extended for the statement form
src/tma2/eval/calibration.py    reliability (overall and binned), circular log score, coverage
src/tma2/calib/gate.py          Gate 4 criteria; cli/g4.py
schema/tma.yaml                 the row fields and configs above
configs/gate4/g4-a.json         the plan (bound by the decision record)
```

## Phases

1. **Measure** (no training, no calibrated estimator on scoring rows): add the statement fields
   and the measures; the baseline is E raw and the references on scoring ordinals 500–1499, with
   E's raw statement (P from its own Gaussian course sd, arc capped at Xmax; intervals at 1.96 sd).
   Every design setting is chosen from tuning ordinals 0–499 only (research R2, R3).
2. **Amendment and decision**: Gate 4 row (owner merges), decision record binding the plan.
3. **Train and validate**: three seeds, shuffled, temperature; validation scoring with `--reuse`;
   `tma2-g4 --split validation`; panel if the rule is not met.
4. **Test** (only if validation passes): seed 320, predictions with features, calibrated files,
   scoring, panel.
5. **Report**: slides post (reliability diagram, coverage charts, track plots with course arcs).

## Complexity Tracking

None beyond spec 008's pipeline; the statement replaces the covariance scale.
