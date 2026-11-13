# Spec 014: the registered study on test seed 335 (2026-11-13)

CI run 43313825135 (`timelate/tl-c-test`, commit 78f423f, clean tree), scored once. Plan and
time-late code digests equal `experiments/20261112-tl2-decision/decision.json`. Files here:
`summary.json`, `score.txt`, `*.periods.json`, `plan.json`, `run.json`, `ci.json`. The per-row
errors (`*.errors.npz`, 16 MB) stay on the results branch
`results/timelate-tl-c-test-43313825135` under `experiments/timelate-runs/`.

Median period range error unless said; intervals are 95% period bootstraps; "paired" is the
geometric mean of the per-period ratio.

## What was decided

| | Quantity (Annex B, 400 periods, 369 scored, unless said) | Forecast | Result | Forecast right? |
| --- | --- | --- | --- | --- |
| D1 | Share of the search's gain over C″ obtained by refitting C″'s own manoeuvre times | 0.75; interval includes 0.6, excludes 0.3 | **0.43 [0.28, 0.58]** | No |
| D2 | Wrong-history periods (195): ambiguous / search failure / evidence failure | 0.45 / 0.10 / 0.45 | **0.53 [0.46, 0.60] / 0.08 [0.05, 0.13] / 0.39 [0.32, 0.46]** | Roughly |
| D3 | Attainable headroom, a perfect search under the same evidence | inconclusive | **1.04 [1.01, 1.08]: not material** | No |
| D3 | Attainable headroom, a perfect evidence as well | material | **1.10 [1.04, 1.18]: inconclusive** | No |
| D4 | False-manoeuvre rate, 400 held-course periods: search / C″ / flat prior / mixed prior | 0.80 / 0.03 / 0.02 / 0.10 | **0.76 [0.71, 0.80] / 0.02 [0.01, 0.04] / 0.01 [0.00, 0.03] / 0.03 [0.02, 0.05]** | Yes |
| D5 | Recommendation on a learned whole-period model | by the rule | **Do not spend GPU budget on it** | – |

**D5 by the registered rule**: a learned whole-period model is pursued only if the headroom
with a perfect evidence is material on the Annex B test split. It is 1.10 [1.04, 1.18]:
inconclusive against 1.10, which the rule counts with "not material". No GPU budget is spent.

Soundness on this seed, as validation read it: the reference with times held at 1.09 of the
bound on tight rows; 99.8% of true-history fits with a consistent cost.

## Systems

| System | Annex B (369) | Shifted (273) | Held course (360) | Correlated (92) | Outliers (92) | Whole (60) |
| --- | --- | --- | --- | --- | --- | --- |
| One leg | 0.396 | 0.387 | 0.017 | 0.359 | 0.350 | 0.623 |
| Smoothed EKF | 0.422 | 0.383 | 0.025 | 0.447 | 0.490 | 0.526 |
| C″ read as a track | 0.078 | 0.137 | 0.017 | 0.297 | 0.180 | 0.096 |
| C″ refitted | 0.055 | 0.128 | 0.017 | 0.190 | 0.125 | 0.062 |
| Search, flat prior | 0.043 | 0.092 | 0.017 | 0.186 | 0.137 | 0.026 |
| Search, Gate T's prior | 0.038 | 0.086 | 0.035 | 0.180 | 0.105 | 0.025 |
| Search, corrected prior | 0.038 | 0.095 | 0.035 | 0.184 | 0.085 | 0.022 |
| Search, mixed prior | 0.039 | 0.097 | 0.017 | 0.184 | 0.085 | 0.022 |
| True history, with the prior | 0.027 | 0.039 | 0.017 | 0.100 | 0.049 | 0.021 |
| True history, times held | 0.025 | 0.041 | 0.017 | 0.073 | 0.035 | 0.016 |

Paired ratios on Annex B data:

| Comparison | Paired | First better in | Over twice as bad: first / second |
| --- | --- | --- | --- |
| C″ ÷ search | 2.13 [1.88, 2.43] | 27% | 49% / 10% |
| C″ ÷ C″ refitted | 1.39 [1.22, 1.57] | 39% | 33% / 12% |
| C″ refitted ÷ search | 1.53 [1.35, 1.76] | 36% | 25% / 8% |
| Flat-prior search ÷ search | 1.18 [1.07, 1.29] | 40% | 18% / 11% |
| Gate T's search ÷ corrected | 1.07 [1.02, 1.13] | 11% | 5% / 2% |
| Search ÷ mixed-prior search | 0.99 [0.96, 1.03] | 3% | 1% / 2% |
| Search ÷ true history with the prior | 1.37 [1.23, 1.53] | 37% | 24% / 8% |

## Reading

1. **The search does most of its own work** (D1). Refitting C″'s transitions with the arc
   model and the prior obtains 0.43 of the gain; where the search names the true history,
   0.34. The tuning seed had said 0.79 and validation 0.30; three seeds of 134, 139 and 369
   periods give 0.79, 0.30, 0.43, and the first was the outlier. The forecast was written
   from it and is wrong. Gate T's panel suspected "mostly smoothing": on this evidence the
   model, the prior and the whole period are under half, and the search the larger part.
