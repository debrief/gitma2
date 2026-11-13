# Spec 014: panel review, round 1 (2026-11-13)

Five independent reviewers read the spec, the decision record, the tuning, validation and
test records and the code at the registered commit, and recomputed from the per-row errors
and per-period records. **All five: approve with findings. Decided in one round.** The
registered figures stand as registered. Two defects in the registered code move decided
numbers, and most of the README's readings were stated more firmly than the data allow.

## Verdict on each decided quantity

| | As registered | Panel |
| --- | --- | --- |
| D1 | 0.43 [0.28, 0.58] | Reproduced. **"About half", not "under half"**: 0.4 to 0.6 by estimand; four numerical failures of the control carry the point estimate |
| D2 | 0.53 / 0.08 / 0.39 | Reproduced. **Moved by a defect**: manoeuvres cut by the period's edge are counted; without them 0.61 / 0.12 / 0.27. "Ambiguous" is a property of this evidence at a wide threshold, not of the bearings |
| D3 | 1.04 not material; 1.10 inconclusive | Reproduced. **Convention-bound**: 1.05 to 1.20 across the registered thresholds; the composite is a noisy oracle, not an upper limit |
| D4 | 0.76 / 0.02 / 0.01 / 0.03 | Reproduced. **Partly a defect**: the duration of a manoeuvre is given too large a volume; re-ranking the stored candidates with a corrected volume gives 0.47 to 0.57. The direction stands |
| D5 | No GPU budget | **Follows from the rule, not from the evidence.** The evidence is on the line where the simulator's assumptions hold and silent on a robust or hedging model |

## What was checked and found sound

- D1 to D4, the paired ratios, class counts, counts at three tolerances, candidates, the
  splits and soundness all recompute from the per-row errors with independent code.
- All nine configuration digests and four scorer digests in `decision.json` equal the files
  at 78f423f and at HEAD; the time-late code digest equals every shard header of both runs;
  `git diff 78f423f HEAD -- src configs .github schema` is empty.
- The rule for D5 (research R9) was committed before the tuning run was created. One test
  run exists, attempt 1; the committed records are byte-identical to the results branch.
- The test run was created 16 minutes after validation's score existed.
- No system that should not have the truth receives it. The reference and the classing use
  the true history's structure only, never its states.
- Recomputing `log_evidence` for every stored candidate from its stored parameters agrees
  with the record to 3e-7 on the gate's CPU family.
- Prior version 1 is line for line Gate T's. The mixture is a correct mixture. The
  smoother's recursion is right. The held-course split is fair (it differs from Annex B in
  leg length only; the ownship manoeuvres as often).

## Major findings

1. **A defect in the evidence rewards small, short manoeuvres** (code review). Prior version
   2 kept version 1's stand-in volume for a manoeuvre's duration (about 600 s) while the
   prior's density for it is sharp (20 to 120 s for a minimum-size change). Each such
   manoeuvre gets 2 to 3 nats of unearned Occam factor. The 360 manoeuvres invented on held
   course are of this kind: 167 are speed changes of about 1 m/s over 20 s, at the prior's
   lower edge. Re-ranking the five stored candidates and the no-manoeuvre history with a
   corrected volume gives a false rate of 0.47 to 0.57 against the registered 0.76, and on
   Annex B data changes the first candidate in 56 to 84 of 400 periods, raising "first
   candidate right" from 205 to about 218. The effect on D1 to D3 needs the search re-run.
2. **The classing counts manoeuvres the spec says to exclude** (three reviewers). 70 of 400
   Annex B periods have a manoeuvre cut by the period's edge; 62 are classed wrong, and in
   35 the search's history equals the truth without it. Edge-aware, on scored periods: 147
   wrong, 0.57 / 0.11 / 0.33; "true history first" 0.51 becomes about 0.60. Half the
   evidence failures contain a cut manoeuvre. D3 barely moves (1.10 [1.04, 1.17]).
3. **The "true history" fit is often not the true history** (two reviewers). With times
   free, 50 of 389 fits drift more than 120 s from the true times; 16 become the search's
   own history. On the periods it replaces, the true-history fit is worse than the search
   in 35%. On validation the "perfect evidence" composite (1.04) is below the "perfect
   search" one (1.08): a statistic where fixing more failures lowers the headroom is not an
   upper limit.
4. **D3, and so D5, depend on conventions the README did not show** (four reviewers). With
   a perfect evidence: threshold 1, 1.18 [1.10, 1.28]; threshold 3, 1.10 [1.04, 1.18];
   threshold 5, 1.05 [1.01, 1.09]. With times held as the replacement 1.17 [1.09, 1.25];
   replacing only where it helps 1.17 [1.11, 1.24]; replacing every wrong period 1.25
   [1.15, 1.36]; three seeds pooled 1.13 [1.07, 1.20]. Five periods carry half the gain.
   "Inconclusive" is robust; "little left to win" is not: the interval admits 18%.
5. **"Ambiguity no identifier can remove" is unsupported.** On the 94 ambiguous periods the
   search is at 0.057 against 0.026 for the true-history fit; in 28 the true history has
   the higher evidence; the true history is in the first three candidates in 0.45. The
   evidence difference's own noise is comparable with the threshold: where the search's
   history equals the truth it still ranges from −10.6 to +9.4, and on another CPU family
   it moves by more than 1.6 in a tenth of periods. And a learned model need not identify
   at all: an error-minimising estimator can hedge across histories, as spec 012's
   regressor did. Nothing here bounds that.
