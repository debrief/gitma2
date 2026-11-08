# Gate 3 decision record (spec 008 T018)

`decision.json` (a `Gate3Decision`) is committed before any calibration training and before test
seed 320 is generated. It binds `configs/gate3/g3-a.json` by SHA-256 (`plan_digest` `fdf7987e…`),
which is never edited after this. Later changes are amendments: new files here (`carried.json`
after validation, `test-digest.json` after seed 320 is made). None may change a criterion once
any test result exists.

## Fixed here

- **The SRD:** §5 Gate 3 row (PR 18, merged by the owner, 2026-11-08) with G3-b as amended by the
  owner the same day, before any result (PR 19): the share of rows within the χ²₄ 95% NEES point.
- **The carried estimator:** Gate 2's E, e-s3 (weights `a5485318…`), frozen. Calibration changes
  its covariance only; its points are copied (G3-d checks it exactly).
- **The calibration** (research R5–R8, as amended): `form: local`, four log-scales (log range,
  bearing, speed, course), bound 4, on E-w's encoder state at the row, the raw log sds and C's
  code; β-NLL, β = 0.5, raw NEES capped at 10⁴; width 32; Adam 1e-3, 1,024 rows per batch, at most
  50 epochs, patience 5. Three seeds (cal-s1..s3) and a shuffled control (seed 4).
- **The classical control:** a local temperature per cell of (G5 minute × open at k), the same
  loss, fitted on validation tuning ordinals 0–499.
- **Inputs:** E's feature caches over the training stream (seed 318, `results/g2predict-g3-feat-stream-42472098077`,
  39,054 rows) and validation 0–1499 (`results/g2predict-g3-feat-val-42472096319`); E's validation
  prediction file with covariances (`results/g2predict-g3-base-val-42471500526`).
- **Test seed 320,** generated after `carried.json` with `--count 100000`, as Gate 2; its digests
  go to `test-digest.json` here, and a test scoring must cover every σ = 1° scenario (FR-032).
- **Criteria** (`decision.json`): G3-a coverage95 of log range, course and speed each wholly in
  [0.92, 0.98]; G3-b the share within the χ²₄ 95% NEES point wholly in [0.92, 0.98]; G3-c the
  head's interval score in log range minus the temperature's wholly below 0, void by the
  shuffled rule; G3-d point errors identical to E's. 97.5% scenario-clustered paired bootstrap,
  2,000 resamples. Scored by `tma2-g3` from one scoring run's stored arrays.
- **Rules:** carried seed (median validation interval score), shuffled (best and last epoch),
  validation, as in `decision.json`.

## Evidence for the forecast

From `experiments/20261108-g3-base-val/` and a local temperature fitted in sample on the tuning
rows (0–499, 1,971 rows; linearised errors):

| | Cov95 log range | Cov95 course | Cov95 speed | Within χ²₄ 95% | Median NEES ratio |
| --- | --- | --- | --- | --- | --- |
| E raw (scoring rows) | 0.598 | 0.532 | 0.647 | 0.330 | 6.65 |
| Local temperature, cap 10⁴ (tuning rows) | 0.965 | 0.926 | 0.960 | 0.794 | 0.18 |

The marginal coverages can be reached; the joint 4-state share cannot by a per-cell scale, because
the tails come from rows where segmentation or a manoeuvre went wrong, and those differ within a
cell. The head can only pass G3-b if it tells those rows apart.

## Forecast

G3-a pass 0.4 (course binding), G3-b 0.15, G3-c 0.5, G3-d 1.0; overall about 0.1. The most likely
outcome is G3-b failed on validation, in which case seed 320 is not generated and the write-up
proposes a heavy-tailed predictive as the follow-on.
