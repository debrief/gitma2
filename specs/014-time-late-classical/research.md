# Research: spec 014

## R1. Keeping Gate T's search as registered

- **Decision**: Gate T's code is frozen by its commit (34da02f; a `git worktree` reproduces
  it). In the working tree, new behaviour is added behind settings whose defaults reproduce
  Gate T, and a fixture (two tuning periods of seed 329: candidates' evidence, spans and
  tracks) pins that to 1e-4 (the evidence moves 2e-7 between CPU families). The code digest in new shards necessarily differs.
- **Rationale**: the digest covers every module in `timelate/`, so any addition changes it;
  equality of output is what matters and is what the fixture tests.
- **Alternatives**: a copied package `timelate2` (duplicates 2,000 lines); never touching
  `timelate/` (makes the corrected prior and the controls impossible to share code with).

## R2. The corrected prior

- **Decision**: `ManoeuvrePrior.version` 1 (Gate T) or 2. Version 2: leg curvature counted
  once; the uniform-direction term given its proper volume; the leg-length normal renormalised
  above its minimum. Effect reported on tuning seed 333 (track error, counts, calibration)
  before use; version 2 is then the search of this spec, named `search2`, and Gate T's is
  scored beside it as `search` on every primary split.
- **Rationale**: all three errors penalise extra manoeuvres (at most about 0.35 nats each),
  and the search under-counts; the size of the effect is unknown and must not be confounded
  with the other studies.
- **Alternatives**: leaving the errors (the panel recorded them); fixing silently.

## R3. The two controls

- **C″ refit** (`c2-refit`): C″'s transitions as spans, kinds chosen by evidence
  (`choose_kinds`), one joint fit to the posterior with times free, started from C″'s own
  states and from the neutral starts, best evidence kept. No add, remove or re-kind moves.
- **Flat-prior search** (`search-flat`): the same search with the prior over histories replaced
  by uniform densities over the solver's own box (turn up to its bound, speed change up to its
  bound, times uniform over the period, kinds equally likely), the state prior unchanged and
  the Occam volumes kept.
- **Rationale**: the refit has the model, the prior on magnitudes and the whole period but not
  the search; the flat search has the model, the whole period and the search but no manoeuvre
  statistics. Gain(C″ → refit) ÷ gain(C″ → search2), in log track error per period, is FR-005.
