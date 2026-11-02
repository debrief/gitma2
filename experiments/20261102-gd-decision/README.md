# Gate D decision record (spec 004 T022)

`decision.json` (a `GateDDecision`) is committed before the plan branch `train/gd-a` is pushed;
`tma2-gd` refuses any checkpoint whose training commits do not descend from this record's first
commit. It binds `configs/gate-d/plan.json` by SHA-256.

Inputs fixed here:

- frozen references from `experiments/20261102-gd-tune/` (IMM `imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16`,
  EKF `ekf-sa0.03-p4-r8`);
- D3: the frozen IMM's held-leg G5 false-alarm fraction at μ_CT > 0.5 on validation seed 304 is
  21 / 7,620 = 0.27559%, below 5%, so the D-false limit is 0.27559% (Annex A §A.8 D3), measured
  with `tma2.cli.controls.statistic` (kind `imm_mode`, threshold 0.5) over every σ = 1° held-leg G5
  row of the 10,000-scenario validation split;
- runner throughput (T021): 29 ms per scenario for the carried detectors, so no R5 lever is used;
- the architecture check (FR-035) is in the record's `architecture_check`.

Control thresholds are tuned after training on validation and recorded as an amendment by digest
before the test split (seed 305) is generated; the amendment changes no criterion.
