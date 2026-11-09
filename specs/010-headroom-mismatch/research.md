# Research: spec 010, headroom under bearing-error mismatch

## R1. Where the mismatch is drawn

- **Decision**: an overlay. The 0.6.0 kernel runs unchanged and yields the noise-free bearing b,
  the white draw g and the dropout flag per sample. The overlay draws from a separate stream
  derived from the scenario seed (label `mismatch`), in a fixed order: σ factor; correlated
  process; bias process; outlier flags and values, for every sample whether dropped or not.
  Generator version 0.7.0; with no condition the 0.6.0 path is taken unchanged.
- **Rationale**: FR-002 and FR-003 hold by construction: no kernel draw moves.
- **Alternatives**: draws inside the kernel (shifts later draws; breaks byte-identity); a
  post-processing tool on finished packs (cannot recover b after float32 rounding).

## R2. The error model and its severities

Bearing error at sample i: e_i = w_i + c_i + β_i + o_i, with σ_true = σ_nominal × s.

| Kind | Model | Mild | Central | Harsh |
| --- | --- | --- | --- | --- |
| Correlated | c: first-order Gauss–Markov, correlation time τ; a share f = 0.5 of σ_true² is correlated and the rest white, so the total sd is unchanged | τ = 30 s | 60 s | 180 s |
| Bias | β: Gauss–Markov with sd σ_b and correlation time 30 min (a part constant over the window is unobservable, see edge cases) | σ_b = 0.25° | 0.5° | 1° |
| Untold σ | s log-uniform on [1/k, k], per engagement | k = 1.25 | 1.5 | 2 |
| Outliers | with probability p the error is replaced by N(0, (10 σ_true)²) (the glint mixture) | p = 0.5% | 2% | 5% |

- **Decision**: these are a **declared design grid that brackets plausible behaviour**, not
  measured sensor figures. The primary condition is all four at central.
- **Rationale**: a literature search (9 November 2026) found the model forms in open sources but
  no authoritative open figures for passive-sonar bearing error. Bearings-only TMA papers assume
  white Gaussian error almost without exception; time-correlated bearing noise and prewhitening
  appear in a US Navy patent; glint is modelled as a two-component Gaussian mixture with a glint
  probability; untold or mis-stated σ and bearing-mean mismatch are studied as model uncertainty.
  Quoting real figures would in any case be outside the classification rule (FR-006).
- **Consequence**: the spec's wording "from open literature" is corrected to "model forms from
  open literature; severities a declared grid". The owner knows the domain and is asked to
  confirm or change the grid before the decision record.
- **Sources**: Le Cadre and Jauffret, convergence of iterative methods for bearings-only TMA
  (IEEE); US Navy TMA patent with a prewhitener for time-correlated noise (DTIC ADD020092);
  Student-t and glint-mixture filtering (arXiv 1703.05189, 1704.00040); EUSIPCO 2023 paper 2038 on
  bearings-only filtering under bearing mean and sd mismatch.
- **Alternatives**: a single "realistic" condition (unfalsifiable choice); severities tuned until
  headroom appears (the risk the decision record exists to prevent).

## R3. The ceilings

- **Decision**: generalised least squares on the declared piecewise-CV parameterisation with the
  true segmentation. The Gaussian part of the error has a known covariance
  Σ = σ_w² I + σ_c² exp(−|Δt|/τ) + σ_b² exp(−|Δt|/τ_b), built on the valid samples' times, so
  dropouts need no special case. Residuals and Jacobian rows are multiplied by the inverse
  Cholesky factor before the layer's normal equations.
  - **Realisation ceiling**: Σ plus (10 σ)² on the diagonal at flagged outliers. Exact.
  - **Attainable ceiling**: flags unknown. Iteratively reweighted: each bearing's outlier
    responsibility from the two-component mixture at its current marginal residual, and the
    diagonal inflated by responsibility × (10 σ)². An approximation to the mixture likelihood.
- **Rationale**: FR-010 and FR-011. The realisation ceiling bounds the attainable one from above;
  if the two are close, the approximation is immaterial, and both are reported.
- **Mismatch off**: Σ = σ² I, the whitening branch is skipped and the existing oracle path runs,
  so FR-013 holds row for row.
