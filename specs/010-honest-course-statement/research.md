# Research: an honest course statement (spec 010)

All evidence comes from validation seed 314 **tuning ordinals 0–499**:
- 1,971 G5 rows, of which 1,951 have a usable covariance;
- spec 008's feature cache `results/g2predict-g3-feat-val-42472096319`;
- C's tuning segmentation `results/segment-c3-val-tune-42268374366` (same C, digest `60e6ee63…`).

Fits marked "held out" are fitted on ordinals 0–249 and tested on 250–499, and vice versa. Nothing
here touches scoring ordinals 500–1499. Scripts: `scripts/research/g5_tuning.py` (T002).

## R1. Can the unsettled rows be recognised causally?

- **Truth.** 26.8% of tuning rows are not settled: a target manoeuvre is in progress, or one ended
  less than 5 min before. E's course is within 30° on 0.75 of settled rows and on 0.39 of
  unsettled rows.
- **C's segmentation barely sees them.** As a score for truth-unsettled:
  - C has a transition open at the row: AUC 0.550;
  - minutes since C's last closed transition: 0.499;
  - no transition yet: 0.510;
  - E's course sd: 0.532.

  C confirms transitions late, so at the row a recent manoeuvre is usually not yet in its
  segmentation.
- **Recent bearing residuals see a little more.** The bearings in the last W rows are compared
  with E's own state propagated back at constant velocity.
  - The |mean residual| ·√n over the last 6 rows (1 min) gives AUC 0.625, and over 30 rows 0.624.
  - The mean squared residual over 60 rows gives 0.615.
- **Combined.** A logistic model on the residual statistics (6, 12, 30 rows), the 60-row χ², C's
  open flag, E's three log sds and the minute reaches a held-out AUC of **0.643 / 0.659** for
  truth-unsettled. For a course miss over 30° it reaches 0.689 / 0.588.
- **Decision.** The unsettled proxy is this logistic score, fitted on tuning rows. It flags the
  rows above the quantile that matches the tuning base rate (about 27%).
  - The gate's per-slice reliability check uses the proxy's two states, which are causal. The truth
    split is reported alongside.
  - The proxy's features are also inputs to the statement, so P can drop where they suggest a
    manoeuvre.
- **Consequence, stated up front.** With AUC about 0.65, no causal statement can bring the
  truth-unsettled rows' reliability (−0.31 in Gate 4) close to zero. What can be asked is honesty
  per proxy state.
- **Alternatives.**
  - A threshold on C's open flag alone: AUC 0.55, so it flags too few unsettled rows to matter.
  - A GLR change statistic on the recent residuals: similar information to the residual bias. Not
    pursued.

## R2. The course statement must be consistent by construction

- **The normal approximation is unusable.** With the Gate 4 mixture and the sd^β temperature, the
  normal approximation to the von Mises mass on ±X differs from the exact mass by 0.036–0.045 on
  average, and by up to **0.51–0.55** on broad rows: κ is small there, and the arc cap limits X but
  not a·sd. The panel's 0.12 was measured on the head's rows. On the temperature's rows it is far
  worse.
- **With exact mass, the mixture is mis-shaped.** The lowest fifth of P (0.33–0.38) hits 0.64–0.65.
  A broad von Mises puts too little mass near the estimate for these rows. Recalibrating the
  mixture weight p (a Platt map on logit p fitted by log score) leaves it unchanged (slope 1.00),
  because the log-score fit already makes p optimal for the wrong shape.
- **Decision: the truncated construction.** The row states the arc X, the probability P, and a
  concentration κ for the shape inside the arc. The course density is:
  - **inside ±X:** P times a von Mises with concentration κ, truncated to ±X and renormalised;
  - **outside ±X:** (1 − P) spread uniformly over the rest of the circle.

  The mass on the arc is P exactly, by construction, for any P. The log score of this density at
  the true course is proper. It splits into the Bernoulli log score of P, plus the log density of
  the shape given a hit, plus the uniform term given a miss. So recalibrating P keeps the statement
  consistent, and P is trained by binary log loss.
- **Alternatives.**
  - The Gate 4 mixture with exact mass: inconsistent once P is recalibrated, and mis-shaped.
  - A wrapped Student-t: no closed-form arc mass.

## R3. Recalibration and resolution

- **Under the temperature, P has almost no resolution.** The arc scales with E's sd, so the hit rate
  is nearly flat (0.57–0.65 across fifths of P). A Platt map on logit P, fitted held out, has
  slopes 0.09 and −0.19 and makes P nearly constant at 0.6. That is honest, but it says nothing
  per row.
- **Decision.**
  - P is a logistic function of causal features: E's three log sds, the R1 proxy features and the
    minute. The classical control fits a few parameters of it on the stream; the head learns a
    nonlinear function of the same features plus E-w's encoder state.
  - A final two-parameter Platt map on logit P is fitted on tuning rows. It replaces the 10-knot
    isotonic map, which capped P by noise in Gate 4.
