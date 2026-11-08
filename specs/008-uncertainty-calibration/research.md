# Research: uncertainty calibration (spec 008)

Each item gives the decision, the reason, and the alternatives considered.

## R1. Which covariance, in which frame

- **Decision:** the physics layer's `PhysicsOutputs.cov`: the Gauss–Newton covariance at the final
  iteration, σ²-scaled, of the state (x, y, vx, vy) at the reported row (east, north, metres,
  m/s), as the ONNX conformance tests already check it. E's covariance is the same quantity from
  E-w's solve, so it uses E-w's weights.
- **Why:** it is free (research note 04 §2), it is already exported, and it is the quantity a
  calibration head corrects.
- **Alternatives:**
  - a covariance in the layer's parameters (window-start position, segment velocities): no, it is
    not comparable across segmentations;
  - Monte Carlo over noise draws: no, it is far too costly and not exportable.

## R2. What each prediction row stores

- **Decision:** the 10 upper-triangle entries of the 4 × 4 covariance, plus `log_range_sd` (an
  existing optional field), `course_sd_rad`, `speed_sd_mps` and `cov_ok`. All are optional
  `PredictionRow` fields, so the schema is extended additively and older files stay valid.
- **The standard deviations** come by first-order propagation through:
  - log range = ½ log(Δx² + Δy²), with Δ relative to ownship at the row;
  - course = atan2(vx, vy);
  - speed = hypot(vx, vy).
- **Why:** the full covariance allows NEES and any later re-parameterisation. The derived
  standard deviations make the coverage measures trivial to recompute.
- **Alternatives:**
  - standard deviations only: no, NEES needs the cross terms;
  - a covariance in (log range, course, speed): no, it is derived and cannot be mapped back.

## R3. IMM and EKF covariances

- **Decision:**
  - the IMM reports the mixed covariance (`_mix` already returns it), as its top-left 4 × 4
    block;
  - the EKF reports its 4 × 4 block;
  - both are passed out through optional output arrays, as `nis_out` is.
- **Why:** the gitma-ported numerics and their f32 point rows stay byte-identical (the Gate 2
  references are frozen by name).
- **Alternative:** recompute a covariance outside the filter. No: it would not be the filter's own
  statement.

## R4. Calibration measures

- **Coverage.** For each quantity q in {log range, course, speed}, a row is covered at level α
  when |e_q| ≤ z_α · sd_q, with z = 1 (68.3%) and 1.96 (95%). Course errors are wrapped to
  (−π, π]. A row with no plausible estimate, or with `cov_ok` false, is not covered (FR-012).
- **NEES.** eᵀ P⁻¹ e for the 4-state error e = state − truth at the row. Reported:
  - the median over the χ²₄ median (3.357);
  - the share of rows below the χ²₄ 95% point (9.488).
- **Proper score.** The 95% interval score (Gneiting and Raftery 2007), per quantity:
  (u − l) + (2/0.05)·(l − y)⁺ + (2/0.05)·(y − u)⁺, in log range (natural log), degrees and knots.
  Its mean over rows is the score of record. It is linear in the miss, so it is more robust to
  gross rows than the Gaussian NLL. A missing estimate is charged the 99th percentile of the
  estimator's own finite scores, and the share of missing rows is reported.
- **Sharpness:** the median 95% interval width per quantity.
- **Intervals:** scenario-clustered paired bootstrap, 97.5%, 2,000 resamples, with the scorer's
  resamples (`eval/bootstrap.py`).
- **Alternatives:**
  - Gaussian NLL as the score of record: no, gross rows dominate it (a 10% gross share at E);
    it is reported as a diagnostic;
  - CRPS: no, it adds nothing over the interval score for Gaussian marginals and needs more care
    with wrapped course.

## R5. Calibration head

- **Form.** One scalar log-scale s per row; the calibrated covariance is e^{2s} · P.
  - s = b · tanh(head(h_k ⊕ log sd_raw ⊕ code_k)), with b = 2 (the Gate 1 `scale_bound`);
  - h_k is E-w's frozen encoder state at the row (64-d);
  - sd_raw is the raw log-range, course and speed standard deviations;
  - code_k is C's code at the row;
  - the head is a 2-layer MLP (width 32, tanh) whose last layer is zero-initialised, so it starts
    as the identity.
- **Why:**
  - a scalar keeps P's shape, which the solve knows, and corrects only its scale, which the weight
    rescaling (panel R2-5) and model mismatch (manoeuvres, gross rows) distort;
  - research note 04 §2 names a scalar.
