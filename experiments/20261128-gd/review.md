# Review panel, round 1: spec 038 test record

Three reviewers (fidelity, statistics, critical) read the decision record, the test record and
the per-row errors, each with their own code (`panel/`). **All three approve with findings.**
Every registered number reproduced (G 0.439 [0.346, 0.530] with other bootstrap seeds; the seven
labels follow the registered lines; the 18 bound files hash identically at the test's commit; the
edit's causality and the segmentation cache hold). No outcome label flips under any alternative
statistic. The findings narrow what the record's prose may say; the README is corrected to them.

## Findings that change what may be said

1. **G is a tail and a best case (statistics, critical, fidelity).** 0.439 of the *mean* log gap,
   carried by about a quarter of engagements: the median engagement closes about a quarter (0.26
   as a ratio of median logs; 0.29 to 0.40 trimmed at both ends); in median absolute error 0.53.
   The control's ratio to C″-robust is 1.43 in geometric mean and 1.22 in median (better in 62%,
   twice as good in 28%, twice as bad in 11%); it gains where C″ fails badly (2.54 where the
   regressor leads by over 3) and loses elsewhere (0.86 where the lead is under 1.5). By split it
   is 0.26 to 0.44. The course and speed shares (0.63, 0.59) fall to 0.32 and 0.16 on medians.
2. **The headline control is not the one the registered choice rule prefers (critical).** By the
   pooled ratio over clean and primary (FR-002), editing alone is 1.19 and editing with the
   threshold 1.17; the combined control was put forward for its share under the primary
   condition, which is what G reads. Pooled over clean and primary it closes about 12% of the log
   gap; editing alone about 14%. The two tools are not interchangeable: outside the mix editing
   closes nothing (0.012), on far ranges the threshold alone closes nothing (0.034).
3. **The clean-data cost is a tail (statistics).** 0.815 in geometric mean, 1.000 in median;
   twice as bad in 22% of engagements, twice as good in 11%; worse if unanswered rows count
   (0.79 in distribution, 0.74 far).
4. **P was a foreseeable null and does not test "prior or bearings" (critical, fidelity).** The
   ownship-only model is at 0.33 median range error and, as a prior at any weight tried, moved
   C″'s solve by at most a few per cent (median ratio 1.00). User story 2 promised a control
   tight enough to move the solve; it was not delivered. The share is 0 to 3% in distribution
   (nil for the typical engagement) and 6 to 14% on the other splits. What the data do say about
   a prior: against the solve told the true manoeuvre times the regressor wins where the bound is
   loose and loses where it is tight (range, in distribution: tight third 0.77 clean, 0.93
   primary; loose third 1.15, 1.34 [1.15, 1.56]; course in the tight third 0.51 and 0.71), and
   its range efficiency in the loose third is 0.98 clean, 0.61 primary, 0.35 on the shifted split
   under mismatch. An efficiency under 1 is prior or the ceiling on a relative error (the solve
   told the true times is at 0.54 to 0.89 there). "Level in range" is a loss where the bearings
   decide cancelling a win where they do not.
5. **T shows sufficiency, not cause (critical); and "behind in course and speed everywhere" was
   false (fidelity).** Knowing the true times is enough to match the regressor in range in
   distribution; it does not show the regressor gains by segmenting. Under mismatch the solve
   told the true times is not separated from the regressor in course on the shifted and far
   splits (0.99, 0.95) nor in speed on the shifted split (0.95), and not separated in range on
   far ranges (1.05). In distribution, clean, "level" in range is an average of large opposite
   differences (twice as good in 22%, twice as bad in 23%).