- **Expectation.** With features of AUC about 0.65, P can spread to roughly 0.35–0.8 while staying
  honest. Whether the head adds resolution beyond the classical logistic is G5-d's question.

## R4. A reciprocal-course mode

- **Finding.** 2.7% of E's course errors exceed 150°, and 7.0% lie between 90° and 150°.
- **Decision.** No reciprocal mode. It could move at most 2.7% of rows, and the uniform remainder
  already covers them.

## R5. Early rows (before minute 5)

- **Decision.** Not added. The feature caches hold G5 rows only, so adding earlier rows needs new E
  prediction runs over the validation and stream data at extra k. That stays out of this spec's
  scope.
- The minute-5 slice is gated. The gap is stated in the record and carried as a follow-on
  (FR-012).

## R6. Classical controls (registered before any result)

1. **The sd^β temperature, restated in the truncated form.** Per cell (G5 minute × open at k): X
   scale, κ, P, c_range, c_speed, with β per quantity from the grid. This is Gate 4's control,
   carried.
2. **The classical rule:**
   - logit P is a quadratic in E's three log sds plus a linear term in the R1 proxy features and
     the minute;
   - log X-scale, log κ, log c_range and log c_speed are quadratics in the three log sds.

   It is fitted on the training stream (seed 318, the head's rows) by the same loss. It extends the
   Gate 4 red team's 43-parameter rule with the proxy features, so the head is compared with the
   best classical use of the same causal inputs except the encoder state.
3. **The encoder-only shuffle.** The head is retrained with E-w's encoder state permuted across
   rows each epoch, keeping the sds, the proxy features, C's code and the errors. It is scored at
   best and last epoch as `st-encshuf-best` and `st-encshuf-last`.
4. **References.** The oracle and the frozen IMM each get the temperature fitted to their own
   errors on tuning rows. The IMM's rows without an estimate are reported apart.

## R7. The gate (proposed defaults; the owner merges the amendment)

- **G5-a (intervals):** range and speed coverage. Overall, the interval must lie wholly within
  [0.92, 0.98]. Per gated slice, it must not lie wholly outside [0.90, 0.99].
- **G5-b (reliability):**
  - overall hit − P wholly within ±0.04 (revised from ±0.03 by the synthetic check below);
  - the calibration slope (logistic regression of the hit on logit P), with an interval wholly
    within [0.75, 1.33];
  - per gated slice, hit − P not wholly outside ±0.05. The point band of ±0.08 was dropped
    after the synthetic check below.

  The gated slices are G5 minute (4), open at k (2), range band (6) and proxy state (2). A slice
  with fewer than 150 rows is reported, not gated.
- **G5-c (usefulness):** the course log score's gain over "unknown" wholly above 0, and the AUC of P
  for a hit wholly above 0.55.
- **G5-d (learning):** the head's standardised summed score minus the better classical control's
  (the lower of 1 and 2), wholly below 0. The claim is void if `st-encshuf-best` or
  `st-encshuf-last` also beats that control on validation.
- **G5-e (consistency):** every row's P equals its density's arc mass to within 1e-6, and the
  points are identical.
- **Synthetic check (SC-003).** Before the decision record, the verdict logic is run on resampled
  synthetic statements (`scripts/research/g5_synthetic.py`). A calibrated statement must pass G5-b
  in at least 90% of datasets, and one miscalibrated by 0.15 on one slice must fail it in at least
  90%. Bands that fail this check are revised before the amendment, not after.
  - **First proposal** (overall ±0.03, per-slice point band ±0.08), 10 datasets: G5-b on the
    calibrated statement passed 60%, was inconclusive 30% and failed 10%. Two components caused it:
    - the overall interval is about ±0.019 wide, so it falls wholly within ±0.03 only when the
      point is within ±0.011;
    - slices of about 200 rows have a clustered sd near 0.035, so the ±0.08 point band failed them
      on noise.
  - **Revision:** overall ±0.04, and an interval-only check per slice. The slice verdict is pass
    unless the interval lies wholly outside ±0.05. Result over 60 datasets: the calibrated statement
    never failed G5-b (75% pass, 25% inconclusive, before the interval-only change), and the
    0.15-off slice failed in 100%. The final run (100 datasets, 500 resamples) is recorded in the
    decision record.

## R8. Sample sizes

- Validation scoring rows: 3,934 (1,000 scenarios).
- **Smallest gated slices:** open at k is about 8% (about 300 rows) and the 30+ km band is about 670
  rows. A per-slice clustered sd of hit − P is about 0.03 at 300 rows, so ±0.05 "not wholly
  outside" fails only a slice that is truly off by more than about 0.11. That is deliberate: it
  catches Gate 4's −0.31 failure mode without failing on noise.
