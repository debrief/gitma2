# Gate H decision record (spec 010 T019, T020)

`decision.json` (a `GateHDecision`) is committed before validation seed 321 or test seed 322 is
generated, and so before any score on either. It binds `configs/gateh/gh-a.json` by SHA-256
(`plan_digest` `26d8e898…`) and the conditions file (`d260fd75…`); the plan is never edited after
this. Later additions are new files here. No criterion may change once a validation or test
result exists.

## Fixed here

- **The SRD:** §5 Gate H row as proposed on this branch (owner to merge). The criteria below are
  the row's.
- **Nothing is trained.** No learned estimator takes part in the verdict.
- **Data:** generator 0.7.0's overlay on MAN2, the 16 conditions of
  `configs/gateh/conditions.json` (owner accepted the grid, 2026-11-09); primary `all-central`.
  Validation: seed 321, count 2,600, the `train` split's first 1,000 σ = 1° scenarios, every
  condition. Test: seed 322, count 13,000, every σ = 1° scenario of the primary condition (about
  5,200), and the first 1,000 of `off` and of the four single kinds at central. Re-score, only if
  H-c is inconclusive: seed 323, count 26,000.
- **Estimators, all on the true segmentation** (12 knots, speed prior): the plain solve; the
  robust control with the grid's settings (Huber constant 2.0, σ and correlation from residuals,
  no shrinkage, three reweightings; `experiments/20261110-gh-grid/`); the attainable and
  realisation ceilings. Reported beside them: one leg, the plain oracle solved in the scoring
  run, the IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` and the EKF `ekf-sa0.00003-p4-r0.5`
  (`experiments/20261110-gh-refs/`).
- **Criteria** (`decision.json`):
  - **H-a** (soundness): the attainable ceiling's range efficiency on settled rows of the primary
    condition within [0.9, 1.6], and its median range error no worse than the plain solve's.
  - **H-b** (soundness; owner, 2026-11-10): on mismatch-off data the robust control's median
    range error over the plain solve's, minus 1, is at most 5%, and its interval is not wholly
    above 2%.
  - **H-c** (the verdict; owner, 2026-11-09): R, the robust control's median range error over the
    attainable ceiling's, minus 1, on the primary condition. Material if the interval is wholly
    above 10%; not material if wholly below; otherwise inconclusive, one re-score on seed 323,
    then final.
- **Statistics:** paired, scenario-clustered percentile bootstrap, 97.5%, 2,000 resamples. All
  G5 rows; a row an estimator does not answer is an infinite error. The same comparison on the
  rows every estimator answers is reported, not gated.
- **Validation rule:** H-a (primary) and H-b (off) on seed 321. A failure stops the gate before
  seed 322 is generated. H-c is reported on validation and cannot stop the gate.
- **The panel decides.** Five reviewers, rounds until decided.

## Forecasts (from tuning seed 320 only)

| Check | Forecast | Probability |
| --- | --- | --- |
| H-a | efficiency about 1.25; pass | 0.90 |
| H-b | cost about +3%; pass | 0.75 |
| H-c on test | R about +1.5%, interval about [−1, +4]; **not material** | 0.85 |
| | inconclusive | 0.12 |
| | material | 0.03 |

## What the tuning seed has already shown, and what that does to this gate

The tuning runs make "not material" the expected verdict. That is disclosed, not hidden: the
threshold (10%) and the conditions were fixed by the owner before any tuning run, the control's
settings were chosen by a declared rule, and validation and test seeds are untouched. The gate's
job is now to confirm or contradict the tuning seed on fresh data at ten times the size.

## Known weaknesses, stated before the result

- **The ceiling is the ceiling of this solve.** It is 1.2 to 1.6 times the Cramér–Rao bound
  because the oracle fits each manoeuvre by a chord. A verdict of "not material" says a learner
  of the *error model* has little to win on this estimator. It does not say nothing better than
  this estimator exists.
- **The attainable ceiling treats outliers by an approximation** when errors are correlated. The
  realisation ceiling, which is exact, is reported beside it to show whether that matters.
- **Target-motion mismatch is not tested**, nor a classical bias state, nor other severities.
- **H-b's cost on the tuning seed was +4.0%** at the chosen settings (interval −3.0 to +7.6 at
  95%). A failure of H-b on validation is a real possibility and would stop the gate.
- **Before the test run** the workflow needs shards: about 5,200 scenarios exceed one job's
  time limit. That is plumbing, and changes no setting bound here.
