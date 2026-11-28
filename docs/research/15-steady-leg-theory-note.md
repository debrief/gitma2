# Steady-leg detector: theory-first findings

Date: 28 November 2026. Scope: open questions 1, 2, 3 and 5 of the problem brief, worked on
paper and on a small stand-alone simulation. Nothing here was run against the repository.

**Status of the evidence.** The simulator is my re-implementation of section 4 of the brief
(`sim.py`), not generator 0.6.0. Ownship zigs are assumed to be 60° to 120° at 1°/s; helm
wander and bearing dropouts are not modelled. Detectability figures are expected (noise-free)
costs, not Monte Carlo detections. Treat every number as a hypothesis to re-run in the
repository, not as a result.

## Summary

1. **Most of C's misses are probably undetectable, not missed.** With manoeuvre times told and
   the whole window available, 28% of manoeuvres cost less than 25 σ² to omit. C misses about
   30%. Priority 1 of the brief (fewer misses) has little headroom at that threshold.
2. **The false-alarm problem is the noise model, and it is large.** On held-course targets a
   split statistic that is safe on white noise (95th percentile 10.6) reaches 58 under the
   correlated component alone and 171 under the full primary condition. A threshold of 25 σ²
   would split 91% of held-course windows under the primary condition.
3. **The two findings collide.** A threshold honest under the primary condition (about 170)
   leaves 56% of manoeuvres below it. Under those bearing errors, about half of all
   manoeuvres cannot be found by a goodness-of-fit test at a 5% false-split rate.
4. **C's detection delay is already near the bound.** The expected-cost bound gives a median
   of 209 s after the end of the change; the brief reports 235 s for the sliding-window alarms.
5. **Open question 2 has a negative answer.** Within one steady ownship leg, position
   continuity is exactly bearing continuity: one constraint, no more.

6. **Once the structure is given, timing and prior bounds decide the estimate.** In a crude
   stand-alone solve, the true structure declared two minutes late is as bad as one leg, and
   bounds on target speed and range cut the told-truth error by a third to a half.
7. **Undetectable manoeuvres do not need to be found.** Leaving them out of the solve is
   neutral on clean bearings and better under bearing errors.

The implication for the investigation: the gap to the told-truth solve is unlikely to be closed
by a better detector of the same kind. It needs a noise model inside the test, a prior on
structure for the manoeuvres the bearings cannot show, and honest "unknown" output.

## Q2. Position continuity across a manoeuvre

Take leg 1 as (b₀, a, c) with time from its start, and leg 2 as (b₀′, a′, c′) with time from
the knot at t_k. Choose any range R₀. Leg 1 puts the target at the knot at range
R_k = R₀ · ρ, with ρ = √((sin b₀ + a t_k)² + (cos b₀ + c t_k)²), on bearing
b(t_k). Leg 2 starts from range R_k on bearing b₀′ with relative velocity R_k · (a′, c′).

- Position is continuous if and only if b₀′ = b(t_k). The range matches automatically, because
  leg 2's scale is free.
- Any (a′, c′) is then physically realisable. The joined model has five parameters against six
  for independent slices.
- Numerical check: the joined model's Jacobian has rank 5 of 6 with ownship steady, and rank 6
  with an ownship zig anywhere in the window (`e1.py`).

Consequences:

- The benefit of the joined model does not come from continuity at the knot. It comes from
  sharing one range scale across ownship's turns.
- Two manoeuvres inside one ownship leg remain weakly determined whatever the algorithm
  (priority 5 of the brief).
- The useful relation between consecutive triples is across an *ownship* turn with the target
  steady: R₀ (a, c) + v_own,1 = R_k (a′, c′) + v_own,2, two equations that fix the range.

## Q1. A closed-form test for leaving the arctan family

**Cross-ratio invariant.** For any four bearings on a steady leg against a steady ownship:

    sin(b₁−b₂) sin(b₃−b₄) / (sin(b₁−b₃) sin(b₂−b₄)) = (t₁−t₂)(t₃−t₄) / ((t₁−t₃)(t₂−t₄))