- **Alternative:** a diagonal correction in (log range, course, speed). This is deferred: it needs
  a non-linear map back to (x, y, vx, vy). It becomes a candidate if a scalar fails coverage on
  one quantity only.

## R6. Training loss

- **Decision:** β-NLL (Seitzer et al. 2022) on the 4-state Gaussian:
  L = stopgrad(e^{2sβ}) · [½ eᵀ(e^{2s}P)⁻¹e + 4s]. Per-row terms are capped as E-w's (100); rows
  with `cov_ok` false are excluded and counted. β = 0.5 is declared in the plan.
- **Why:** SRD §4 names β-NLL. With P fixed, only s learns, so β only reweights rows; it keeps the
  rows with large raw variance from dominating.

## R7. Features and data

- **Decision.** Run the carried E (e-s3) once over:
  - stream seed 318 (train split, 9,930 σ = 1° scenarios, G5 rows);
  - validation ordinals 0–1499.

  Cache per row: h_k, the raw covariance, the code at k, the state and the truth. Head training
  then reads the cache and needs no physics solves.
- **Why:** E is frozen (FR-022). The physics layer is the cost (about 10 s per scenario with C
  re-run, as `g2predict`). Caching makes three seeds plus controls cheap (minutes per epoch).
- **Workflow:** `g2predict` gains `--features`, written beside the predictions as `.npz` per
  shard, on a new `g2features/<plan>` branch family.

## R8. Classical control: per-slice temperature

- **Decision:** a single log-scale per slice, fitted by the same loss on validation tuning
  ordinals 0–499. There are 8 slices: the 4 G5 times × open-at-k or not, declared in the plan.
- **Why:** this is the classical stand-in for what the head could learn. Gate 2 showed a rule can
  match a learned component. G3-c is the learning claim against it.
- **Alternatives:**
  - one global temperature: no, too weak a bar;
  - isotonic recalibration: no, it is not a covariance and cannot drive NEES.

## R9. Time-late variant (constitution IV; panel G7)

- **Decision:** E-w with the encoder's causal mask removed: it reads every row of the scenario
  (only padding is masked), so its per-bearing weights at rows ≤ k and its start correction may use
  bearings after k. It is trained as ew-s1 was (one seed, as spec 003's control d; plan
  `configs/gate2/g3-timelate.json`), on CI, and scored on validation only, beside the causal E-w.
- **Amended at implementation:** the solve stays C's at prefix k, not a whole-window solve with
  `k_state`. C's knots exist only up to k in the prefix tables, so a solve across later
  manoeuvres would be biased by missing knots, and C's whole-window segmentation would need a
  new segmentation and table run. The variant therefore measures what the *learned* part leaves
  unused, which is the question the panel asked (G7); the classical part's future information is
  not tested.
- **Rule:** it must score at least as well as the causal E-w in gap recovered (paired), or the
  shortfall is reported in the write-up.
- **Why:** it is the constitution's check that the causal model is not leaving information unused
  through a design fault.

## R10. Process follow-ons

- **Stored errors (R2-6).**
  - The scorer writes `errors.npz` with every re-solved estimator and now also the per-row
    calibration arrays.
  - A new `--reuse <errors.npz>` loads C, one leg, the oracle, the IMM, the EKF and GLR from that
    file, if its rows (ordinal, k) match exactly. A row mismatch is refused.
- **Coverage assertion (G10):** in gate mode on the test split, `count` MUST equal
  `test-digest.json`'s `sigma1_scenarios`, and `start` MUST be 0.
- **Merge counts (G11):** g2predict's and segment's merges assert that every ordinal in
  [a, b) appears once.
- **Last-epoch shuffled (G4):** training also saves `last.safetensors`; validation scoring takes
  the shuffled control's last weights as a separate estimator.
- **Shuffled rule source (G9):** the test gate reads it from the validation record's
  `validation.json` by digest; `carried.json` records that digest.
- **Control headers (R2-7):** the prediction header carries the model's plan entry
  (`model_settings`) and the C segmentation file's SHA-256.

## R11. Gate 3 criteria (proposed; owner merges the SRD amendment)

- **Proposed after the validation baseline** (US2), before any calibration training. The defaults
  are as spec FR-030. The bands are fixed in the amendment.
- **G3-a.** Coverage is judged on all rows (not covered = missing), so a model that fails to
  answer cannot pass by abstaining. A coverage band rather than a one-sided bound penalises both
  over- and under-confidence.
- **G3-b.** NEES uses the median, so gross rows do not dominate. Their coverage is reported
  separately.