6. **S is the comparator moving, not the regressor (statistics, critical).** The same split
   differences taken for C″-robust ÷ the solve told the true times, and for that solve ÷
   fine-tuned:

   | split / condition | C″-robust ÷ told true times | told true times ÷ fine-tuned |
   |---|---|---|
   | shift / primary | 0.858 [0.762, 0.966] | 1.002 [0.895, 1.122] |
   | far / primary | 0.794 [0.709, 0.889] | 0.944 [0.846, 1.054] |
   | far / clean | 1.005 | 0.836 [0.745, 0.937] |
   | shift / clean | 1.184 [1.045, 1.342] | 0.892 [0.792, 1.005] |

   Under mismatch C″-robust's handicap against any good solver is smaller on these splits; the
   regressor does not lose ground to the solve told the true times. On clean data it does (far;
   borderline on busier targets), where the registered S hides it (1.055). In absolute terms the
   regressor's median range error rises 43% clean and 23% under mismatch on busier targets
   (0.068 to 0.097; 0.106 to 0.130) while C″-robust rises 55% clean and not at all under
   mismatch (0.104 to 0.161; 0.264, 0.264): user story 3 assumed C″ would not move, and it did.
   S is not matched for how tight the bound is (median range bound 0.061 in distribution, 0.110
   shifted, 0.114 far); standardised on pooled bound quintiles it is 0.743 and 0.699 (far, clean
   and primary) and 0.962 and 0.807 (shifted). Clean and primary are the same engagements, so
   four readings are two samples. With seven lines, shifted/primary "shrinks" holds at the
   nominal 95% only (Bonferroni upper limit 1.012); the far readings, G and both P survive.
7. **The far split's caveat was wrong in its basis (critical).** No training stream drew initial
   ranges of 20 to 30 km (`held-course-ranges.json` is 2 to 20 km, as MAN2). What is true: 46% of
   in-distribution scored rows are already beyond 20 km (77% on the far split; median 30 km
   against 19 km). The shifted split is mostly a re-weighting inside the training support (same
   300 s minimum leg; only turns of 15 to 30° lie outside).
8. **The structure slice cannot test spec 037's finding (fidelity, statistics).** Where C″'s
   declared transitions match the truth at the first scored row, C″-robust is still 1.50
   [1.30, 1.72] × the solve told the true times on the later rows (clean), and that solve ÷
   fine-tuned is 0.99 there: the regressor's lead in the slice is the told-truth solve's lead.
   Right against wrong is never separated (1.48 [1.30, 1.69] against 1.65 [1.46, 1.88]); under
   mismatch the right class is 59 engagements (2.25 [1.66, 3.07]). A classification by error
   (C″-robust within 1.5 × the told-truth solve at the first row) behaves the same (1.97 against
   2.44). The match is not one to one and ignores a change's kind. Spec 037's finding is neither
   reproduced nor refuted.

## Smaller findings (taken in)

- "Over 15 min since the last change" includes rows with no target change yet.
- First bearing an outlier: 14 engagements, 2.80 [1.93, 4.14] against 2.26; not separated.
- Weight digests are in the plans and checked in the job, not in the scored record; the runs
  used three CPU families (shift/clean on another than shift/primary; all comparisons are within
  one job except the split differences, which difference within-job ratios).
- `gd_tables.py` prints labels the registration does not define ("grows"; "holds" taking
  precedence; a share "not defined"); none touches a registered reading.
- "At the IMM's level" compares the ownship-only model on all rows with the IMM on the 69 to 83%
  it answers.
- Forecasts for P, T, S-far and G restate run B at a size where the outcome was near certain;
  the clean-cost forecast (0.92) ignored run A's 0.82.
- The stop rule was read as written but could not be decided: 0.453 [0.347, 0.561] on run B and
  0.439 [0.347, 0.526] on test both straddle one half. Thresholds 6 and 8 were not run with the
  edit.
- Not delivered and now listed: a prior control that moves the solve; the ownship-only model by
  range third; the hybrid with the fine-tuned prior in the README (1.57 clean, 2.19 primary:
  level with the regressor); a check of the cache against recomputation on a real shard.

## What the panel says may be written

- Classical hardening of this kind closes part of the gap under bearing errors (0.44 of the mean
  log gap in distribution, about a quarter for the typical engagement, 0.26 to 0.44 by split) at
  a clean-data cost; it describes this small family, not classical segmentation.
- The marginal prior given the ownship track is worth nothing in C″'s solve; a prior used with
  the bearings was not tested, and the regressor's lead over a solve told the true manoeuvre
  times lies where the bound is loose.
- Knowing the true manoeuvre times is sufficient to match the regressor in range in distribution
  and to beat it in course and speed there and on every clean split. The source of the
  regressor's gain is not established.
- Not: "not the prior", "it is segmentation", "classical methods cannot".

## Recommended order (the owner's choice)

1. A causal classical MAP control given the generator's manoeuvre, speed and range priors (CPU,
   spent seeds first), read by thirds of the bound: the test P was meant to be.
2. A better real-time segmenter registered against the solve told the true times (1.4 to 2.0 of
   headroom over the hardened control).
3. Only after 1, any further use of the regressor. Nothing is carried; no GPU run.
