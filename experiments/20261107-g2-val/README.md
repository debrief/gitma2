# Gate 2 validation (spec 007 T028)

Seed 314 validation, scoring ordinals 500–1499 (1,000 scenarios, 3,934 G5 rows, 2,933 settled),
every physics-layer solve at 12 knots, C frozen (parameters `60e6ee63…`, code `4d2c084f…`,
hand-over `knot_at_k`). 97.5% scenario-clustered paired bootstrap, 2,000 resamples.

- Training: `g2train/g2-a`, run 42352638177 at 36bfab8 (`results/g2-g2-a-42352638177`).
- Predictions: `g2predict/g2-a-val`, run 42385722106 at d9206ab
  (`results/g2predict-g2-a-val-42385722106`); every file from a clean tree, weights digests as
  trained.
- Scoring: `score/g2-a-val` (`configs/score/g2-a-val.json`, gate mode, split validation), run
  42392768062 at bc2593a (`results/score-g2-a-val-42392768062`). `validation.json`,
  `report.md`, `metrics.json`, `inputs.json`, `plan.json` and `run.json` here are copies;
  `errors.npz` stays on the results branch.
- `models/`: the carried pair's weights and training meta (es-s3, ew-s3).

## Training (best epoch's validation loss on tuning ordinals 0–499)

| Model | Untrained | Best | Best epoch / run | Note |
| --- | --- | --- | --- | --- |
| es-s1 | 52.31 | 50.60 | 4 / 7 | hard decision-row loss |
| es-s2 | 52.31 | 51.11 | 1 / 4 | |
| es-s3 | 52.31 | 51.01 | 3 / 6 | |
| es-shuffled | 52.31 | 52.31 | 0 / 3 | never beat untrained |
| ew-s1 | 38.10 | 36.39 | 8 / 11 | trimmed prefix loss; resumed by train-2 |
| ew-s2 | 38.10 | 36.74 | 2 / 5 | |
| ew-s3 | 38.10 | 36.64 | 3 / 6 | |
| ew-shuffled | 38.10 | 38.10 | 0 / 3 | never beat untrained (trained 44.9–45.5) |

## Results (median range error as a fraction of range unless stated)

| Estimator | Range | Course ° | Speed kt | Range / IMM | Gap recovered | E − C (G2-d) | Rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| One leg | 0.580 | 65.97 | 6.20 | 1.077 | — | — | |
| IMM | 0.539 | 52.32 | 5.79 | — | — | — | |
| C | 0.120 | 15.54 | 1.62 | 0.223 [0.200, 0.247] | 0.890 [0.869, 0.909] | — | |
| **e-s1** | 0.105 | 14.34 | 1.55 | 0.194 [0.175, 0.216] | 0.921 [0.903, 0.936] | +0.030 [+0.018, +0.044] | pass |
| **e-s2** | 0.110 | 14.86 | 1.54 | 0.205 [0.183, 0.226] | 0.910 [0.892, 0.927] | +0.019 [+0.008, +0.033] | pass |
| **e-s3** | 0.106 | 14.48 | 1.54 | 0.197 [0.177, 0.219] | 0.918 [0.900, 0.934] | +0.028 [+0.013, +0.041] | pass |
| e-shuffled | 0.120 | 15.54 | 1.62 | 0.223 | 0.890 | 0.000 [−3e-8, +2e-8] | not passed |
| ew-s1 (reported) | 0.115 | 14.79 | 1.61 | 0.213 | 0.901 | +0.011 [+0.001, +0.021] | pass |
| ew-s2 (reported) | 0.116 | 15.53 | 1.60 | 0.215 | 0.899 | +0.009 [+0.001, +0.018] | pass |
| ew-s3 (reported) | 0.114 | 15.13 | 1.57 | 0.212 | 0.902 | +0.012 [+0.004, +0.023] | pass |
| Oracle | 0.064 | 7.41 | 0.96 | 0.118 | — | — | |

G2-b (settled rows, E / one leg) for e-s3: range 0.175, course 0.145, speed 0.230; every E and
E-w passes G2-a to G2-c with wide margins, as C does.

## Rules (decision record `experiments/20261107-g2-decision/`)

- **Carried seed:** median of e-s1..3 by gap recovered: e-s2 0.9095, e-s3 0.9181, e-s1 0.9207 →
  **e-s3** (`carried.json` beside the decision, weights `a5485318…` = SHA-256 of
  `2b3b9c73…+58b51d10…`).
- **Shuffled rule:** e-shuffled − C wholly above zero? No (the interval contains zero) → **pass**:
  a G2-d pass on test is not voided.
- **Validation rule:** every gated point of e-s3 meets its limit → **pass**: seed 319 is generated
  and E is carried to test (T029).

## Reading

- The forecast was E − C +0.005 [−0.005, +0.015] with a pass probability of about 0.25.
  Validation gives +0.019 to +0.030 on all three seeds, each wholly above zero. The forecast was
  too pessimistic, mainly about E-s: E-w alone gives +0.009 to +0.012, so roughly two thirds of
  E's gain comes from E-s's threshold shifts (the E-w improvement is on C's own segmentation;
  E's is on E-s's).
- The gain is in gross rows more than in the median: rows with range error over 50% fall from
  11.6% (C) to 8.7–9.0% (E), and range efficiency from 2.79 to 2.40–2.49 against the
  known-manoeuvres bound.
- **Caveat: the shuffled control is weak.** Both shuffled components early-stopped at epoch 0,
  so e-shuffled is C to the last bit and its rule passes trivially. That shows training on
  shuffled targets found nothing on the tuning ordinals, which is what the control is for, but it
  says nothing about whether a model that did move under shuffled targets would also have
  "improved" on the scoring rows. The panel should weigh this.
- Validation selected the carried seed and set early stopping on disjoint ordinals (tuning 0–499,
  scoring 500–1499), but the scoring ordinals were also used for C's frozen choices (the
  hand-over, `experiments/20261106-c3-val/`); a fresh test seed is the remedy, and is next.
