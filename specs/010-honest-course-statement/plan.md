# Implementation Plan: An honest course statement (Gate 5)

**Branch**: `010-honest-course-statement` (developed on `claude/happy-galileo-ksybjj`) |
**Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-honest-course-statement/spec.md`.

## Summary

E's points stay as they are. Each scored row states:
- **Course**, in the truncated form (research R2): an arc ±X, the probability P that the course
  lies inside it, and a concentration κ for the shape inside. The arc mass is P exactly, by
  construction.
- **What sets P**: a logistic function of causal features (R3). These are E's three log sds, a
  recent-bearing-residual proxy and C's open flag (R1), and the minute. A two-parameter Platt map,
  fitted on tuning rows, replaces the isotonic map.
- **Range and speed**: 95% half-widths, as in Gate 4.

Three statements are fitted in the same form:
- a learned head (adds E-w's encoder state);
- a classical rule (quadratics in the log sds, plus linear proxy terms), fitted on the stream;
- the sd^β temperature, per cell.

An encoder-only shuffled head is the learning control. Gate 5 (R7) is proposed as an SRD amendment,
followed by the decision record, training on CI, validation, and seed 320 only if the validation
rule is met.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: PyTorch 2.x, NumPy (existing; no SciPy: the von Mises mass on the arc is
computed numerically with `np.i0e`).

**Storage**: NDJSON prediction files; `.npz` feature caches (spec 008's), extended by a proxy cache
(R1 features per row, computed from the data split, E's state and C's segmentation); results
branches.

**Testing**: `pytest`, `ruff`, `mypy --strict`.

**Target Platform**: CI for training and scoring; the session for seconds-long steps (the proxy
cache for 1,971 + 3,934 + 39,054 rows is computed on CI for the stream).

**Project Type**: research library and CLIs.

**Performance Goals**: training minutes per seed; validation scoring with `--reuse` under 30 min.

**Constraints**:
- E's points are bit-identical.
- Every design setting is chosen on tuning ordinals 0–499 only, and trial runs are disclosed.
- References are frozen by name.
- The gate is scored from stored arrays.

**Scale/Scope**:
- validation scoring ordinals 500–1499 (3,934 rows);
- test seed 320 (about 5,000 scenarios), only if validation passes;
- three seeds, plus the encoder-only shuffle, the classical rule, the temperature and the
  reference temperatures.

## Constitution Check

- **I. Types once**: the new row fields (`course_kappa`, and the truncated form's `course_arc_prob`
  reused) and the configs and decision as LinkML classes; schema 0.31.0. Pass.
- **II. Determinism**: seeded; caches carry digests; the decision record comes before training;
  provenance is read first. Pass.
- **III. Physics does the numerics**: the estimate is E's; the learned part states uncertainty only.
  Pass.
- **IV. Honest measurement**:
  - the classical controls are registered first and use the same causal inputs except the encoder
    state;
  - the references get fitted statements;
  - every design setting comes from tuning rows;
  - the trial runs behind R1–R3 are disclosed (they were fits, not trainings of the head).

  Pass.
- **V. Fail fast through gates**: Gate 5 has a validation rule and a fresh seed; the synthetic check
  of the verdict logic runs before the amendment. Pass.
- **VI. Portable artefact**: export deferred, as in spec 009 (noted in tasks). Pass with a note.

## Project Structure

```
specs/010-honest-course-statement/   spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
src/tma2/calib/statement.py          + truncated course density, exact arc mass, its log score; Platt map
src/tma2/calib/proxy.py              R1 features per row (residual bias/χ² windows, C open flag) and the proxy score
src/tma2/calib/statement_fit.py      head, classical rule and temperature in the truncated form
src/tma2/cli/g5proxy.py              tma2-g5proxy: builds the proxy cache for a split (data, E file or cache, C segmentation)
src/tma2/cli/g3train.py              + subcommands statement5, classical5, temperature5
src/tma2/cli/g4predict.py            + the truncated form (kind by plan); writes course_kappa
src/tma2/eval/calibration.py         columns for κ, the proxy state; per-slice reliability; calibration slope; AUC
src/tma2/calib/gate5.py, cli/g5.py   Gate 5 criteria and verdicts
scripts/research/g5_tuning.py        R1–R4 evidence on tuning rows
configs/gate5/g5-a.json              the plan (bound by the decision record)
.github/workflows/g5train.yml, g5proxy.yml
```

## Phases

1. **Tuning evidence** (done in research; scripted as T002).
2. **Statement and measures**:
   - the truncated density and exact arc mass;
   - the proxy cache (validation 0–1499 in session, the stream on CI);
   - scorer columns and measures (per-slice reliability, slope, AUC, proxy state);
   - the synthetic check of the verdict logic.
3. **Baseline**: raw E, Gate 4's carried statement (st-s3, re-expressed as raw rows) and the
   references with their raw statements, on scoring rows (`--reuse`).
4. **Amendment and decision**: the SRD Gate 5 row; the plan and decision record, binding the
   controls, the proxy definition and threshold, and the Platt map's fitting rows.
5. **Training (CI)**: three head seeds, the encoder-only shuffle, the classical rule (stream), the
   temperature (tuning rows), the reference temperatures (tuning rows).
6. **Validation**: stated files, scoring, `tma2-g5 --split validation`, the panel.
7. **Test** (only if the validation rule is met): seed 320, its features, proxy and segmentation on
   CI, scoring, the panel.
8. **Reporting**: write-up, slides, AGENTS.md.

## Complexity Tracking

| Addition | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Proxy cache from bearings | C's segmentation alone has AUC 0.55 for unsettled rows (R1) | without it P cannot react to a fresh manoeuvre |
| Truncated density | the mixture with exact mass is mis-shaped and inconsistent once P is recalibrated (R2) | keeping the mixture repeats Gate 4's contradiction |
| Classical rule on the stream | Gate 4: 72% of the head's gain was a function of the sds | a weaker control would void the learning claim on review |
