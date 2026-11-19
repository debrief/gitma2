# Spec 028 decision record: the previous window as a prior

This record was registered on 2026-11-19, before seeds 355 and 356 existed. It is a registered
study, not a gate: nothing is trained and nothing runs on GPU. Run on CI, `tma2-long carry2`
solves `ctl`, `ctl-carry` and `ctl-prior` in one job per engagement and contact, and
`tma2-long study27` scores them.

## Bound

`decision.json` holds the registration and `digests.json` binds:
- the configs: `cp-val.json`, `cp-test.json` and `carry2.json`;
- the run files `configs/long/runs/cp-{val,test}.json`;
- the priors and C's parameters;
- `long.yml`;
- the spec and the plan;
- one code digest, `09a7edae…`, over `src/tma2/long/`, `src/tma2/timelate/`,
  `src/tma2/cli/long.py` and the simulator's prng and geometry.

Bound files are not edited from here on. Anything new goes in new scripts.

## Settings

The settings were chosen on tuning seed 354 by the plan's rules
(`experiments/20261118-cp-tuning/`):
- **Covariance scale:** 4 on the carried Laplace covariance.
- **Tail:** 1,200 s of manoeuvre time the bearings could not show.
- **Guard level:** α = 0.001 for the χ²(4) guard.

## Rule

- **Estimand:** the geometric mean over windows of ctl ÷ ctl-prior, from per-window median range
  error. Each chain's first window is excluded. The interval comes from the engagement bootstrap.
- **Gain:** the lower limit on the weak-geometry split is above 1.
- **Harm:** the upper limit is below 1 on weak, other, contact 1 or contact 2, in range, course
  or speed.
- **Otherwise:** the outcome is "not shown, at this size".

## Validation soundness (seed 355)

The study stops before the test if any of these fails:
- **S1:** at least 95% of windows ran.
- **S2:** the per-engagement geometric mean of ctl ÷ the true-history fit lies in [0.8, 4].
- **Coverage:** contact-1 coverage of the carried 95% region lies in [0.80, 0.99].

## Forecasts

These are written now, before seed 355 exists.

- **Weak split, range:** about 1.2 to 1.4, lower limit above 1 with probability about 0.6. On
  tuning it was 1.52 [1.006, 2.45] at scale 2. The registered scale of 4 pulls less, so the
  effect should shrink.
- **Other split, range:** about 0.95. Harm, an upper limit below 1, has probability about 0.3.
  On tuning it was 0.92 [0.78, 1.11]: where the window's own bearings are rich, the prior can
  hold a stale estimate.
- **Weak split, course:** a gain in course is more likely than in range (tuning 1.87).
- **Guard:** it falls back on 1–4% of windows.
- **Coverage:** contact 1 at about 0.88–0.92; contact 2 lower.
- **Joint solve:** a full joint solve remains better than the hand-over. On tuning, ctl-prior
  was 1.7 times the joint error, from 12 pairs, reported only.

## Known before any result

- **Split mix:** the weak split is mostly contact 2 (60 of 73 tuning windows). The
  "at most one ownship turn" clause never fires in this simulator. A gain is therefore mostly a
  statement about the untended contact and about windows near gaps.
- **Coverage:** the carried prior is overconfident even at scale 4 (0.90 for a stated 0.95).
- **What is carried:** the hand-over carries one state, not a second-best manoeuvre history.

**After merging main (2026-11-19).** This study was registered and run as spec 027. Another
session's spec 027, carrying state across gaps (PR 49), merged first, so this one is now
spec 028. Its folder moved from `specs/027-carry-prior/` to `specs/028-carry-prior/`.

- **Bound files:** the spec and plan are unchanged; their contents still match the bound
  digests under the new path. Configs, code and raw outputs still say 027 and were not edited.
- **Code digest:**
  - The merge added three modules under `src/tma2/timelate/`: `carry.py`, `run9.py` and
    `study9.py`. The code digest's glob picks them up, so at the merged commit it no longer
    equals `09a7edae…`.
  - Over the bound file list, the digest still equals `09a7edae…`, so no bound module changed.
- **Seeds:** that study had skipped seeds 354–359 to stay clear of this one, which used
  354–356. Seeds 357–359 are unused; the next fresh seed is 362.
