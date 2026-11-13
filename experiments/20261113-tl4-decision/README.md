# Spec 016 (study L): decision record (2026-11-13)

Written after the tuning run on seed 338 (`experiments/20261113-tl4-tuning/`) and the
throughput pilot (`experiments/20261113-tlm-pilot/`), **before any training run of the
learned model and before seeds 340 and 341 exist**. `decision.json` binds the plan
(`configs/timelate/tl-e.json`, `82cd70ee…`), the ranges, the training mix, the three
training plans, the time-late code (`e5040f5e…`) and the scoring files by SHA-256, and
states the criteria, the order of events, the power and the forecasts. Owner decision:
2026-11-13, option B. SRD §5 row "Study L" (proposed; the owner merges).

## What is compared

- **The standing search** (`search3`): spec 015's, Annex B's prior, the bearings as given.
- **The classical control** (`ctl`): wild bearings edited out; an effective bearing sd from
  the estimated error correlation (used above a share of 0.2); searches under Annex B's
  prior and a broadened one, pooled. Reported as a declared history (margin 1, quiet
  probability 0.01: `ctl-d1-q0.01`) and as a hedged track (temperature 1: `ctl-h1`).
  Nothing trained; settings from tuning seed 338; not told the conditions.
- **The learned model**: three seeds, 12.5 million simulated periods each (65% Annex B,
  20% randomised manoeuvre statistics, 15% quiet; a quarter with correlated errors,
  outliers or both; no bias). Reported track: the arc model fitted from its output
  (`learned-sK-arc`); its direct track beside.

## Criteria

- **L-a** soundness on validation (controls only); a failure stops the study.
- **L-b** what the controls close, reported.
- **L-c** on five mismatch splits: learning *shown* only if every seed beats both the
  declared control and the hedged track; *hedging* if only the declared one.
- **L-d** *harm* on Annex B or held-course periods if every seed loses to the control.
- Shown on two or more splits without harm: a gate is proposed. On none: the classical
  controls stand and the learned track stops. Otherwise the owner decides.

No materiality line is registered. Each comparison is a sign test against 1 with an
interval; the size is reported with it. From tuning data a learned track must differ from
the control by about 15% to 40% (by split) to be separated at the test sizes.

## Forecasts (written before any training result)

- L-a passes.
- The control beats the standing search by about 1.5 with outliers and 1.3 with correlated
  errors, and barely under the first shifted prior.
- **Learning is most likely shown on no split.** The shifted prior is the one place with
  room; about one chance in four there.
- **Harm on Annex B data is more likely than not for the model's own track**: at this
  budget the model is unlikely to match a fit that knows the exact motion model. The arc
  read-out should narrow that.
- If these hold, the result is "the classical controls stand", at a budget of $18 of GPU
  time; it would not show that a larger model or more data could not do better.

## Order of events, enforced

1. This record is committed.
2. The three training runs start (plans bound here; the ledger refuses past its cap).
3. The controls' validation runs on seed 340 (`tl-e-val`), with no learned track; L-a is
   read and the record committed.
4. An addendum names the trained seeds' results branches and the validation record in the
   test run file.
5. The test runs on seed 341 once. The scorer refuses a learned track without step 3's
   record.

## Known limits

Listed in `decision.json`: the unrepaired evidence faults at the prior's support edges; the
correlated-error control is an effective sd and knows the error family; only editing is
built as a robust form; the training budget; the ledger's under-count on restarts.