It has no parameters and needs no fit (checked numerically, `e1.py`). It is the cross-ratio of
four lines through ownship, which equals that of four points on the target's straight track.
It is valid only within a steady ownship leg, and it amplifies noise badly on single bearings,
so it is a screening tool, not a replacement for a likelihood ratio.

**Linearised likelihood-ratio scan.** This is the practical answer. Linearise the
constant-velocity fit (four columns, J₀). A knot at time k adds two columns: the hinge
max(t − k, 0) times (cos b, −sin b)/R. Project them off J₀, and the statistic is the energy of
the residuals in that two-dimensional subspace.

- It costs one QR per candidate time: milliseconds for a full scan of a 720-row window.
- Under white noise each statistic is χ² with 2 degrees of freedom, and the maximum over
  candidate times is calibrated by simulation per geometry in the same milliseconds.
- Under any stated error covariance Σ, the statistic is a quadratic form with a known
  distribution; its mean inflation is tr(QᵀΣQ)/2.

Null distribution of the scan maximum on 150 held-course engagements, 200 noise draws each
(`experiments.py null`):

| Noise | Median | 95th percentile | Share over 25 |
|---|---|---|---|
| White, 1° | 4.8 | 10.6 | 0.0% |
| Correlated component only (half the variance, 60 s) | 24.9 | 58.2 | 50% |
| Bias wander only (0.5°, 30 min) | 13.2 | 52.5 | 21% |
| Wild bearings only (2%, ten times sd) | 14.3 | 46.0 | 22% |
| Wild bearings, then the brief's editing rule | 4.8 | 11.8 | 1.2% |
| Primary condition (all at once) | 61.8 | 171.2 | 91% |
| Primary condition, edited | 46.0 | 130.6 | 81% |

Reading:

- The 25 σ² threshold is conservative on white noise: 11 would give a 5% false-split rate.
- The correlated component inflates the statistic by 5.6 on average. The analytic value for a
  slow signal is 0.5 + 0.5 · (1+ρ)/(1−ρ) = 6.5 with ρ = e^(−10/60). Dividing by 6.5 restores a
  95th percentile of 9.0. An effective-sample-size correction works, if the correlation is
  known.
- Editing wild bearings restores the white-noise null almost exactly. That agrees with the
  brief's "one cheap gain".
- **Disagreement with the brief.** Here bias wander alone produces false splits; the brief says
  bias does nothing to C. A whole-window test sees a 30-minute wander as a slow manoeuvre; a
  short window does not (see the prototype test below), which is consistent with C's fading
  memory protecting it.
- The inflation cannot be whitened away. Manoeuvre signatures are low-frequency hinges, in the
  same band as the correlated error and the bias. A generalised least-squares test gets the
  null right but does not recover the lost power.

## Q5. Which manoeuvres are undetectable

For each of 1,673 manoeuvres in 600 engagements: the cost of omitting it from the joined model,
other knots at their true times, transition rows excluded, on noise-free bearings
(`experiments.py detect`).

| Threshold (σ² units) | Meaning | Below it, whole window | Below it, by the next manoeuvre |
|---|---|---|---|
| 11 | 5% false splits, white noise | 18% | 20% |
| 25 | the demonstrator's setting | 28% | 29% |
| 130 | 5%, primary condition, edited | 52% | 53% |
| 170 | 5%, primary condition | 56% | 57% |

- By kind, at 25: course changes 23% undetectable, speed changes 67%, both 23%.
- An ownship zig during the following leg helps: 23% undetectable with one, 33% without.
- The whole window adds almost nothing over the manoeuvre's own leg. Waiting does not help.
- The quantity is computable in real time for a *hypothesised* manoeuvre: the scan's
  non-centrality for a given velocity step is a closed form in the current geometry. The
  detector can therefore report "a turn of up to X° now would not be visible for Y minutes".
  That is a usable definition of "unknown".

