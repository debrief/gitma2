# Gate D decision record

`experiments/<date>-gd-decision/decision.json` (a `GateDDecision`), committed before the plan
branch is pushed. Before registration, each validation check and control is checked against the
detector's architecture (FR-035) and the check is recorded in the record's notes: a check that
every physics-layer model passes or fails by construction is not used.

It fixes:

- the plan id and SHA-256; the carried variants (causal, time-late) with three seeds each; the
  classification-only control;
- D1: operating threshold 0.5 on `p_change`, tolerance ±60 s; the knot export threshold (0.5);
- D2: both variants carried, intervals at 97.5%;
- D3: the held-leg false-alarm limit, 5%, or the frozen IMM's own rate on validation if lower;
- D4: test seed 305 (100,000 generated, the 10% split scored once), validation seed 304, training
  stream 311;
- the held-leg weighting (3) and the loss weights;
- the carried rule (median seed by validation D-downstream-all);
- the controls' tuning rule (threshold matched to the carried variant's validation held-leg
  false-alarm fraction), and the frozen IMM and EKF settings from `tma2-tune --criterion g5`;
- Gate D's checks and the validation rule exactly as Annex A §A.5;
- the follow-on of Annex A §A.6;
- a forecast, and the bootstrap level (0.975) and resamples (2,000).

The control thresholds are tuned after training on validation and recorded as an amendment by
digest before the test split is generated; that amendment changes no criterion.
