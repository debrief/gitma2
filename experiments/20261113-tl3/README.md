# Spec 015: the re-registered study on test seed 337 (2026-11-13)

CI run 43404500552 (`timelate/tl-d-test`, commit 30cc410, clean tree), scored once. Plan and
time-late code digests equal `experiments/20261113-tl3-decision/decision.json`. **Every
table is in `tables.md`, generated from `summary.json` by `scripts/research/tl3_tables.py`;
every figure below is copied from it and checked against it by script.** Files: `summary.json`,
`tables.md`, `score.txt`, `*.periods.json`, `plan.json`, `run.json`, `ci.json`. The per-row
errors (15 MB) are on the results branch `results/timelate-tl-d-test-43404500552` under
`experiments/timelate-runs/`.

"Paired" is the geometric mean of the per-period ratio with a 95% period bootstrap.

## What was decided

| | Quantity (Annex B, 400 periods, 364 scored, unless said) | Forecast | Result | Forecast right? |
| --- | --- | --- | --- | --- |
| D1 | Share of the repaired search's gain over C″ obtained by refitting C″'s own manoeuvre times | 0.50; interval includes 0.5 | **0.33 [0.20, 0.45]** | No |
| D2 | First candidate right (edge-aware) | 0.63 | **0.64 [0.59, 0.69]** | Yes |
| D2 | Wrong scored periods (131): ambiguous / search failure / evidence failure | 0.50 / 0.12 / 0.38 | **0.44 [0.36, 0.53] / 0.13 [0.08, 0.20] / 0.43 [0.35, 0.51]** | Yes, within the intervals |
| D3 | Headroom, a perfect search under the same evidence | 1.05 to 1.08; inconclusive or not material | **1.06 [1.01, 1.11]: inconclusive** | Yes |
| D3 | Headroom, a perfect evidence as well | 1.12 to 1.20; an even chance of material | **1.17 [1.10, 1.25]: inconclusive** (the lower limit is 1.099) | Yes |
| D4 | Held-course periods with a manoeuvre declared (398): repaired search | 0.50 (0.44 to 0.56) | **0.53 [0.48, 0.58]** | Yes |
| D4 | ... C″ / flat prior / mixed prior | 0.02 / 0.01 / 0.01 | **0.02 [0.01, 0.03] / 0.01 [0.00, 0.02] / 0.00 [0.00, 0.01]** | Yes |
| D5 | Recommendation on a learned whole-period model | spec 014's rule | **By the rule: no GPU budget. See below.** | – |

Soundness on this seed, as validation read it: the reference with times held at 1.00 of the
bound on tight rows; every true-history fit with a consistent cost; 0.133 of references held.

## D5: the rule's output, and what the evidence supports

**The rule's output.** A learned whole-period model is pursued only if the headroom with a
perfect evidence is material on the Annex B test split: an interval wholly above 1.10. It is
1.17 [1.10, 1.25], and the lower limit, to three places, is 1.099. Inconclusive, which the
rule counts with "not material": **no GPU budget**. The verdict is not a bootstrap accident:
with 50,000 resamples the limit is 1.0975, and it is below 1.10 for 19 of 20 bootstrap seeds
(computed after the run from the per-period errors; not part of the registered scoring).

**What the evidence supports.** The headroom misses the line by two thousandths. At the
other registered sensitivities (`tables.md`, "attainable headroom") it is material at class
threshold 1 (1.30 [1.20, 1.42]) and at a 60-second match (1.20 [1.12, 1.29]), and
inconclusive at threshold 5 (1.10 [1.05, 1.17]) and without held references
(1.13 [1.06, 1.20]). On validation seed 336 it was material (1.30 [1.15, 1.49]). A fair
statement: **on Annex B data a better identifier of histories has between 10% and 30% to
win, most likely about 17%; the registered rule says that is not enough, by the narrowest
margin a rule can.** The decision the rule was written to make automatically is, on this
evidence, a judgement, and it is the owner's.

**Where the assumptions are wrong** the same statistic is material on every split: shifted
prior 1.71 [1.50, 1.96]; correlated errors 1.44 [1.20, 1.74]; outliers 1.50 [1.30, 1.75];
held course 1.53 [1.40, 1.68] (which the mixed prior removes). No remedy, classical or
learned, was built against the first three.

**What the study is silent on.** A model that hedges across histories instead of naming
one; anything outside this simulator.

## Systems

See `tables.md`, "Systems". On Annex B data C″ read as a track is at 0.083, C″ refitted
0.066, the flat-prior search 0.049, the repaired search 0.039 and the true-history fit
0.028. Paired on Annex B:

| Comparison | Paired | First better in | Over twice as bad: first / second |
| --- | --- | --- | --- |
| C″ ÷ repaired search | 2.10 [1.82, 2.44] | 0.31 | 0.44 / 0.12 |
| C″ refitted ÷ repaired search | 1.65 [1.45, 1.87] | 0.39 | 0.29 / 0.07 |
| Flat-prior search ÷ repaired search | 1.22 [1.10, 1.34] | 0.37 | 0.19 / 0.10 |
| Spec 014's search ÷ repaired search | 1.07 [0.98, 1.16] | 0.20 | 0.10 / 0.06 |
| Repaired search ÷ mixed-prior search | 0.98 [0.96, 1.01] | 0.03 | 0.01 / 0.02 |