## Q3. Best achievable detection delay

A velocity change Δv⊥ across the line of sight at range R changes the bearing rate by
Δḃ = Δv⊥ / R. Against a long prior history, the omission cost after τ seconds grows as
Δḃ² τ³ / (3 σ² Δt), so the delay to reach a threshold λ* is

    τ* ≈ (3 λ* σ² Δt / Δḃ²)^(1/3)

- Example: 5 m/s across at 10 km, λ* = 25, 1° noise, 10 s interval: about 100 s.
- The simulated delays are 1.45 times the formula at the median (quartiles 1.03 to 2.72),
  because the refit absorbs part of the change. Use it as a floor.
- Delay scales with the cube root of threshold and of noise variance. Honest calibration under
  correlated error (×6.5) costs a factor of 1.9 in delay, not 6.5.
- Simulated distribution at λ* = 25, from the end of the change: median 209 s, quartiles 81 s
  and 431 s; 71% of manoeuvres are detectable before the next one. From the start of the
  change the median is 360 s.
- The brief's sliding-window alarms were a median 235 s late. C is not far from the bound.

## Prototype test: does an online noise correction give a stated false-alarm rate?

A whole-window "is there a split?" test on noisy bearings, using no truth (`detector.py`):
one-leg fit from four range starts, the brief's wild-bearing editing on the residuals, the
linearised scan at the fitted solution, and the statistic divided by an inflation estimated
from the residual autocovariance (after removing the best hinge). Thresholds were set for 5%
false splits on white noise on 300 development seeds, then applied once to 400 fresh
held-course and 400 fresh manoeuvring engagements.

| Variant | Threshold | False splits, held course: white / correlated / bias / wild / primary | Manoeuvring windows flagged: white / primary |
|---|---|---|---|
| No editing, 25 σ² | 25 | 0% / 48% / 28% / 21% / 90% | 95% / 99% |
| Editing, 25 σ² | 25 | 0% / 48% / 28% / 2% / 84% | 95% / 98% |
| Editing, calibrated on white | 10.8 | 5% / 90% / 64% / 7% / 98% | 97% / 100% |
| Corrected, autocovariance to 5 min | 16.7 | 8% / 19% / 50% / 9% / 35% | 93% / 89% |
| Corrected, autocovariance to 15 min | 23.6 | 8% / 10% / 41% / 7% / 25% | 87% / 84% |
| Editing, threshold set on the primary condition | 131 | — / — / — / — / 5.5% | 85% / 89% |

- **The correction helps but does not deliver a stated rate.** Under the primary condition it
  takes false splits from 98% to 25–35%, not to 5%. Bias wander is the part it cannot remove.
- **It does not beat a higher fixed threshold.** At a matched 5–8% false-split rate under the
  primary condition, the plain edited statistic with a threshold of 131 flags 89% of
  manoeuvring windows; the corrected statistic flags 78% (5 min) or 69% (15 min). The noise
  estimate is contaminated by the other manoeuvres in the window. This repeats the brief's own
  finding that doubling the threshold did as much as a robust cost.
- **But the fixed threshold needs to know the condition**, which section 7.1 forbids, and it
  costs 12 points of detection on clean data (97% to 85%).
- **A short window removes the bias problem.** 95th percentile of the scan maximum on held
  course, relative to white noise (`win.py`, 300 engagements):

  | Window | Bias wander | Correlated component |
  |---|---|---|
  | Whole | ×4.8 | ×4.8 |
  | 40 min | ×1.8 | ×5.7 |
  | 20 min | ×1.2 | ×3.8 |
  | 12 min | ×1.0 | ×3.4 |

  This resolves the disagreement with the brief: C tests on short histories with a fading
  memory, so bias does nothing to it. A whole-window (time-late) test does not have that
  protection and needs a bias term in the model or a window of 20 minutes or less.
