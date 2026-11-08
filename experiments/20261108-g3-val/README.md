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

## What the record shows

1. **The calibration can reach 95% marginal coverage; it cannot make the joint statement honest.**
   Every head covers log range, course and speed at 0.92–0.99, from 0.53–0.65 raw. But only 0.835
   of rows fall within the 4-state χ²₄ 95% point. On settled rows the head meets G3-b (0.924); on
   unsettled rows it reaches 0.572. The failures are rows where the segmentation is wrong mid-
   manoeuvre: their errors are not Gaussian around the estimate at any scale the head can learn
   from these features.
2. **The head is worse than the classical temperature on the score of record** (+1.07 in IS95 log
   range) and worse than raw E (5.95 against 4.54). It widens log range more than needed (sharpness
   4.21 against the temperature's 3.08; coverage 0.986 against 0.983) because the β-NLL, with the
   raw NEES capped at 10⁴, is dominated by the gross rows. The loss is not the score: β-NLL rewards
   covering the tail of the 4-state NEES, the interval score charges every unit of width in log
   range. The head did learn something per row (it beats its shuffled control by about 1.1 in
   IS95), but in the direction the loss asked, not the one the gate measures.
3. **Course is the binding marginal:** 0.923 for the head, 0.888 for the temperature; a third of
   course errors exceed 30°.
4. **Points unchanged** (G3-d exact on all 3,934 rows).

## Critical notes on the design (for the panel)

- The cap (10⁴) and bound (4) were chosen before training from the tuning rows; a lower cap
  trades coverage for sharpness (tuning-row temperature: cap 10³ gave course coverage 0.89). No
  re-tune is allowed after this result without a new plan and decision.
- The head trained to the epoch cap; a longer run would lower the NLL a little but cannot change
  the failure mode (finding 1).
- The interval score favours raw E over every calibration here because raw E's intervals are
  narrow and its misses are charged in log range only. This is a property of the score of record
  chosen in the decision (log range only), not evidence that raw E's uncertainty is usable (its
  coverage is 0.60).

## Files

`validation.json` (tma2-g3 output: criteria, intervals, shuffled rule), `calibration.json`,
`report.md`, `plan.json` (= `configs/score/g3-a-val.json`), `inputs.json` (every input's digest,
the calibrated files included), `run.json`. `errors.npz` stays on the results branch.
