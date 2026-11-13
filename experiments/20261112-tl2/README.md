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

| System (table regenerated from `summary.json` after the panel found hand-copied errors) | Annex B (369) | Shifted (273) | Held course (360) | Correlated (92) | Outliers (92) | Whole (60) |
| --- | --- | --- | --- | --- | --- | --- |
| One leg | 0.396 | 0.387 | 0.017 | 0.359 | 0.350 | 0.623 |
| Smoothed EKF | 0.422 | 0.383 | 0.025 | 0.447 | 0.490 | 0.526 |
| C″ read as a track | 0.078 | 0.137 | 0.017 | 0.297 | 0.180 | 0.096 |
| C″ refitted | 0.055 | 0.128 | 0.017 | 0.190 | 0.125 | 0.062 |
| Search, flat prior | 0.043 | 0.097 | 0.017 | 0.195 | 0.112 | 0.023 |
| Search, Gate T's prior | 0.038 | 0.087 | 0.035 | 0.180 | 0.104 | 0.025 |
| Search, corrected prior | 0.038 | 0.095 | 0.035 | 0.185 | 0.085 | 0.022 |
| Search, mixed prior | 0.038 | 0.098 | 0.017 | 0.185 | 0.085 | 0.022 |
| True history, with the prior (`history-map`) | 0.027 | 0.038 | 0.017 | 0.100 | 0.049 | 0.021 |
| True history, best evidence (`history-best`) | 0.027 | 0.040 | 0.017 | 0.102 | 0.048 | 0.021 |
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
   false manoeuvres rise from 0.35 to 1.42 a period. Outliers hurt C″ far more than the search
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

## Corrections after the panel (2026-11-13; `review.md`, five approve with findings)

**Verdict: decided by the panel, round 1.** The registered figures above stand as
registered. The following statements above are withdrawn or narrowed, and two defects in the
registered code are recorded.

**Defects in the registered code** (not repaired here: the code is registered; a repair is a
new registration):

- **The evidence over-credits short manoeuvres.** A manoeuvre's duration keeps version 1's
  stand-in volume (about 600 s) against a sharp prior density: 2 to 3 nats of unearned Occam
  factor for each small, short manoeuvre. Re-ranking the stored candidates with a corrected
  volume gives a held-course false rate of 0.47 to 0.57, not 0.76, and changes the first
  candidate in 56 to 84 of 400 Annex B periods. **D4's 0.76 is partly this defect**; its
  direction stands (C″ 0.02). The effect on D1 to D3 is unknown without re-running.
- **The classing counts manoeuvres cut by the period's edge**, against the spec's edge case.
  Edge-aware, D2 on scored periods is **0.57 / 0.11 / 0.33** of 147 wrong (0.61 / 0.12 / 0.27
  on periods with no cut manoeuvre), and the first candidate is right in about 0.60, not
  0.51. D3 barely moves.
- **The true-history fit drifts**: with times free, 50 of 389 fits end more than 120 s from
  the true times. "The true history's evidence" is not that for 13% of periods, and the
  composites are noisy oracles, not upper limits.

**Withdrawn or narrowed:**

- **Reading 1, "the search does most of its own work", and "the first was the outlier"**:
  withdrawn. D1 is about half: 0.43 [0.28, 0.58] as registered; 0.52 [0.41, 0.65] without
  four refits that ran away numerically; 0.39 to 0.58 by estimand; 0.47 [0.36, 0.59] over
  three seeds, whose spread is marginally consistent with noise. The refit inherits C″'s
  misses. Gate T's "mostly smoothing" is qualified to "about half", not overturned. The
  clearer split: the flat-prior search obtains 0.78 [0.67, 0.91] of the gain, so Annex B's
  manoeuvre statistics are worth about a fifth of it.
- **Reading 2, "the tuning seed's 'no difference' was noise"**: withdrawn as stated; the
  intervals (1.01 [0.84, 1.23] and 1.18 [1.07, 1.29]) overlap.
- **Reading 3, "about half the wrong histories are ambiguous"**: the share is of this
  Laplace evidence at a threshold of 3, whose own noise is of that size. On those periods
  the search is at 0.057 against 0.026 for the true-history fit, and the true history is in
  the first three candidates in 0.45.
- **Reading 4, "little left to win" and "ambiguity no identifier can remove"**: withdrawn.
  The headroom with a perfect evidence is 1.05 to 1.20 across the registered thresholds
  (1.18 [1.10, 1.28] at 1; 1.05 [1.01, 1.09] at 5), 1.17 [1.09, 1.25] with times held as
  the replacement, 1.25 [1.15, 1.36] if every wrong period is replaced; ratio of medians
  1.07 [0.96, 1.23]. Inconclusive is the fair reading: the interval admits 18%.
- **Reading 5**: held course does not belong in the list (its gap is self-inflicted and the
  mixed prior closes it). For the shifted prior, correlated errors and outliers the record
  shows gaps of 1.5 to 1.9 with the same noisy composite, and no remedy of any kind tried.
- **Reading 6, "at no cost" and the cause**: withdrawn. The mixed prior moves errors from
  false manoeuvres to missed single ones: "held course" declared on a manoeuvring target in
  7.8% of Annex B periods against 1.9%, and on periods with one true manoeuvre 19.7%
  against 6.0%. Its 3% depends on its half. The flat-prior search already gives 1% on held
  course. The cause is not only the prior's leg term: it decides periods over an hour; under
  30 minutes the false rate is still 0.46, from the Occam factor and the defect above.
- **Reading 7**: "removes the search's edge over the refit" (1.12 [0.86, 1.52] on 92
  periods) is an absence of evidence.
- **Reading 10**: the smoothed EKF's figure partly reflects rows with no state (8%) and
  stretches smoothed apart; its recursion is right.
- **Forecasts**: D4 is "yes, except the mixed prior" (forecast 0.10, result 0.03
  [0.02, 0.05]); D2's ambiguous share excludes its forecast. The forecasts were written
  from a tuning run at an earlier commit than the registered code.
- **The systems table** had a wrong flat-prior row and small slips; it is regenerated from
  `summary.json` above.
- **"What this record supports"**, restated: a whole-period search halves C″'s track error
  on Annex B data, and about half of that gain is available without a search; with this
  evidence, as defective as recorded, the search's gap to a fit told the history's structure
  is 5% to 25% depending on convention; this evidence invents small manoeuvres on quiet
  targets, in part through a recorded defect.

**D5, for the owner.** The registered rule gives "no GPU budget", and it was applied as
written. What the evidence says is narrower: where targets behave exactly as the simulator's
statistics say and errors are independent, the search is within roughly 5% to 25% of a fit
told the history, on the 10% line and not below it; a learned model trained on Annex B to
identify histories is not supported. Where the prior or the error model is wrong the gap is
50% to 90% and nothing, classical or learned, has been tried against it. The study is silent
on a model that hedges across histories instead of identifying one.

**Also not run**, beyond the list above: a sampler in place of the Laplace approximation; a
Huber cost in the search; FR-002's effect on candidate calibration.
