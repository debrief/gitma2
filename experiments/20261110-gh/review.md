# Gate H: agent review panel

Five independent, read-only reviewers: evaluation statistics, estimation and numerics, TMA
domain, reproducibility and pre-registration, and red team. Each was briefed on the committed
records (`experiments/20261110-gh-decision/`, `experiments/20261110-gh-val/`, this folder), the
code and the per-row arrays on the results branches, and returned a verdict with findings tagged
[blocker], [major] or [minor]. Their scratch scripts are not part of the record. Findings are
condensed; the numbers are theirs unless marked.

The reviewers are agents of the same model family as the author (research note 10 §4). They
verified independently by computation where stated; they are not independent in outlook.

# Round 1

All five returned **approve-with-findings**. None raised a blocker. Every reviewer who recomputed
it reproduced H-c: R = −0.4% [−2.4, +1.4], wholly below 10%.

**Decision: H-c "not material" stands, as registered.** The majors concern what the verdict may
be taken to mean. The test README was revised accordingly (commits 85a428f and the one adding
this file); no criterion, setting or number of the gate changed.

## Statistics: approve-with-findings
- Reproduced with own code and with the repository's bootstrap: R −0.392% [−2.361, +1.445] on
  20,473 rows, 5,203 scenarios; course, speed, all-answer, plain over ceiling, H-a (1.2573) and
  H-b (+1.9% [−0.9, +4.7] on test) all reproduce.
- [major] Heterogeneity by true range is hidden by the pooled figure: +4.9% [+1.6, +8.2] under
  11 km, +3.1% [−0.3, +7.1] at 11–17 km, −2.6% [−5.5, +0.7] at 17–25 km, −5.2% [−8.3, −1.9]
  beyond. Two post-hoc cross-slices cross 10% in interval (under 11 km and settled: +7.2%
  [+3.6, +11.6]; under 11 km at 15 min or later: +8.6% [+2.7, +12.9]); no point exceeds 10%.
  "Nothing measurable to win" is too strong. *Done: table and wording added (the author
  recomputed the table: same values).*
- [minor] The median is the most favourable statistic; none comes near 10% (geometric mean +0.9%
  [−0.7, +2.6]; trimmed mean +0.3%; P90 +1.7% [+0.1, +3.0]; P95 +1.8%). The control is slightly
  worse in the tail. [minor] "As accurate as" holds in distribution only: row by row the fits
  differ by up to a factor 3.3. [minor] The "all-answer" figure conditions on the trackers
  answering (30% of rows dropped); on rows the pair answers, R is −0.5% [−2.4, +1.4]. [minor]
  Power is ample pooled (+10% is about ten standard errors away). [minor] `gate.LEVEL` defaults
  to 0.95 and the gate's 97.5% comes from the plan: correct, fragile. The speed interval's lower
  edge is seed-sensitive near zero.

## Estimation and numerics: approve-with-findings
- Clean: `cov.py` matches the generated process (empirical autocovariance 1.24/0.67/0.43/0.23
  against 1.28/0.70/0.45/0.24 at lags 0/1/6/30); the whitening touches the bearing block only,
  with the parent's priors, damping and acceptance; no truth reaches the control; the bound is
  right for a known Gaussian covariance.
- [major] The outcome was close to predetermined by the severity grid: linearised, the plain
  solve's range sd over exact GLS for the Gaussian part of the primary condition is 1.028
  (P90 1.06); 1.085 at τ = 180 s; 1.12 at 90% correlated; 1.06 at 1° bias. Only outliers could
  reach 10%, and Huber removes them. *Done: stated in the README.*