- **Single-split placement is poor on multi-manoeuvre windows**: the best knot is within two
  minutes of a true change in 37% of windows (white) and 31% (primary). This is the "split
  between them" failure and is expected of a one-knot test.
- Caveat: "manoeuvring windows flagged" counts a window with two to four changes as found if
  any one is seen. It is a weak measure of power and says nothing about misses per manoeuvre.

## Q4 and Q6. What limits the estimate once the structure is given

A stand-alone solve (`solve.py`): legs joined by position continuity, fitted to noisy bearings
after wild-bearing editing, scored by relative range error at the end of the window, 238
engagements. **My solve is cruder than the repository's**: three starts, no robust cost, one
scored moment. Its told-truth error on clean bearings is 0.166 against the brief's 0.065. Only
the paired comparisons below mean anything; the absolute figures do not.

| Solve | Clean: median error | Clean: share over 50% error | Primary: median error |
|---|---|---|---|
| One leg | 0.550 | 53% | 0.536 |
| True times, instantaneous knot at the midpoint | 0.194 | 29% | 0.514 |
| True times, constant-rate arc ("told truth") | 0.166 | 25% | 0.455 |
| Told truth, plus bounds on speed (3 to 20 kn) and initial range (2 to 20 km) | 0.109 | 5% | 0.251 |
| Only the manoeuvres costing over 25 σ² to omit | 0.152 | 27% | 0.365 |
| Same, plus the bounds | 0.121 | 13% | 0.257 |
| True structure, every transition declared 120 s late | 0.529 | 53% | 0.981 |

Findings:

- **Bounds on speed and range are worth more than anything else tried.** They cut the
  told-truth error by a third on clean data and nearly half under the primary condition, and
  the share of gross errors from 25% to 5%. If the repository's told-truth solve has no such
  bounds, the learned regressor matching it in range is explained by the regressor knowing
  them, and told-truth is not the ceiling.
- **Undetectable manoeuvres do not need to be found.** Leaving them out is neutral overall on
  clean data and better under the primary condition (0.365 against 0.455), because fewer
  parameters are fitted. The cost is confined to the 47% of engagements that contain one, on
  clean data only: 0.348 against 0.261.
- **Timing dominates.** The right structure declared two minutes late is as bad as one leg
  (paired median 3.5 times the told-truth error). The brief's sliding-window alarms are a
  median 235 s late. C″ is only 1.6 times told-truth, so either its timing is better than this
  or the repository's solve tolerates late knots better than mine; that should be measured.
- **Refitting the times inside the solve did not recover it** (`refine.py`, 138 engagements).
  With start and end free within ±3 minutes and those rows excluded, the error stayed at 3.0
  times told-truth, and the midpoint error only fell from 120 s to a median 60 s. Freeing the
  times from the *true* values made the solve 2.7 times worse. Time freedom trades against
  range. This is a negative result from a crude implementation, not a proof.
- **An instantaneous knot is the wrong model for a slow turn.** A knot at the midpoint of a
  turn Δψ at speed v and rate ω misplaces the target afterwards by
  (v/ω) · (2 sin(Δψ/2) − Δψ cos(Δψ/2)) along the bisector, which a shift in knot time cannot
  absorb. Over the simulator's course changes: median 92 m, 90th percentile 386 m, 99th 773 m.
  With no noise the knot model's range error is 6% at the median and over 10% in 40% of
  engagements; the arc model's is zero. With noise the arc is worth about 15% (0.194 to 0.166).
  The arc needs only the start and duration: displacement = D · mean velocity · tan(x)/x, with
  x = Δψ/2.
- **The leg-length prior is small as a detection aid.** As log prior odds it moves the
  threshold by −4.9 σ² units at 8 minutes into a leg and +2.3 at 45 minutes. At a threshold of
  11 that changes the undetectable share by about three points either way; at 170 it does
  nothing. The answer to open question 6 is that the prior earns its keep in the estimate
  (bounds, and averaging over what cannot be seen), not in detection.

