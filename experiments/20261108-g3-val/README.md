# Gate 3 validation (spec 008 T026): the validation rule is not met

The carried calibration does not go to test; seed 320 is not generated (decision record
`experiments/20261108-g3-decision/`, validation rule). Validation seed 314, scoring ordinals
500–1499 (1,000 scenarios, 3,934 σ = 1° G5 rows). Scoring run 42497421159
(`results/score-g3-a-val-42497421159`, commit 5fafbd3, Intel Xeon 6973P-C), the reference
estimators reused from the baseline scoring (`--reuse`, rows matched exactly). Calibrated files
`results/g3predict-g3-a-val` (tma2-g3predict from the training run
`results/g3-g3-a-42493381448`). Verdict file `validation.json` (tma2-g3 --split validation).

## Carried head

The carried rule takes the median validation interval score in log range among the seeds: s1
5.76, s2 6.00, s3 5.95, so **cal-s3**. All three seeds trained 50 epochs (the cap; s1 and s3
were still improving slowly: validation NLL 787 untrained, 12.56 to 12.82 at the end); the
shuffled control stopped at 41 (best 36), NLL 13.16.

## Overall

| Estimator | Cov95 log range | Cov95 course | Cov95 speed | Within χ²₄ 95% | Median NEES ratio | IS95 log range | Sharpness log range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E raw | 0.598 | 0.532 | 0.647 | 0.330 | 6.65 | 4.54 | 0.27 |
| Temperature (control) | 0.983 | 0.888 | 0.979 | 0.793 | 0.16 | 4.88 | 3.08 |
| Head s1 | 0.988 | 0.925 | 0.985 | 0.836 | 0.16 | 5.76 | 4.09 |
| Head s2 | 0.988 | 0.920 | 0.984 | 0.836 | 0.14 | 6.00 | 4.25 |
| Head s3 (carried) | 0.986 | 0.923 | 0.984 | 0.835 | 0.15 | 5.95 | 4.21 |
| Shuffled, best | 0.988 | 0.921 | 0.985 | 0.835 | 0.08 | 7.03 | 4.71 |
| Shuffled, last | 0.988 | 0.923 | 0.986 | 0.837 | 0.09 | 7.26 | 4.86 |

## Criteria (carried head cal-s3)

| Check | Value [97.5% interval] | Band | Outcome |
| --- | --- | --- | --- |
| G3-a log range | 0.986 [0.980, 0.991] | [0.92, 0.98] | inconclusive (point above) |
| G3-a course | 0.923 [0.911, 0.934] | [0.92, 0.98] | inconclusive |
| G3-a speed | 0.984 [0.977, 0.989] | [0.92, 0.98] | inconclusive (point above) |
| G3-b within χ²₄ 95% | 0.835 [0.819, 0.849] | [0.92, 0.98] | **fail** |
| G3-c head − temperature, IS95 log range | +1.07 [+0.98, +1.17] | below 0 | **fail** |
| G3-d points identical | exact | — | pass |
| Shuffled rule | best +2.15 [+1.99, +2.34], last +2.37 [+2.20, +2.59] over the temperature | not wholly below 0 | pass (the rule would not void) |

The validation rule needs every point within its band: log range (0.986) and speed (0.984) are
above 0.98, G3-b and G3-c fail. **Not carried; seed 320 not generated.**

## By slice (carried head and temperature)

| Slice | Head cov95 log range | Head cov95 course | Head within 95% | Head IS95 lr | Temp cov95 course | Temp within 95% | Temp IS95 lr |
| --- | --- | --- | --- | --- | --- | --- | --- |
| g5_minutes=5 | 0.975 | 0.896 | 0.765 | 6.71 | 0.876 | 0.747 | 6.32 |
| g5_minutes=10 | 0.991 | 0.929 | 0.861 | 5.15 | 0.886 | 0.795 | 3.44 |
| g5_minutes=15 | 0.991 | 0.925 | 0.848 | 5.69 | 0.883 | 0.809 | 4.18 |
| g5_minutes=20 | 0.988 | 0.942 | 0.866 | 6.27 | 0.909 | 0.822 | 5.61 |
| open_at_k=open | 0.957 | 0.967 | 0.890 | 7.74 | 0.852 | 0.843 | 6.48 |
| open_at_k=not_open | 0.988 | 0.920 | 0.831 | 5.87 | 0.890 | 0.790 | 4.80 |
| range_band=0-2km | 0.942 | 0.981 | 0.923 | 5.60 | 0.923 | 0.923 | 4.48 |
| range_band=10-20km | 0.989 | 0.935 | 0.845 | 5.61 | 0.898 | 0.799 | 4.62 |
| range_band=2-5km | 0.986 | 0.907 | 0.856 | 4.63 | 0.884 | 0.847 | 3.79 |
| range_band=20-30km | 0.990 | 0.911 | 0.836 | 6.20 | 0.883 | 0.782 | 5.04 |
| range_band=30+km | 0.976 | 0.907 | 0.781 | 7.52 | 0.866 | 0.743 | 6.08 |
| range_band=5-10km | 0.989 | 0.930 | 0.851 | 5.20 | 0.897 | 0.818 | 4.37 |
| settled=settled | 0.988 | 0.959 | 0.924 | 6.06 | 0.940 | 0.896 | 4.94 |
| settled=not_settled | 0.980 | 0.815 | 0.572 | 5.62 | 0.737 | 0.490 | 4.72 |

