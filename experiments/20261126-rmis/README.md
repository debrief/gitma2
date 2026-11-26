# Spec 037 test record: the regressor under bearing-error mismatch (seed 371, scored once)

A registered study, not a gate. Decision record `../20261123-rmis-decision/` (protocol
`beb6af49…`, three addenda), validation `../20261126-rmis-val/`, fine-tunes
`../20261123-ft-runs/`. Test plan `configs/headroom/rm-test-371.json`; CI run 45819634327 at
commit b5aeaf9, 147 jobs, none failed; 1,000 σ = 1° engagements of **test seed 371** per
condition, seven conditions, one scoring run per condition (four CPU families across the
conditions: EPYC 7763, Xeon 8370C, EPYC 9V74, EPYC 9V45; every comparison is within one
scoring job). Scored once. **Reviewed by the panel, round 1: three approve with findings
(`review.md`); this text is as narrowed by them.**

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
| M2 | the same, `ho-both` (kinds not in the training mix; see below) | **better**, 2.285 [2.133, 2.435]; course 1.72, speed 1.48 | better, 1.2 to 1.9, low confidence: direction held, size under-forecast |
| M3 | unchanged ÷ fine-tuned, same seed | **better**: 1.683 [1.601, 1.778] primary, 1.463 [1.389, 1.543] held out | 1.4 to 2.0 and 1.3 to 1.9: held |
| M4 | unchanged ÷ fine-tuned, clean data | **a cost of about 3%**: 0.967 [0.949, 0.985]; course 0.980, speed 0.977. The "no cost" clause (lower limit at least 0.95) is not resolved: the limit is 0.9496 and about a fifth of bootstrap seeds put it above | a cost, 0.92 to 0.98: held |
| M5 | coverage of the stated 95% intervals | **honest by the registered check** (on average) on all nine (three quantities × clean, primary, held out): range 0.939 to 0.964, speed 0.958 to 0.970, course 0.927 to 0.938 where stated | "not honest on held-out": **wrong** |
| M5 | interval score, head ÷ temperature control | **better**: range 0.779 [0.753, 0.807], course 0.913 [0.870, 0.961], speed 0.824 [0.791, 0.861] | better: held |
| Y1 | C″-robust ÷ hybrid | **better**: 1.528 [1.448, 1.618] clean, 1.961 [1.851, 2.070] primary; course 1.40, 1.65; speed 1.27, 1.52 | 1.2 to 1.5 and 1.2 to 1.6: direction held, size under-forecast |
| Y2 | fine-tuned ÷ hybrid | range **not separated** (1.021 [0.999, 1.044], 1.003 [0.985, 1.023]); course 1.22 and 1.05, speed 1.23 and 1.10: the hybrid is **better** | "below 1 in range": **wrong** |
| | hybrid harm on clean data | **none** | |

The three seeds agree closely: M1 by seed 1.94, 1.95, 1.97; M2 2.34, 2.27, 2.24; M4 0.974,
0.971, 0.957.

## What the readings mean, as the panel narrowed them

- **The gain is real, typical and sits where C″'s segmentation has failed.** M1 and M2 are not
  tails (median per-engagement ratio 1.92 and 2.23; one row in seven is twice as bad). But a
  classical robust solve told the true manoeuvre times equals the regressor in range on every
  condition (0.89 clean, 1.03 primary, 0.96 held out) and beats it in course and speed (0.68 to
  0.84). The factor of two is the gap between C″-robust (0.233) and that solve (0.116): the
  segmentation gap of specs 010 and 011. Where C″'s segmentation holds (its best quartile, split
  on other rows) the regressor is 1.15 to 1.43 better in range under mismatch and not separated
  in course or speed; where it fails, 2.7 to 3.3. On clean data, where C″ is right, the
  regressor is worse than C″ in course and speed. A lead of 1.49 exists on clean data already.
