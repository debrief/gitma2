# Spec 037 test record: the regressor under bearing-error mismatch (seed 371, scored once)

A registered study, not a gate. Decision record `../20261123-rmis-decision/` (protocol
`beb6af49…`, three addenda), validation `../20261126-rmis-val/`, fine-tunes
`../20261123-ft-runs/`. Test plan `configs/headroom/rm-test-371.json`; CI run 45819634327 at
commit b5aeaf9, 147 jobs, none failed; 1,000 σ = 1° engagements of **test seed 371** per
condition, seven conditions, one scoring run per condition (EPYC 7763 and Xeon 8370C runners;
every comparison is within one scoring job). Scored once.

- `readings.md`, `readings.json`: the registered readings and their outcomes
  (`scripts/research/rmis_readings.py`; the per-row `errors.npz` are on the results branches
  `results/headroom-rm-test-371-<condition>-plan-45819634327`).
- `tables.md`, `summary.json`: every system on every condition
  (`scripts/research/rmis_val_tables.py`).
- Weights: fine-tuned `5ecb77e9…`, `9695333f…`, `e151ac91…`; unchanged `dbf6488d…`,
  `d88c944b…`, `3f75d81d…` (full digests in the plan; each checked in the scoring job).

## The registered readings

| | Reading | Outcome | Forecast (2026-11-23) |
|---|---|---|---|
| M1 | C″-robust ÷ fine-tuned, `all-central`, range | **better**, 1.954 [1.839, 2.074]; course 1.58, speed 1.39 | better, 1.5 to 2.2: held |
| M2 | the same, held-out `ho-both` | **better**, 2.285 [2.133, 2.435]; course 1.72, speed 1.48 | better, 1.2 to 1.9, low confidence: direction held, size under-forecast |
| M3 | unchanged ÷ fine-tuned, same seed | **better**: 1.683 [1.601, 1.778] primary, 1.463 [1.389, 1.543] held out | 1.4 to 2.0 and 1.3 to 1.9: held |
| M4 | unchanged ÷ fine-tuned, clean data | **a cost**: 0.967 [0.949, 0.985]; course 0.980, speed 0.977. Lower limit 0.949 against 0.95 | a cost, 0.92 to 0.98: held |
| M5 | coverage of the stated 95% intervals | **honest** on all nine (three quantities × clean, primary, held out): range 0.939 to 0.964, speed 0.958 to 0.970, course 0.927 to 0.938 where stated | "not honest on held-out": **wrong** |
| M5 | interval score, head ÷ temperature control | **better**: range 0.779 [0.753, 0.807], course 0.913 [0.870, 0.961], speed 0.824 [0.791, 0.861] | better: held |
| Y1 | C″-robust ÷ hybrid | **better**: 1.528 [1.448, 1.618] clean, 1.961 [1.851, 2.070] primary; course 1.40, 1.65; speed 1.27, 1.52 | 1.2 to 1.5 and 1.2 to 1.6: direction held, size under-forecast |
| Y2 | fine-tuned ÷ hybrid | range **not separated** (1.021 [0.999, 1.044], 1.003 [0.985, 1.023]); course 1.22 and 1.05, speed 1.23 and 1.10: the hybrid is **better** | "below 1 in range": **wrong** |
| | hybrid harm on clean data | **none** | |

Three seeds agree to the second decimal in every reading (for example M1 by seed 1.94, 1.95,
1.97).

## What the readings mean, and what they do not

- **In the training ranges and outside them, the fine-tuned regressor halves the classical
  system's range error under these simulated bearing errors.** M2's kinds (a sinusoidal error,
  bursts with a common offset) were never drawn in training or tuning; they are still this
  simulator's. Reported conditions agree: outliers 2.07, correlated error 1.70, the two held-out
  kinds alone 2.35 and 1.71.
- **The fine-tune costs about 3% on clean data.** M4's interval is wholly below 1 and its lower
  limit is 0.949 against the registered 0.95: a cost by the rule, and a small one.
- **On clean data the fine-tuned model is behind the solve told the true manoeuvre times**
  (0.890 [0.838, 0.943] in range; course 0.74, speed 0.68), and its lead over C″ is small at
  near range (1.11 [1.00, 1.24] in the nearest third, 1.91 in the farthest). Under mismatch it
  is level with that reference in range and behind in course and speed (0.75 to 0.84). The
  reference is told the manoeuvre times and is not attainable.
- **The hybrid keeps the gain and reports from the physics layer.** It is level with the
  regressor in range and better in course and speed, on clean data most (1.22, 1.23). The
  static range-prior comparator explains none of it (C″-robust ÷ C″ with a static prior 1.01
  and 1.04; comparator ÷ hybrid 1.52 and 1.88): the gain is the regressor's information, not
  shrinkage toward a usual range. Every hybrid row used its prior (3,936 of 3,936 on clean
  data), so there were no constructed ties to exclude.
- **The intervals cover as stated on all three conditions**, with scales fitted on validation's
  clean and primary rows only, and they beat a per-range-band constant width. Course carries
  an interval on 63% to 80% of rows; elsewhere the model says "undetermined". The normalised
  error for course is 0.6 to 0.7: the arc covers 95% by being wide in the middle of its
  distribution, so the course error is not Gaussian in shape and the arc is a statement of
  coverage, not of spread.

## Limits known at registration, and found since

- The regressor was trained on this simulator's manoeuvre statistics and error family; C″ is
  told neither. A win over C″ is a win of a prior-informed estimator.
- The seven conditions are the same 1,000 engagements under different errors.
- Median range error per engagement over five scored rows; the IMM, the EKF and one leg answer
  73% to 81% of rows and are compared on rows they answer.
- Efficiency under held-out conditions is against a bound that does not describe the held-out
  kinds (so the 4 to 6 in course there is not comparable with the other rows).
- The fine-tunes were interrupted and resumed (addendum 2); the readings code changed after
  registration by additions recorded in addenda 1 and 3; the pooled same-seed readings are
  computed after the run from its stored errors.
- M5's bootstrap resamples engagements across conditions and seeds together.

## Promised and not run

- Readings by time since the last target change, and by whether the first bearing is an
  outlier (research R8).
- A refusal in the workflow for a second test scoring (the test was launched once, by hand).
- The hybrid on the held-out condition (it was registered on clean and primary only).
- Quantile or mixture heads (the existing variance head was used, research R1).
- Full unit-test suite run on the final tree (the spec's own tests and their neighbours pass).

## Money

About $46.75 of the owner's $50 (`../20261123-ft-runs/`); the ledger undercounts by about $3.50.
