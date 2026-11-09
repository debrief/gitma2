# Gate 4 decision record (spec 009 T012)

`decision.json` (a `Gate4Decision`) is committed before any statement training on CI and before
test seed 320 is generated. It binds `configs/gate4/g4-a.json` by SHA-256 (`plan_digest`
`e357f8a7…`); the plan is never edited after this. Later additions are new files here
(`carried.json` after validation, `test-digest.json` after seed 320). None may change a criterion
once any test result exists.

## Fixed here

- **The SRD:** §5 Gate 4 row as proposed on this branch (owner to merge; the agent merges after
  two working days without objection, `AGENTS.md`). The criteria below are the row's.
- **The carried estimator:** Gate 2's E, e-s3 (weights `a5485318…`), frozen; the statement adds
  fields to its rows and copies its points (G4-e checks it exactly).
- **The statement** (research R2–R4, R6): course arc X = min(45°, 1.96 · a · sd) with
  P = p · P_vm(±X) + (1 − p) · X/π mapped through an isotonic map fitted on the tuning rows;
  range and speed 95% half-widths c · sd. Head: width 32, outputs bounded at e^(±2) (p on the logit
  scale) around the global statement fitted on the training stream, loss the standardised sum of
  the course log score and the two interval scores on exact errors; Adam 1e-3, 1,024 rows per
  batch, at most 50 epochs, patience 5, early stopping on validation tuning ordinals 0–499. Three
  seeds (st-s1..s3) and a shuffled control (seed 4; errors permuted across rows each epoch).
- **The classical control:** a per-cell temperature (G5 minute × open at k) stated on sd^β, β per
  quantity from the grid 1.0…0.3 chosen inside the fit on the tuning rows (research R3a: with the
  plain sd the shuffled head beat it in sample, so the control would have been a strawman), with
  its own isotonic map.
- **Inputs:** E's feature caches over the training stream (seed 318,
  `results/g2predict-g3-feat-stream-42472098077`, 39,054 rows) and validation 0–1499
  (`results/g2predict-g3-feat-val-42472096319`); E's validation prediction file with covariances
  (`results/g2predict-g3-base-val-42471500526`).
- **Criteria** (`decision.json`, SRD row): G4-a range and speed coverage95 each wholly in
  [0.92, 0.98]; G4-b hit − P wholly within ±0.03 and each of five bins within ±0.05 (point);
  G4-c course log gain over the uniform wholly above 0 and mean P ≥ 0.5; G4-d head − temperature
  standardised summed score wholly below 0 (each component divided by the temperature's mean on
  the scored rows), void by the shuffled rule; G4-e points identical. 97.5% scenario-clustered
  bootstrap, 2,000 resamples, scored by `tma2-g4` from one scoring run's stored arrays.
- **Rules:** carried seed (median validation summed score), shuffled (best and last epoch, as
  distinct models), validation, as in `decision.json`.
- **Test seed 320,** generated only after `carried.json`, `--count 100000`; its digests go to
  `test-digest.json` here, and the test scoring must cover every σ = 1° scenario.

## Evidence for the forecast

Validation baseline (`experiments/20261108-g4-base-val/`, scoring rows, raw E's sds as the
statement) and tuning rows 0–499 (in sample, `scripts/research/g4_tuning.py`):

| | Mean P | Hit − P | Course log gain | Cov95 log range | Cov95 speed |
| --- | --- | --- | --- | --- | --- |
| E raw (scoring rows) | 0.904 | −0.396 | −2.59 | 0.598 | 0.647 |
| Per-slice temperature (tuning rows) | 0.602 | +0.006 | ≈ +1.0 | 0.95 by construction | 0.95 by construction |

Standardised summed score on the tuning rows: plain temperature 3.08, shuffled head 2.85,
sd^β temperature 2.66, head 2.46 (st-s1, best epoch 29).

## Forecast

G4-a pass 0.7, G4-b 0.5, G4-c 0.8, G4-d 0.4, G4-e 1.0; overall about 0.15. The most likely
failure is G4-b's ±0.03 overall band or G4-d out of sample.

## Addendum (2026-11-09, after validation; panel round 1): a trial training before this record

Before this record was committed, two models were trained locally as a design trial on the tuning
rows (st-s1 and st-shuffled, commit 9e8c7d4 with a dirty tree and an earlier plan digest
448cbce9; `scratchpad/g4ck/`, not committed). Their in-sample numbers (head 2.46, shuffled 2.85,
plain temperature 3.08) are the ones quoted above and drove the sd^β redesign of the temperature
(research R3a). Training is deterministic, so CI's st-s1 best weights after this record are
byte-identical to the trial's (`601c820b…`): the registered st-s1 is a rerun of a model that
already existed, not a model first trained after the record. Nothing was scored on validation
ordinals 500–1499 by any stated estimator before this record other than the raw-E baseline
(T009, whose statement is its own sds) (the trial and the β choice used
ordinals 0–499 only); constitution IV allows validation exploration, and the change made the
classical control stronger. Neither the criteria nor the plan changed.