## What the repairs changed (spec 014's search beside the repaired one, same periods)

| | Spec 014's evidence | Repaired |
| --- | --- | --- |
| Held course: periods with a manoeuvre declared | 0.80 [0.76, 0.84] | 0.53 [0.48, 0.58] |
| ... under 30 min (86) / 30 to 45 (99) / 45 to 60 (88) / 60 to 90 (94) / over 90 (31) | 0.50 / 0.78 / 0.91 / 0.95 / 1.00 | 0.09 / 0.32 / 0.68 / 0.86 / 1.00 |
| Held course: spec 014's ÷ repaired, paired | – | 1.22 [1.12, 1.34] |
| Annex B: false manoeuvres (716 true) | 135 | 89 |
| Annex B: true manoeuvres missed | 0.20 | 0.22 |
| Annex B: first candidate right; calibration gap | 0.598; −0.071 | 0.652; −0.038 |
| Annex B: one-manoeuvre targets declared quiet (122) | 0.041 | 0.131 |

## Reading

1. **The repair removes the evidence's false manoeuvres on short periods and not the
   prior's on long ones.** Under 30 minutes the held-course rate falls from 0.50 to 0.09;
   over 90 minutes it is 1.00 either way. Overall it is still 0.53, and the repaired
   search's track on held course is still 1.80 [1.60, 2.02] times the one-leg fit's.
2. **The repair is not free.** The repaired search calls a target with one manoeuvre quiet
   in 0.131 of such periods, where spec 014's did in 0.041. It trades false manoeuvres for
   missed single ones, as the mixed prior does more strongly (0.197). C″ does in 0.238.
3. **On Annex B data the repair changes the track little** (1.07 [0.98, 1.16]) and improves
   which history comes first (0.652 against 0.598).
4. **D1: about a third of the search's gain comes without a search**, 0.33 [0.20, 0.45], and
   the interval excludes a half. Spec 014 had 0.43 [0.28, 0.58] on seed 335; development on
   that seed gave 0.47 and validation 0.64 [0.36, 1.01]. By the other declared estimands:
   0.37 [0.23, 0.50] where no period median exceeds 1, and 0.31 as a ratio of log medians.
   The fall-back fired in 5 of 400 periods; 7 refits still have a period median of 1 or
   more. The flat-prior search obtains 0.74 [0.61, 0.86]: Annex B's statistics are worth
   about a quarter of the gain. The share is not a constant: five readings on four seeds run
   from 0.33 to 0.64.
5. **D2 no longer depends on the period's edges.** Without periods that have a cut
   manoeuvre (301 scored) the first candidate is right in 0.62 and the wrong histories divide
   0.46 / 0.14 / 0.40. 72 of 400 periods have a cut manoeuvre.
6. **The search itself is rarely the fault** (0.13 of wrong histories); the evidence prefers
   a wrong history about as often as it cannot separate them.
7. **The mixed prior** removes false manoeuvres on held course (0.00 [0.00, 0.01]) at no
   cost in median track error on Annex B data (0.98 [0.96, 1.01]) and at the cost in item 2.
8. **Correlated errors** triple the repaired search's false manoeuvres (1.29 a period
   against 0.22) and leave its candidate probabilities meaningless (calibration gap 0.332).
   **Outliers** raise them to 0.67 a period. Under the shifted prior the first candidate is
   right in 0.23 of periods and 0.77 of wrong histories are evidence failures.

## Forecasts

Seven of eight decided forecasts held; D1's did not (0.50 forecast, 0.33 found, the interval
excluding a half). Of the reported ones: "spec 014's ÷ repaired 1.03 on Annex B" close
(1.07 [0.98, 1.16]); "1.15 to 1.20 on held course" slightly low (1.22); "fall-backs under 5%
of periods" right on Annex B, held course and the shifted split, wrong with outliers (20 of
100) and correlated errors (10 of 100); "the mixed prior calls a one-manoeuvre target quiet
in about 0.2 against 0.1" right (0.197 against 0.131); "headroom material under the shifted
prior and both error conditions" right. "Above 0.90 over an hour" for the held-course rate
is missed narrowly: 0.86 from 60 to 90 minutes and 1.00 beyond.

## Not run, weaknesses, and what this does not support

- No remedy for the shifted prior, correlated errors or outliers; no hedged track; no
  sampler in place of the Laplace approximation; no thinning. They are the next choice.
- The fall-back rule fires in a fifth of outlier periods: there the "cost the noise
  explains" test fails by construction (the outliers are not in the stated noise), as the
  consistent-cost share of 0.020 on that split shows.
- 0.133 of references were held to the true times on Annex B data, 0.300 under the shifted
  prior and 0.280 with correlated errors: there the composite is mostly a times-held fit.
- The held-course split is not wholly quiet: 2 of its 400 periods contain a manoeuvre (the
  first change is drawn uniformly over a very long leg). D4 is over the 398 without.
- The class threshold is a convention, and the headroom's verdict turns on it (see D5).
- One test seed; every split is drawn from the same seed with different ranges files; the
  fitting model is the simulator's own; bearing errors are independent Gaussian in the
  primary condition.
- This record does not show that learning cannot help, nor that it would.