- **Causality**: Σ for a row uses samples up to that row's time only (FR-014).
- **Alternatives**: a particle or MCMC posterior mean as the ceiling (the true Bayes ceiling, but
  slow, a different estimator class, and it would add a prior the other estimators lack).

## R4. The bound

- **Decision**: Fisher information Jᵀ Σ⁻¹ J with known manoeuvre times and kinds
  (`known_manoeuvres`), outlier-flagged bearings given their inflated variance.
- **Note**: for the mixture this is the realisation bound, slightly below the true bound of an
  estimator that does not know the flags; efficiency of the attainable ceiling is read with that
  in mind.

## R5. The classical robust control

- **Decision**: C″'s solve with three textbook additions, each also scored alone:
  1. Huber weights on standardised residuals (iteratively reweighted);
  2. σ̂ from the median absolute residual on the current prefix;
  3. whitening by an estimated first-order correlation ρ̂ from the lag-one autocorrelation of
     residuals within legs, with ρ̂^(Δt/dt) across gaps.
  It does not model the bias: a classical bias state is a larger design, listed as not tested.
- **Settings grid** (chosen on seed 320, primary condition, by median range error on G5 rows):
  Huber constant 1.0, 1.345, 2.0; minimum bearings before σ̂ and ρ̂ are trusted 30, 60, 120
  (nominal values below it); ρ̂ shrunk toward 0 by 0, 0.25, 0.5.
- **Segmentation**: for the gate, the control and C″ are solved on the true segmentation as well
  as on C's (R6). C runs at the nominal σ.
- **Alternatives**: a Student-t likelihood (similar effect, one more parameter); an augmented
  state for the bias (noted above).

## R6. What headroom is measured on

- **Problem found while planning**: the spec's FR-042 compared the robust control with the
  attainable ceiling. The ceiling has the true segmentation and the control has C's. With no
  mismatch at all, C recovers 0.898 of the gap to the oracle (Gate S), so that comparison would
  very likely exceed 10% before any mismatch is added. The verdict would restate Gate S.
- **Decision**: the gated comparison gives **both sides the true segmentation**. It then measures
  only what knowing the error model is worth. The same comparison on C's segmentation is
  reported beside it, with the mismatch-off value subtracted, as the segmentation part.
- **Owner**: this refines the 10% threshold confirmed on 9 November (same number, a stated
  denominator). No result exists. It is flagged in the SRD row for the owner's merge.
- **Statistic**: R = median range error (robust control) / median range error (attainable
  ceiling) − 1 on G5 rows, paired scenario-clustered bootstrap of the ratio; rows where either
  side states nothing are handled as at Gate S, and the result is also given on rows every
  estimator answers.

## R7. Gate H

| Check | Criterion | Kind |
| --- | --- | --- |
| H-a | attainable ceiling's efficiency against the bound on settled rows of the primary condition within the band the decision record declares from seed 320 | soundness |
| H-b | on mismatch-off data the robust control's median range error at most 1.02 × C″'s, interval wholly below | soundness |
| H-c | R (R6) on the primary condition: **material** if the interval is wholly above 0.10; **not material** if wholly below; otherwise inconclusive, one re-score on a larger fresh seed (323), then final | the verdict |

- Validation (seed 321) applies H-a and H-b only. H-c is computed and reported there but does not
  stop the gate (FR-043).
- Reported, not gated: course and speed; every other condition; the realisation ceiling; the
  segmentation part; E for information.

## R8. Operational units

- **Decision**: median range error in metres (and as a share of range), course in degrees, speed
  in knots; **time to a settled solution**: the first of zig + 5, 10, 15, 20 min at which range
  error is within 10% and stays so at the later scored times, reported as the share of
  engagements settled by each time.
- **Note**: this is a score, so it uses the truth like every error measure. The spec's wording
  ("computed without the truth where the operator could not have it") is corrected.

## R9. Seeds and reuse

- 320 tuning, 321 validation, 322 test, 323 held for an inconclusive re-score. Seed 314 is not
  used. The IMM and EKF are re-tuned on 320 (primary condition) with the grids of
  `experiments/20261104-man2-refs/`.