- [major] The "chord" explanation of the 1.26–1.6 efficiency is not supported: noise-free, the
  plain solve's error is 2.0%; with white noise 5.4% (efficiency 1.61); a 2% floor explains about
  1.16. The rest is unexplained (candidate: 4 + 2 × knots parameters under weak priors against
  the bound's 8). R is not compromised: both sides share the solve. *Done: the claim is
  withdrawn and marked not established.*
- [minor] The attainable ceiling is slightly handicapped (marginal responsibilities, three
  reweightings from a contaminated start): the exact realisation ceiling is 0.8% lower, so R
  against it is about +0.4%. [minor] The control's fallback can over-whiten, which only raises
  R. [minor] The validation "control beats the ceiling" is noise.

## Reproducibility and pre-registration: approve-with-findings
- Verified: decision, plan and SRD row in one commit (a814ac5, 06:57 UTC) before validation
  (e4d305f) and test (eb028df); the plan's digest binds; no estimator or scorer change between
  the runs; run plans match the decision; all 22 records from clean trees; **seed 322's primary
  condition regenerated from a clone at eb028df with all eight digests equal**; R recomputed
  exactly from `errors.npz`; README spot-checks match; forecasts predate results.
- [major] The owner's go-ahead was not recorded: validation and test ran against a row still
  "proposed; owner to merge". *Done: dated line in SRD §9 and in the README.*
- [major] Registered comparisons were not delivered: C and C″ on C's own segmentation (plan `c2`
  block, research R6, FR-020, FR-033). *In hand: run launched on the validation seed after a
  fix to how C's parameters are read; record in `experiments/20261110-gh-c2/`.* The naive
  baseline is absent. *Done: stated (nothing is trained).*
- [minor] H-b's form and H-a's band were set after tuning results (disclosed). [minor] Only the
  scoring jobs' CPUs are recorded (*README corrected*). [minor] Forecasts were given for the
  primary condition only. [minor] `headroom.json` carries no plan digest (`gate.json` does).

## TMA domain: approve-with-findings
- The results are physically sensible; the operational figures are plausible for 1° bearings at
  about 16 km.
- [major] The mismatch is stationary and independent of geometry. Most likely to hide headroom:
  a bias that steps or lags at the ownship zig (range comes from the bearing-rate change across
  the zig); bursty, one-sided outliers; σ varying within the engagement. [major] "An untold σ
  costs nothing" is true by construction. [major] True manoeuvre times hide the likeliest
  operational cost: correlated error and bias mimic manoeuvres. *Done: all three stated.*
- [minor] The settled measure uses the truth, its denominator changes between times, and at
  + 20 min "stays settled" is vacuous. [minor] The IMM and EKF at about 60% error are not
  credible as tuned references. *Stated.*
- Suggested next experiment: this harness on C's own segmentation with a zig-coupled bias and
  bursty outliers, before the scaled regressor.

## Red team: approve-with-findings (the verdict as registered; not the consequence as worded)
- Reproduced R; tails do not rescue headroom (P75 +0.2%, P90 +1.7% [+0.2, +3.0], P95 +1.8%;
  share of errors above 1.0 favours the control).
- [major] The reference is not an upper bound: the control is at 1.22–1.25 times the bound, room
  an end-to-end learner or a better motion model could claim. [major] The true segmentation
  defines away the likeliest locus, and the registered C-segmentation comparison was missing.
  [major] The simulated mismatch is the control's own model family. *All three stated.*
- [minor] The control was tuned on the gated condition and statistic. [minor] The gate was
  confirmatory (forecast 0.85). No manipulation found.
- **Accepted wording**, adopted in the README: "On the true segmentation, under the declared
  stationary Gaussian-plus-outlier bearing-error family at the stated severities, knowing the
  true error model is worth no more than about 1.5% (median) to 3% (P90) in range error to the
  piecewise-CV least-squares solve, over a textbook robust fit. Learning the bearing-error model
  for this solve is not pursued. Not shown: that this solve is near optimal; that segmentation
  is robust to mismatch; anything about other error families or real data."

# Outcome

- **Gate H, H-c: headroom not material.** Decided in round 1; no second round was needed because
  no reviewer disputed the verdict and every major is a statement the record now makes.
- **The follow-on is narrower than the SRD row's words.** The row says "the learning track on
  this estimator stops". The panel supports: *learning the bearing-error model for this solve is
  not pursued.* Whether the learning track as a whole stops is the owner's, with the scaled
  regressor experiment already decided as the next step.
- **Open from this panel:** the C-segmentation comparison (running); why the solve is 1.26–1.6
  times the bound; the short-range 5%; a zig-coupled bias and bursty outliers.