## Detector v1: a truth-free causal segmenter, scored end to end (it does not work well)

`v1.py`. The detector receives only time, ownship's track, noisy bearings and the stated sd.
Every two minutes it runs the linearised scan on the current leg (at most the last 25 minutes),
declares a knot when the statistic passes a threshold, back-dates the knot to the scan's best
time, and puts a fixed two-minute transition around it. Variant A uses the raw statistic;
variant B divides by the online noise estimate. Thresholds were set for 5% false splits per
held-course engagement on white noise (200 development seeds), then scored once on 260
manoeuvring and 140 held-course engagements from fresh seeds, through the stand-alone solve.

| | Clean, A | Clean, B | Primary, A | Primary, B |
|---|---|---|---|---|
| True changes found within two minutes | 45% | 41% | 49% | 30% |
| False transitions per engagement | 0.92 | 0.85 | 5.2 | 1.7 |
| Structure exactly right | 15% | 13% | 0% | 3% |
| Median delay after the true end | 174 s | 204 s | 158 s | 263 s |
| Held-course engagements split | 1% | 4% | 100% | 66% |
| Gap recovered, solve without bounds | −0.77 | −1.26 | worse than one leg | worse than one leg |
| Gap recovered, solve with speed and range bounds | 0.27 | 0.35 | 0.33 | 0.32 |
| Ratio to told-truth with bounds, paired median (95% interval) | 2.9 (2.4–3.9) | 2.9 (2.2–4.0) | 2.1 (1.6–2.6) | 2.0 (1.6–2.3) |

- **It is well short of C**, which recovers 0.90 of the gap on clean data and 0.66 under
  bearing errors in the repository. Without bounds on speed and range its segmentation makes
  the estimate worse than assuming one leg.
- **The false-split rate holds on white noise and nowhere else**, as the earlier rounds
  predicted. The online correction (B) cuts false transitions under the primary condition
  threefold but also cuts detections.
- **Most of the "false" transitions on clean data are probably real changes placed more than
  two minutes off**: found plus false is about 1.3 per true change on a detector calibrated to
  1–4% false splits on held course. I did not store knot times, so this is unverified. If it is
  right, the weak point is knot placement by a one-knot scan on a 25-minute window, which is
  what C's confirm-by-full-solve step addresses.
- This is a baseline that shows what a detection-only design costs, not a candidate.

## Detector v2: confirm and re-place by a joined-leg fit (better boundaries, same estimate)

`v2.py`, truth-free as v1. The scan nominates (statistic over 12). A joined-leg fit on the whole
history then tries the candidate at five times within ±2 minutes and accepts the best if the
cost drops by more than a threshold (14.5 σ², set for 5% false splits on 150 held-course
development seeds). The latest knot is re-placed 4 and 8 minutes after declaration. Scored
once on 160 manoeuvring and 80 held-course engagements, the same bearings as v1.

| Clean bearings | v1 (scan only) | v2 (confirm and re-place) |
|---|---|---|
| True changes found within two minutes | 42% | 59% |
| False transitions per engagement | 0.91 | 0.71 |
| Structure exactly right | 15% | 30% |
| Knot distance to nearest true change, median | 106 s | 61 s |
| Knots within 2 min / 2 to 5 min / over 5 min | 54% / 34% / 12% | 68% / 17% / 15% |
| Held-course engagements split | 1% | 3% |
| Gap recovered, solve with bounds | 0.39 | 0.40 |
| Estimate error, v2 over v1, paired median (95% interval) | — | 0.97 (0.79–1.05) |

- **The placement hypothesis was right.** Three quarters of v1's "false" transitions on clean
  data were real changes placed two to five minutes off.
- **Confirmation fixes the boundaries**: more found, fewer false, placement error nearly
  halved, twice as many structures exactly right.
