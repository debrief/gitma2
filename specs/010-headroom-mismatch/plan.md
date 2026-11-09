# Implementation Plan: Headroom under bearing-error mismatch (Gate H)

**Branch**: `010-headroom-mismatch` (developed on `claude/keen-wozniak-77td7j`) |
**Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-headroom-mismatch/spec.md`.

## Summary

Nothing is trained. The generator gains a bearing-error overlay (version 0.7.0): correlated error,
slow bias, an untold σ and outliers, each switchable, with mismatch off identical to 0.6.0
(research R1, R2). Two ceilings solve the declared piecewise-constant-velocity problem by
generalised least squares with the true error covariance (R3); a classical robust control
estimates what it can of that covariance from residuals (R5). Headroom is the robust control's
median range error over the attainable ceiling's, **both on the true segmentation**, so that
segmentation shortfall already measured at Gates S and 2 is not counted as error-model headroom
(R6). Gate H (R7) is proposed as an SRD row, bound by a decision record, checked for soundness on
validation seed 321 and scored once on test seed 322.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: NumPy, numba, PyTorch 2.x (physics layer, double); nothing new.

**Storage**: f32pack splits with a mismatch-truth side file; NDJSON predictions; `errors.npz`;
results branches.

**Testing**: `pytest` (golden: mismatch off = 0.6.0 bytes), `ruff`, `mypy --strict`.

**Target Platform**: CI runners for generation, tuning and scoring (`score/**`, `tune/**`); the
session for seconds-long steps only.

**Project Type**: research library and CLIs.

**Performance Goals**: a ceiling solve under 50 ms per scored row (a Cholesky of at most 720 × 720
per row); the primary test condition scored in one CI run under 6 h with shards.

**Constraints**: mismatch off byte-identical; estimators never read the mismatch truth; comparisons
within one scoring run; one long CI run at a time.

**Scale/Scope**: 16 conditions (off; 4 kinds × 3 severities; all four at mild, central, harsh).
Tuning seed 320: 500 scenarios per condition. Validation 321: 1,000 per condition. Test 322:
5,000 for the primary condition, 1,000 each for off and the four single kinds at central. The
same seed gives the same tracks under every condition, so conditions are paired.

## Constitution Check

- **I. Types once (LinkML)**: `MismatchCondition`, `MismatchTruth`, the Gate H plan, decision and
  headroom record are added to `schema/tma.yaml`; generated types follow. Pass.
- **II. Determinism**: the overlay draws from its own stream derived from the scenario seed; the
  kernel's draws and their order are untouched. Plans and records bound by digest. Pass.
- **III. Physics does the numerics**: every scored estimate is the declared piecewise-CV solve;
  the ceilings and the control change only the residual weighting. Pass.
- **IV. Honest measurement**: naive, batch least squares, re-tuned IMM and EKF, the oracle
  ceilings and the bound on the same rows; efficiency per slice; settings from the tuning seed
  only; severities fixed before scoring. Three seeds per carried configuration does not apply
  (nothing is trained); recorded as not applicable. Pass.
- **V. Fail fast through gates**: pre-registered Gate H, a soundness rule on validation, a fresh
  test seed, the panel. Pass.
- **VI. Portable artefact**: no model is carried, so nothing is exported. Not applicable.
- **Classification**: severities are a declared design grid, not any real sensor's figures. Pass.

## Project Structure

```
specs/010-headroom-mismatch/    spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
schema/tma.yaml                 MismatchCondition, MismatchTruth, GateHPlan, HeadroomRecord
src/tma2/sim/mismatch.py        the overlay (numba): draws, composition, truth arrays
src/tma2/sim/generate.py        version 0.7.0 option; side file `<split>.mismatch.npz`
src/tma2/headroom/cov.py        error covariance from parameters; Cholesky whitening with gaps
src/tma2/headroom/gls.py        whitened piecewise-CV solve through the physics layer's residuals
src/tma2/headroom/ceilings.py   attainable and realisation ceilings
src/tma2/headroom/robust.py     the classical robust control (Huber, σ̂, ρ̂ whitening)
src/tma2/headroom/crb.py        the bound under the true covariance
src/tma2/headroom/gate.py       Gate H criteria; operational units
src/tma2/cli/hpredict.py        tma2-hpredict {ceiling,robust}
src/tma2/cli/gh.py              tma2-gh (tma2-gs scoring with --predictions, plus headroom)
configs/gateh/gh-a.json         the plan; configs/gateh/conditions.json the 16 conditions
.github/workflows/score.yml     kind `gh`; tune.yml reused for the IMM/EKF re-tune on 320
scripts/research/gh_charts.py   the slides post's figures
```

## Phases

1. **Data** (US1): overlay, schema, generator option, golden test for mismatch off, statistics
   test per kind, the estimator-isolation test (FR-005). Generate seed 320 on CI.
2. **Ceilings and bound** (US2): covariance and whitening, the whitened solve, both ceilings, the
   bound. Tests: mismatch off equals the existing oracle (the whitening branch is not taken, so
   row for row); efficiency against the bound on seed 320.
3. **Robust control** (US3): the estimator and its ablations (each fix alone). Settings chosen on
   seed 320 from the declared grid (R5). IMM and EKF re-tuned on seed 320, primary condition.
4. **Gate H proposed** (US4): SRD §5 row (owner merges), plan `gh-a.json`, decision record with
   forecasts and the soundness bands measured on seed 320. No scoring on 321 or 322 before it.
5. **Validation** on seed 321: soundness rule (H-a, H-b); headroom reported, not acted on.
6. **Test** on seed 322, once; panel; write-up; slides post; PR.

## Complexity Tracking

| Item | Why | Simpler alternative rejected because |
| --- | --- | --- |
| Two ceilings | the attainable one handles outliers by an approximation (R3) | the realisation ceiling brackets it from above, which shows whether the approximation matters |
| Headroom on the true segmentation | isolates the error model | on C's segmentation the gap is already above 10% with no mismatch at all (C recovers 0.898 of the gap), so the verdict would be decided before the experiment |
| A separate overlay stream | byte-identity with 0.6.0 | drawing inside the kernel would shift every later draw |