## What the record shows (amended after panel round 1, `review.md`)

1. **Marginal coverage is reached largely by giving up on course.** Every calibration covers log
   range and speed at 0.98–0.99 (from 0.60 and 0.65 raw), above the 0.95 target. Course is 0.92 for
   the heads, but for 53% of the carried head's rows (42% of the temperature's) the 95% course
   interval covers the whole circle (median stated course sd 101°, raw 5.5°); on the remaining rows
   course coverage is 0.857 (head) and 0.826 (temperature). Course binds because it is the least
   observable state on short or low-bearing-rate legs and just after a zig.
2. **G3-b fails mainly because the stated correlations are kept.** The local covariance's
   correlations are near-singular (median |ρ| 0.81 log range–speed, 0.77 speed–course; 15% of rows
   have some |ρ| > 0.99). The registered form rescales the standard deviations and keeps those
   correlations, so errors off the stated near-singular directions fall outside the χ²₄ 95% point.
   With the same scales and the correlations dropped, the share within it would be 0.957 (head)
   and 0.937 (temperature) (numerics reviewer, on the cache). The registered family cannot reach
   G3-b. Unsettled rows are worst (0.572 against 0.924 settled), but that slice is defined from the
   truth (a manoeuvre in progress or within 300 s): the oracle, with the true segmentation, also
   fails there (0.635). Much of it is manoeuvre lag (the bearings have not yet determined the new
   leg), only part E's segmentation.
3. **The head is not better than the temperature, and little per-row learning is shown.** On the
   score of record (IS95 log range) the head is worse (+1.07). The miss penalty is about zero for
   both; the head's intervals are wider on 93% of rows (width ratio quartiles 1.16, 1.32, 1.59).
   The head is nearly a constant (log-range s between 2.36 and 2.94 for 90% of rows). With each
   estimator's log-range sd moved by its best single global factor (fitted in sample on these
   scoring rows, a diagnostic only), IS95 is 2.264 (head), 2.271 (shuffled) and 2.335
   (temperature); the shuffled head also beats the temperature on the NLL. So
   the head's apparent gain over its shuffled control (1.1 in IS95) is a level, not
   discrimination (AUC for the rows with the largest raw errors: 0.60 head, 0.56 shuffled, 0.53
   temperature).
4. **Why the head is wider than the temperature:** the loss is the joint 4-state NLL, so log range
   is inflated everywhere to absorb tails that course drives; and training used the linearised
   local error (u = T e) while the score uses exact errors. A course flip has a small linearised
   course error (on rows with course error over 90°: median 47° linearised, 123° exact), so the
   head under-widens course and over-widens log range (log-range coverage 0.987 linearised, 0.996
   exact). The β-weight up-weights the rows the head widens (the R6 text said the opposite); its
   effect is at most 1.1× and immaterial.
5. **Points unchanged** (G3-d exact on all 3,934 rows).

## Process notes

- **Data used before the decision.** The local form and bound 4 were chosen from E's validation
  *scoring* rows (ordinals 500–1499, the baseline, `research.md` R5 as amended), the cap from an
  in-sample temperature on the tuning rows (0–499); both before the decision record and before
  any training. The bias runs toward passing; the gate failed, so the outcome is unaffected. A
  later gate should choose such settings on tuning rows only.
- **The score of record charges log range only;** raw E's intervals are about 12× narrower than
  the calibrations', so its miss penalty (it covers 0.60) costs less than their widths. IS95 log
  range alone is not a measure of usable uncertainty.
- **Missing rows** (39 per estimator, 1%) are not covered, outside χ²₄, and charged the
  estimator's own 99th-percentile interval score.
- **Inputs.** The feature cache and the prediction file come from different g2predict runs of the
  same E (segmentation digests 38cdafc… and 8df52ac…); their rows agree to 1e-6 (5 runaway rows
  apart). The calibrated files' headers keep E's commit; the g3predict commit (d9962b7) is in
  `results/g3predict-g3-a-val`'s `run.json`; the files rebuild byte for byte there.
- The cap (10⁴) and bound (4) are not re-tuned after this result; any change is a new plan.

## Files

`validation.json` (tma2-g3 output: criteria, intervals, shuffled rule), `calibration.json`,
`report.md`, `plan.json` (= `configs/score/g3-a-val.json`), `inputs.json` (every input's digest,
the calibrated files included), `run.json`. `errors.npz` stays on the results branch.