6. **D1 is "about half" and the refit is handicapped.** Four of 369 refits ran away
   numerically (errors of 149 to 39,806); without them 0.52 [0.41, 0.65]. By estimand 0.39
   to 0.58. Three seeds pooled 0.47 [0.36, 0.59]; their spread (0.79, 0.30, 0.43) is
   marginally consistent with noise (p about 0.09), so "the first was the outlier" is not
   shown. The refit inherits C″'s misses, so "the search's share" includes simply having
   more manoeuvres. The share is condition-dependent: 0.06 under the shift, 0.76 with
   correlated errors. The cleaner decomposition was in the summary and unreported: the
   flat-prior search obtains 0.78 [0.67, 0.91] of the gain; the manoeuvre statistics are
   worth about a fifth. Gate T's "mostly smoothing" is qualified, not overturned.
7. **The rule reads the one condition where the answer is nearly foregone.** On Annex B data
   the search holds the generator's motion model, prior and noise law. The gaps of 1.5 to
   1.9 are under the shifted prior, correlated errors and outliers, and no remedy, classical
   or learned, was built for them (User Story 6 was cut; no sampler in place of Laplace; no
   Huber cost in the search). Held course does not belong in that list: its 1.88 is
   self-inflicted and the mixed prior is at the true-history fit there.
8. **The mixed prior is not free** (held-course review). In all 24 Annex B periods where it
   changes the answer it switches to "no manoeuvre", and 21 of those targets manoeuvred.
   Declared "held course" on a manoeuvring target: 1.9% to 7.8% of periods; on periods with
   one true manoeuvre, 6.0% to 19.7%. Its 3% depends on its half: re-weighting the stored
   evidences gives 0.20 at a tenth and 0.013 at 0.8, and a split that is all quiet rewards
   any large weight. The flat-prior search already solves the held-course problem (1%) and
   the record did not say so.
9. **The cause of the false manoeuvres was stated incompletely.** The prior's leg term
   decides long periods (false rate 0.98 to 1.00 over an hour). Under 30 minutes the search
   still invents one in 46%, and in 4 of Annex B's own 11 held-course periods: there the
   Occam factor cancels the prior's cost and a noise-level gain in fit decides. A manoeuvre
   the bearings cannot exclude costs nothing net under this evidence (and less than nothing
   with finding 1).
10. **The thinning study tests less than it says.** The adaptive rule breaks bins on noise at
    the tolerances run (on a perfectly steady bearing rate the mean bin is 8 rows at
    tolerance 3): it tested noise-set bins, not the owner's idea, and the README's
    explanation is probably wrong. "Normal points lose little" is not shown (intervals to
    1.19 to 1.32). The adoption rule was unmeetable on 90 periods and that was knowable.
    Under outliers the edit was not separated from the binning, a Huber cost in the fit was
    the obvious comparator and was not run, and 10-sd outliers against a 4-sd edit is the
    easy case. The edit's parameters were chosen on the periods it is scored on.
11. **The README's systems table had a wrong row** (flat-prior search: four of six columns
    copied by hand and wrong) and several third-decimal slips. Regenerated from
    `summary.json`.

## Minor findings

- Forecast calls too generous: D4's mixed-prior forecast (0.10) is excluded by 0.03
  [0.02, 0.05]; D2's ambiguous interval excludes 0.45; "every true-history fit consistent"
  was missed by one period; "the search's counts most" under correlated errors is right as
  a ratio only (C″'s false count rose more in absolute terms).
- The tuning seed ran earlier code (50acc2e) than the registered commit: the forecasts come
  from another code digest. Stated before only for the mixed prior.
- D2's shares are of 195 wrong periods among all 400; D3 uses the 369 scored (176 wrong).
- FR-007's ratio of medians (1.07 [0.96, 1.23]) and FR-008's truth-in-first-three by class
  were in the summary and not in the README. FR-002's effect on calibration is not reported.
- `history_right` ignores kinds: 40 of 193 "right" periods differ from the truth in kind.
- Evidence values are not reproducible across CPU families to the precision of the margins.
- The Laplace volume probably also favours an extra manoeuvre slightly at the 10 s duration
  floor (about +0.7).
- `_leg_sf` and `_leg_tail` were not updated for version 2 (1.4%); the flat prior
  over-credits by log m! where starts are open; a manoeuvre ending exactly on the last row
  is flagged as cut; `controls.py` can clip a span past the period's end (no case on test).
- The smoothed EKF has no state on 8% of Annex B rows and smooths each stretch alone; its
  figure partly reflects lost states. Not a recursion bug.
- Tests: no test with an edge manoeuvre; only the leg density is integrated (a whole-prior
  check would have caught finding 1); `run_shard2` and `study_split` are untested.
- SC-007 is not met from committed files: the per-row errors are on the results branch.
- Every split is generated from the same seed with different ranges files: the splits are
  not independent samples of geometry.

## What the panel wants next

1. Fix the duration volume, the edge rule in classing and the drifting reference; re-run
   under a new registration, since they move D2 and D4 and may move D1 and D3.
2. The cut classical work, aimed at the 1.5 to 1.9 gaps: a broadened or mixture prior with a
   mismatch diagnostic, a Huber or edited likelihood in the search, a correlated-error model.
3. A posterior-weighted (hedged) track from the candidates, as the classical control for any
   error-minimising learner.
4. Only then a learned model, registered against those on the shifted, quiet and mismatch
   splits.
5. Thinning, if run time ever matters: normal points on enough periods, the compression
   ratio recorded, the edit alone, and an adaptive rule that does not break on noise.

## What should not be concluded

That learning cannot help time-late TMA; that half of wrong histories are irreducibly
ambiguous; that the search's share of the gain is 57%; that bearing-rate-adaptive binning is
a bad idea; that normal points are free; that the mixed prior is free; that 76% is the rate
at which a sound evidence invents manoeuvres.
