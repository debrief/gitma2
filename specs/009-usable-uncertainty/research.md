# Research: usable uncertainty (spec 009)

All evidence here comes from validation seed 314 **tuning ordinals 0–499** (spec 008's feature
cache `results/g2predict-g3-feat-val-42472096319`, 1,971 rows, 1,951 with a usable covariance),
never from the scoring ordinals 500–1499 (Gate 3 panel lesson). Fits are in sample on those rows;
they set the design, not a result.

## R1. Can bad courses be flagged causally? (scoping, before the re-scope)

- **Finding**: 35.2% of E's course errors exceed 30° and 9.8% exceed 90°. Their AUC against causal
  signals: E's stated course sd 0.61, log-range sd 0.59, C's open flag 0.53, minutes since the zig
  0.49, C's code 0.54; a logistic model on E's encoder state, stated sds and code, fitted on
  ordinals 0–249 and tested on 250–499, 0.62.
- **Consequence**: a determined/undetermined split cannot separate them (half the rows declared
  undetermined still leaves 28–29% of the rest over 30°). **Owner decision (2026-11-08)**: state
  course probabilistically.

## R2. The course statement

- **Decision**: a mixture on the circle, p · vonMises(0, κ) + (1 − p) · uniform, centred on E's
  course. κ = 1 / (a · sd)², with sd E's stated course sd (from the solve) and a a learned (or
  per-slice) scale; p learned (or per slice). The reported statement is the arc half-width
  X = min(Xmax, 1.96 · a · sd) and its probability P = p · P_vm(|e| ≤ X) + (1 − p) · X/π.
- **Why**: proper (the log score of the mixture density at the true course is a proper score);
  honest when the course is unknown (p → 0 gives "unknown", not a whole-circle Gaussian); keeps
  the solve's information through sd.
- **Evidence (per-slice fit, tuning rows)**: stated P 0.605 against a hit rate of 0.608 overall;
  mean X 21.5°; per-cell log score 0.70–0.87 against 1.838 for the uniform; p between 0.36 and
  0.90 by cell, lowest on rows with a transition open. In five bins of P the hit rates are 0.600,
  0.579, 0.582, 0.605 and 0.673 against stated 0.479, 0.592, 0.623, 0.645 and 0.686: the lowest bin
  is under-confident by 0.12, so the per-slice temperature alone fails a per-bin check.
- **Settings**: Xmax = 45° (an arc wider than ±45° is not a usable course statement); P is
  recalibrated by an isotonic map fitted on the tuning rows (applies to the head and the
  temperature alike), which fixes bin reliability without touching the arc.
- **Alternatives**: a wrapped normal (no closed-form mixture with the uniform); a fixed arc with
  only p learned (loses the solve's information).

## R3. Range and speed intervals

- **Decision**: 95% intervals q = c · sd (log range ratio; speed in m/s), with c learned per row
  (head) or per slice (temperature), trained on the **interval score** of the exact errors (the
  gate's own proper score for central intervals).
- **Why**: likelihood fits of Gaussian or Student-t scales do not target coverage: on the tuning
  rows they gave 0.92–0.96 (log range) and 0.91–0.96 (speed) depending on the tail (ν = 1, 2, 3, 5,
  ∞); the interval score targets the 95% quantile directly.
- **Alternative**: Student-t with a fixed ν (kept as a diagnostic, not the statement).

## R3a. The temperature's sd power (added during implementation, tuning rows only)

- **Finding**: with the plain temperature (cells on E's sd), the shuffled head beat the
  temperature on the tuning rows (standardised summed score 2.85 against 3.08; the head 2.46), so
  the learning control was a strawman. Stating each cell on sd^β fixes that: by quantity the best β
  on the tuning rows is 0.7 (log range), 0.9 (course) and 0.4 (speed), and the tempered temperature
  scores 2.66. An absolute rule (β = 0) is worse than either (3.48).
- **Decision**: the temperature picks β per quantity from the plan's grid
  (1.0, 0.9, …, 0.3) on the tuning rows inside its own fit (`calib.statement_fit.fit_temperature`);
  the head sees the raw log sds among its inputs and can learn the same tempering.
- **Reproduce**: `scripts/research/g4_tuning.py` (R1, R2, R3a; R1's AUCs there are single
  signals, 0.51–0.60, on the 1,951 usable rows).

## R4. Errors used for training (Gate 3 panel)

- Exact: wrapped course error (atan2 of the sine and cosine of the difference), log range ratio
  ln(r̂ / r), speed difference; computed from the cache's state, truth and ownship. No linearised
  local error is used.

## R5. The 4-state covariance

- Kept as the solve's (raw) for downstream use; its χ² share is reported, not gated (owner
  re-scope). A correlation-shrinkage variant is not built in this spec.

## R6. The head

- Inputs as spec 008 (E-w's encoder state at the row, raw log sds, C's code), outputs (a, logit p,
  c_range, c_speed) bounded by tanh; output layer zero-initialised so the untrained head equals the
  temperature's global values (fitted first). Loss: the course log score plus the two interval
  scores, each divided by the temperature's mean on the tuning rows so the three are commensurate.
- Three seeds, a shuffled-label control (best and last epoch), the temperature in the same form per
  slice (G5 minute × open at k). Early stopping on tuning ordinals 0–499.

## R7. The gate (proposed defaults; owner merges the amendment)

- G4-a range and speed coverage95 wholly in [0.92, 0.98]; G4-b overall |hit − P| wholly within
  ±0.03 and every bin of P within ±0.05; G4-c course log score above the uniform's wholly, mean P at
  least 0.5; G4-d learning: the head's standardised summed score below the temperature's wholly,
  void if the shuffled control also beats the temperature; G4-e points identical.
- **Forecast basis**: the per-slice temperature already passes G4-c and, after isotonic
  recalibration, should pass G4-b; G4-a should pass for an interval-score-trained scale; G4-d is
  unlikely given R1 (AUC 0.62); but on the tuning rows (in sample) the head scores 2.46 against
  the tempered temperature's 2.66 (R3a), so G4-d is open.

## R8. Spec 008's carried minors

- g3predict-style files record `calibration.git_commit` and `git_dirty` (read before writing);
  control files use the model ids `cal-shuffled-best` / `cal-shuffled-last`; the gate's records
  name `producing_commit` and `cpu_model`; the amendment rewrites the Gate 3 row's "a learned scale
  e^(2s)" as the four local scales actually registered.
