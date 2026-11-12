# Implementation Plan: Time-late, the classical follow-on to Gate T

**Branch**: `014-time-late-classical` (developed on `claude/keen-wozniak-77td7j`) |
**Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/014-time-late-classical/spec.md`.

## Summary

Nothing is trained and no GPU is used. Gate T's search stays as registered (its commit, and a
regression fixture that pins its output; research R1). A corrected prior is a second version
selected by a setting, and its effect is reported before anything else uses it (R2). Two
controls split Gate T's gain: C″'s transitions refitted over the whole period with the arc
model and prior, and the search with a flat prior (R3). Every period where the search's first
candidate is wrong is classed by the evidence difference between the true history and the
search's, both fitted from starts that do not use the truth; a composite "better identifier"
system built from those classes gives an attainable headroom (R4). Held-course periods give a
false-manoeuvre rate (R5). The thinning study runs on the search with spec 013's adoption rule
(R6). Counts, timing, splits, mismatch conditions, whole engagements and a smoothed filter
complete what spec 013 owed (R7, R8). It ends in a registered study, not a gate: nothing here
is carried or stopped by a threshold, but what is decided on fresh seeds is written down with
forecasts first, and the panel reviews it (R9).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: NumPy, numba, PyTorch 2.x (C″ only, double); nothing new.

**Storage**: f32pack periods; shard `.npz` + `.json` headers (`tma2-tlsolve`); `summary.json`,
`*.periods.json`, and now per-row errors in the experiment folder as `errors.npz` (the Gate T
panel had to fetch them from results branches).

**Testing**: `pytest` (Gate T fixture unchanged to 1e-9 with prior version 1; the corrected
prior integrates to 1 over its support on a grid; the flat prior is constant inside the box;
the refit control never calls the search; classing is antisymmetric in its two histories;
thinning with bin 1 equals the full data; the smoother equals the filter at the last row;
C's digests unchanged), `ruff`, `mypy --strict`.

**Target Platform**: CI runners (`timelate/**`); the session for seconds-long steps only.

**Project Type**: research library and CLIs.

**Performance Goals**: measured first (R10). Each fresh-seed run completes as one CI run of
shards inside the 350-minute job limit; long runs are queued one at a time.

**Constraints**: C and C″ digests unchanged; Gate T's plans, records and decision untouched;
no system reads the truth except the reference and the classing (history structure only, never
states); comparisons within one scoring run; no paid compute.

**Scale/Scope**: tuning seed 333 (150 Annex B periods, 60 shifted, 100 held-course);
validation 334 (150 Annex B, 150 held-course); test 335 (400 Annex B, 300 shifted, 400
held-course, 100 correlated, 100 outlier, 60 whole engagements). Reduced by a rule in R10 if
run time demands it, before registration.

## Constitution Check

- **I. Types once (LinkML)**: `TimeLateStudyCriteria`, new fields on `TimeLateShardHeader`
  (prior version, thinning, condition), schema 0.36.0. Pass.
- **II. Determinism**: periods and mismatch overlays from their own seeded streams; no other
  randomness (the bootstrap is seeded). Pass.
- **III. Physics does the numerics**: every track is a declared model's fit (chord layer for
  C″, arc model for the rest, the filter's own model for the smoother). Pass.
- **IV. Honest measurement**: C″, one leg, the reference from neutral starts, the bound and the
  filters on the same rows; efficiency per slice with a statement of where the bound does not
  apply; paired statistics beside every ratio of medians; settings from the tuning seed. Three
  seeds do not apply (nothing trained). Pass.
- **V. Fail fast through gates**: no gate; a registered study with a decision record before
  seeds 334 and 335 exist, a soundness stop on validation (the reference from neutral starts
  within Gate T's band on tight rows, and at least 90% of true-history fits converged), and the
  panel. Justified in Complexity Tracking.
- **VI. Portable artefact**: no model. Not applicable.
- **Classification**: simulated data only. Pass.

## Project Structure

```
specs/014-time-late-classical/   spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
schema/tma.yaml                  TimeLateStudyCriteria; shard header fields (0.36.0)
configs/timelate/                tl-quiet-ranges.json; tl-c.json (plan); runs/tl-c-*.json
src/tma2/timelate/prior.py       version 2 beside version 1 (selected by ManoeuvrePrior.version)
src/tma2/timelate/flat.py        the uninformative prior over histories
src/tma2/timelate/controls.py    C″ refit with arc model and prior
src/tma2/timelate/classify.py    wrong-history classes; the composite systems
src/tma2/timelate/thin.py        dropping, fixed and adaptive normal points for the arc problem
src/tma2/timelate/smooth.py      fixed-interval smoother over the frozen EKF
src/tma2/timelate/counts.py      matched, missed, false, timing error at several tolerances
src/tma2/timelate/study.py       the study's readings and its recommendation rule
src/tma2/timelate/run.py         new systems and settings; Gate T's systems unchanged
src/tma2/cli/tlsolve.py, tlscore.py   new options; `--study` reading
tests/unit/test_timelate2.py     the tests above; tests/fixtures/timelate/gt-fixture.json
scripts/research/tl2_*.py        tuning-seed studies (thinning, run time, class thresholds)
.github/workflows/timelate.yml   mismatch condition and quiet split in generation
experiments/                     tuning records, decision, validation, test
```

## Phases

1. **Pin and measure**: Gate T regression fixture; run time per period by system on the
   runner (R10); per-row errors saved by the scorer; counts and paired statistics in the
   scorer (FR-013, FR-014, FR-015). No new estimator yet.
2. **Corrected prior** (FR-002): version 2, its effect on tuning seed 333 beside version 1.
3. **Controls and classes** on the tuning seed: C″ refit, flat-prior search, classing, the
   composite systems; check that the headroom statistic is not degenerate (R4).
4. **Thinning study** on the tuning seed; apply the adoption rule; later phases use its outcome.
5. **Held-course split, mismatch conditions, whole engagements, the smoother**: generate each
   ranges file locally first; smoke run on CI.
6. **Register** (decision record with forecasts, plan `tl-c.json` bound by digest), validation
   seed 334 with the soundness stop, test seed 335 once, panel, write-up, slides.
7. **If time allows**: the mismatch diagnostic and broadened prior (US6), reported only.

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected because |
| --- | --- | --- |
| A registered study, not a gate (principle V) | Nothing is carried or stopped by a threshold here; the output is a decomposition and a recommendation to the owner | A gate would need pass and fail lines for quantities whose purpose is to be measured; forecasts and a recommendation rule fixed beforehand give the same protection |