2. **The manoeuvre statistics help on Annex B data, modestly**: the flat-prior search is
   1.18 [1.07, 1.29] worse and misses 27% of manoeuvres against 20%. The tuning seed's "no
   measurable difference" was noise. Under the shifted prior they add nothing (1.03
   [0.91, 1.16]), as they should not.
3. **About half the wrong histories are ambiguous** (D2): the true history's evidence is
   within 3 of the search's choice in 53% of wrong periods; in 39% the evidence prefers the
   wrong one; the search fails to find a clearly better true history in 8%. At thresholds 1
   and 5 see `summary.json` (`class_sensitivity`).
4. **There is little left to win by identifying histories better on Annex B data** (D3).
   A perfect search: 4% [1, 8], not material. A perfect evidence as well: 10% [4, 18], on
   the line. Gate T's "1.46" was the cost of not knowing the history; most of it is
   ambiguity no identifier can remove.
5. **The headroom is where the assumptions are wrong.** With a perfect evidence: shifted
   prior 1.53 [1.37, 1.72]; held course 1.88 [1.66, 2.12]; correlated errors 1.61
   [1.35, 1.93]; outliers 1.54 [1.27, 1.89]. All material, none decided here. These are not
   an argument for a model trained on Annex B: they measure what the wrong assumption costs.
6. **On a target that holds course the informed search is wrong three times in four** (D4),
   and its track is twice as bad as C″'s (C″ ÷ search 0.50 [0.44, 0.56]). The mixed prior
   removes this (3%) at no cost on Annex B data (0.99 [0.96, 1.03]), under the shift (1.00)
   or under either error condition (1.00). It was added after the tuning seed and before
   registration; its half is not tuned.
7. **Correlated bearing errors hurt everything**, the true-history fit included (0.027 to
   0.100), and remove the search's edge over the refit (1.12 [0.86, 1.52]). The search's
   false manoeuvres rise from 0.38 to 1.5 a period. Outliers hurt C″ far more than the search
   (C″ 0.180, search 0.085); the tuning seed's wild-bearing edit was not run here.
8. **Whole engagements favour the search most**: C″ ÷ search 4.09 [2.77, 5.72] on 60; the
   search is at the true-history fit there (0.022 against 0.021).
9. **The corrected prior is slightly better than Gate T's** on this seed (1.07 [1.02, 1.13]);
   the tuning and validation seeds showed nothing. Small either way.
10. **The smoothed EKF is no reference at all** on manoeuvring targets (0.42, worse than one
    leg) and worse than one leg on held course (0.025 against 0.017). As frozen for
    real-time rows; not re-tuned, no manoeuvre model.
11. **Counts** (120 s match, Annex B, 711 true manoeuvres): C″ misses 52% with 299 false;
    the refit 33% and 157; the search 20% and 140; the mixed prior 21% and 113. At 60 s the
    search misses 30%, at 240 s 15%. Timing error of matches: C″ 52 s, the search 16 s.
12. **Candidates** (search, temperature 3): true history first 0.51, in the first three 0.70,
    calibration gap +0.005 on Annex B data; gap +0.27 under the shift, +0.17 on held course,
    +0.34 with correlated errors.
13. **Splits** (Annex B): the search's error rises with true range (0.022, 0.040, 0.056 by
    tercile) as everyone's does; no difference by position in the period; with fewer than
    two ownship turns in the period (34 periods) every system is poor.

## Forecasts

Three of five decided forecasts were wrong (D1, both parts of D3), all in the direction the
tuning seed pointed. Of the reported ones: "flat ÷ search about 1.0 on Annex B" wrong (1.18);
"refit no better than C″ under the shift" right (1.02); "smoothed EKF worse than C″" right;
"correlated and outlying errors hurt every system and the search's counts most" right for
correlated, wrong for outliers (C″ suffers more).

## Not run, or not as specified

- The prior-mismatch diagnostic and a broadened prior (User Story 6): not built. The mixed
  prior is a different, narrower thing.
- An IMM smoother: the smoother is over the EKF.
- The wild-bearing edit from the thinning study on test data; the edit without thinning.
- Thinning in the registered runs: nothing adopted, full data throughout.
- Efficiency per split for prior-using systems is not a bound comparison
  (`bound_applies` false in `summary.json`).
- `history_converged_share` is 0.05 on the outlier split: the cost test assumes the stated
  noise, so it fails by construction there and means nothing.
- Per-row errors are not committed here (size); they are on the results branch.

## What this record supports, and what it does not

On simulated data, independent Gaussian bearing errors of 1°, a fitting model that is the
generator's own, and one test seed:

- A whole-period search over manoeuvre histories halves C″'s track error on Annex B data,
  and somewhat under half of that gain comes from the arc model, the prior and the whole
  period without any search.
- On Annex B data the search is within about 10% of what a perfect identifier of histories
  could reach; the rest of its gap to the true-history fit is ambiguity.
- A prior that says targets always manoeuvre makes the search declare manoeuvres on targets
  that do not; mixing in a quiet target fixes that at no measured cost.

It does not support: any claim about real bearings; that a learned model could not help
where the assumptions are wrong (it shows headroom there and tests nothing); that the shares
are constants (three seeds gave 0.79, 0.30, 0.43 for D1).