- **It does not fix the estimate.** The paired ratio is 0.97 with an interval spanning 1.
- **The reason is visible in the engagements where v2's structure is exactly right** (48 of
  160): its error is still 2.8 times told-truth (0.296 against 0.103). Where it only misses
  changes the ratio is 3.6; where it has false or misplaced ones, 2.5. Getting every change
  within two minutes with nothing extra is not enough for this solve; the residual timing
  error (median about a minute) and the fixed two-minute transition cost almost as much as
  missing the change. The brief reports the same effect in the repository at 1.5 times.
- **Under the primary condition nothing changes**: every held-course engagement is split, with
  about five false transitions per engagement, for v1 and v2 alike.
- **What this cannot tell apart**: whether timing sensitivity is a property of the problem or
  of my crude solve (no robust cost, fixed transition length). The repository experiment that
  shifts true times by 60, 120 and 240 s decides it.

## Critical reading of these results

- **The simulator is mine.** The 28% and the 30% agreeing could be a coincidence of my ownship
  model. The first repository experiment should repeat the omission-cost calculation on seed
  321 and cross-tabulate it against C's actual misses.
- **Expected cost is not detection probability.** A manoeuvre at exactly the threshold is
  found about half the time. The undetectable shares are therefore on the optimistic side.
- **The scan is linearised at the truth.** A real test linearises at a noisy fit; at long range
  and before the first ownship zig that fit is poor.
- **Knots are instantaneous and transition rows are excluded using the true times.** A real
  detector does not know which rows to exclude, so its costs are lower.
- **One scenario for the knot-placement profiles.** The joined model placed the knot within a
  7-minute band against 11 to 16 minutes for independent slices. Anecdote only.

## What I would change in the brief's plan

1. **Reorder the priorities.** Put a noise-calibrated threshold (priority 2) and transition
   timing (priority 3) ahead of fewer misses (priority 1). Score misses only on manoeuvres
   above the detectability threshold.
2. **Make the first repository experiment the cross-tabulation**, not the joined-leg model at
   scale: omission cost per true manoeuvre against C's hit, miss and delay.
3. **Do not expect an online noise estimate to deliver priority 2 on its own.** The prototype
   test above shows it is partial and costs power. The better-supported route is a test window
   of 20 minutes or less (removes bias wander), wild-bearing editing (removes wild bearings),
   and a correlation estimate taken only from legs already confirmed steady.
4. **Treat the undetectable half as a prior problem.** The learned regressor reaching the
   told-truth range error is consistent with this: it is using manoeuvre statistics, not
   detection. A hypothesis bank with a leg-length hazard is the classical equivalent, and it
   must be compared with controls that hold the same prior.
5. **Report "unknown" from the non-centrality bound**, as in Q5.
6. **Check whether the told-truth solve bounds speed and range.** If not, add the bounds to
   every system and re-state the numbers to beat.
7. **Measure the solve's sensitivity to knot timing in the repository** (true structure, times
   shifted by 60, 120 and 240 s). If it is as steep as here, declaration delay and
   back-dating of the knot are the main lever, ahead of both misses and false alarms.
8. **Add a "told detectable" reference**: the solve given only the manoeuvres above the
   detectability threshold. It is a fairer ceiling than told-truth.

## Files

- `sim.py`: simulator and joined-leg model.
- `experiments.py`: detectability and delay (`detect`), null distribution of the scan (`null`).
- `e1.py`: cross-ratio check, Jacobian rank, knot-placement profiles.
- `detector.py`: prototype whole-window split test with editing and noise correction.
- `win.py`: effect of window length on the null under bias wander and correlated error.
- `solve.py`: structure-given solves (knot, arc, bounds, detectable-only, late).
- `refine.py`: re-estimating transition times inside the solve.
- `v1.py`: truth-free causal detector, calibrated on development seeds and scored end to end.
- `v2.py`: v1 plus confirmation and re-placement by a joined-leg fit.