- **"Held out" is a weak form.** The spec's default held-out family hurt nobody and was replaced
  before registration by a sinusoid and bursts, after the unchanged model was seen to be hurt
  by them and the pilot model to recover. Their statistics lie inside what training covered;
  only the line spectrum and the clustering are new. M2 is "kinds not in the training mix,
  chosen because they hurt", and is biased towards the regressor. It is not evidence of
  robustness to unseen errors.
- **Prior or bearings is still open.** The regressor knows this simulator's manoeuvre
  statistics, geometry and error family; C″ is told none. Where the bound is loose its
  efficiency is below 1 (0.61 in range under the primary condition), which is prior, not
  bearings; where the bound is tight on clean data it is worse than C″ in course and speed.
  The static range-prior comparator (1.01 and 1.04 against C″-robust) was too loose to move
  the solve and rules out only a constant.
- **The fine-tune costs about 3% on clean data**, as a tail (median ratio 0.989) and under
  about 22 km (near third 0.954, far third 0.995).
- **The hybrid is the regressor's range with a classical velocity refit.** Level with the
  regressor in range (1.02, 1.00) and better in course and speed by geometric mean (1.22 and
  1.23 clean; 1.05 and 1.10 primary), but by median only 1.04 to 1.06: a minority of
  engagements. At weight 0.25 the prior carries nearly all of the range information and the
  bearings are counted twice, so "reports from the physics layer" holds in letter only and the
  layer's covariance must not be shown. It is worse than the regressor in the far third on
  clean data (0.955) and inherits the regressor's losses where C″ was right. No hybrid row fell
  back to C″ (`hybrid-ties.json`), so there were no constructed ties.
- **The intervals cover on average, not conditionally.** Course covers 0.78 to 0.79 on
  unsettled rows and 0.97 to 0.98 on settled ones; the narrowest fifth of speed intervals
  covers 0.92 to 0.94; the nearest 5% of ranges 0.885 under the primary condition. Rows with no
  stated course (20% to 37%) are the hard ones (median error 29°). The course head is not
  separated from the constant-width control on the held-out condition (0.986 [0.930, 1.047]).
  A variance head trained on the generating distribution covers there by construction. These
  intervals are not ready to be shown.

## Limits

- One simulator; the seven conditions are the same 1,000 engagements under different errors;
  one bearing sd (1°).
- No prior-informed or mismatch-hardened classical segmenter was registered as a control, so
  "beats the classical system" means "beats C, frozen since Gate 2".
- Median range error per engagement over four scored rows (3,936 rows: 942 engagements with
  four, 52 with three, 6 with two); the IMM, the EKF and one leg answer 73% to 81% of rows and
  are compared on rows they answer.
- Efficiency under held-out conditions is against a bound that does not describe the held-out
  kinds.
- The fine-tunes were interrupted and resumed (addendum 2; patch offsets are reseeded at each
  segment, so the weights are not an uninterrupted run's). Validation seed 370 was also the
  training monitor's seed (logged only). The readings script was committed with this record,
  not before the launch; the scoring code is bound by the test's commit only. The hybrid's
  weight was chosen on one training seed.

## Promised and not run

- Readings by time since the last target change, and by whether the first bearing is an
  outlier (research R8).
- A refusal in the workflow for a second test scoring (the test was launched once, by hand).
- The hybrid on the held-out condition (it was registered on clean and primary only).
- Quantile or mixture heads (the existing variance head was used, research R1).
- The spec's default held-out family (Student-t noise, a level step) on the test; the hybrid
  started from the regressor's estimate (addendum 1); validation early stopping; comparisons on
  rows every system answers, with counts; a prior-informed classical control.
- Full unit-test suite run on the final tree (the spec's own tests and their neighbours pass).

## What follows

The panel's order (`review.md`), the owner's choice: a prior-informed classical control and a
decomposition of the gain into prior and bearings, on CPU with nothing trained (recommended);
a conditional coverage study; only then the hybrid as a provisional real-time candidate; no
further GPU spending.

## Money

About $46.75 of the owner's $50 (`../20261123-ft-runs/`); the ledger undercounts by about $3.50.