- **Alternatives**: a BIC penalty as "flat" (a different approximation, not the same search
  with less knowledge); refit with times held (C″'s times are causal and late by design).

## R4. Classes of wrong-history periods and the attainable headroom

- **Classing**: Δ = evidence of the true history's structure (fitted to the posterior from
  the neutral starts and from the search's own best track; never from the true states) minus
  the evidence of the search's first candidate. Ambiguous: |Δ| ≤ 3. Search failure: Δ > 3.
  Evidence failure: Δ < −3. Sensitivity at 1 and 5 is reported. "Wrong" is Gate T's match rule
  (same count, mid-times within 120 s), with 60 s and 240 s beside.
- **Composite systems**: `ident-search` uses the true history's fit on search-failure periods
  and `search2` elsewhere: what a perfect search under the same evidence would give.
  `ident-all` also uses it on evidence-failure periods: what a perfect evidence would add.
  Ambiguous periods are never replaced.
- **Headroom statistic**: the geometric mean over periods of `search2` ÷ composite in period
  median range error, with a period bootstrap; the ratio of medians (Gate T's statistic) is
  reported beside. Material: interval wholly above 1.10. Not material: interval wholly below.
  Otherwise inconclusive.
- **Rationale**: the composites differ from the search on a minority of periods, so a paired
  median ratio is exactly 1 and useless; a mean of log ratios is not. To be confirmed on the
  tuning seed before registration (phase 3).
- **Risk**: 3 is a convention (a factor of 20 in probability). Hence the sensitivity bands,
  and the threshold is fixed here, before any tuning result.
- **Alternatives**: dropping ambiguous periods from both sides (changes the population);
  judging ambiguity by track error (uses the truth's states).

## R5. Held-course periods

- **Decision**: `tl-quiet-ranges.json`: Gate T's ranges with the target's manoeuvres removed
  (as `configs/regress/held-course-ranges.json` does for spec 012), 5-second bearings, the
  ownship as in Annex B. A false manoeuvre is any manoeuvre in the first candidate (search)
  or any transition (C″). 400 test periods give ±5 points at any rate. Track error is compared
  with the one-leg fit on determined rows.
- **Generate locally first** (gotcha from spec 013's shifted file).

## R6. Thinning

- **Forms** (spec 013 R7): one bearing in n; fixed normal points of n (line fit, variance
  σ²/n); adaptive bins by bearing-rate steadiness; the robust-line variant under outliers.
  n in 2, 4, 6, 12.
- **Applied to** the bearings the arc fit and the evidence see; scoring rows are unchanged.
- **Adoption rule** (fixed here): the longest fixed bin whose cost in track error (geometric
  mean paired ratio to full data) is under 2% with an interval excluding 5%, and which saves
  at least 30% of run time; adaptive bins only if they beat that bin on run time at no more
  cost; under outliers the robust variant is reported, and adopted only if it is no worse
  than the plain one on clean data by the same rule. 100 tuning periods.
- **Evidence caveat**: binning changes the likelihood's normalising constant equally for all
  histories of a period, so evidence differences are comparable within a form, not across.

## R7. Counts, splits and conditions

- Counts: matched, missed, false and timing error at 60, 120 and 240 s, for every system that
  states manoeuvres; manoeuvres cut by the period's edges excluded.
- Splits: ownship manoeuvres in the period (0, 1, 2 or more), leg position (first, middle,
  last), range band (terciles of true range), true manoeuvre count (0, 1, 2, 3 or more).
- Conditions: spec 010's overlay at its primary severities, correlated alone and outliers
  alone, 100 test periods each, with the stated σ unchanged. Whether the overlay's correlation
  time is in seconds or samples is checked before use (5-second bearings).
- Whole engagements: 60 uncut test engagements.

## R8. The smoothed filter

- **Decision**: a Rauch–Tung–Striebel fixed-interval smoother over the frozen, tuned EKF
  (`ekf-rts`). It is named for what it is: a constant-velocity smoother with process noise,
  the conventional whole-period method, with no manoeuvre model.
- **Alternatives**: an IMM smoother (several published forms, none in the repository; a
  second approximation to defend); the forward filter (silent on 60% of rows).

## R9. A registered study, and the recommendation rule

- **Decided on fresh seeds** (decision record before seed 334 exists): the refit's share of
  the gain (FR-005), the three class shares and both headroom figures (FR-007), the
  false-manoeuvre rates (FR-010). Each with a forecast.
- **Recommendation rule** (SC-006): pursue a learned whole-period model only if `ident-all`
  headroom is material; if so, it is registered against `search2` and `c2-refit` under the
  same prior, on the Annex B, shifted and held-course splits. Not material, or inconclusive:
  do not spend GPU budget on it; the reason is stated.
- **Soundness stop** (validation): the reference from neutral starts within [0.8, 1.3] on
  tightly bounded rows, and at least 90% of true-history fits converged.
- **SRD**: one §9 line records the study and its rule (owner merges); no §5 row.

## R10. Run time and sizes

- **Unknown until measured**: Gate T ran 25 periods a shard inside a 350-minute limit. Phase 1
  measures seconds per period for each system on the runner.
- **Rule**: if the test seed as sized would need more than 40 shard-jobs of 350 minutes, sizes
  are cut in this order before registration: whole engagements to 30, mismatch conditions to
  60 each, shifted to 200, then Annex B and held-course together to 300. US6 is cut first.
