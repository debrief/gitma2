# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–149

150 scenarios, 593 G5 rows (436 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.671 | 65.04 | 7.03 | 1.128 [0.989, 1.272] | — | — | — |
| oracle | 0.057 | 7.28 | 0.85 | 0.097 [0.078, 0.121] | — | — | — |
| imm | 0.595 | 59.95 | 7.34 | — | — | — | — |
| ekf | 0.642 | 61.32 | 5.94 | — | — | — | — |
| C | 0.120 | 16.38 | 1.39 | 0.202 [0.145, 0.265] | 0.898 [0.852, 0.942] | 0.303 | nan |
| C-truthnom | 0.109 | 14.73 | 1.38 | 0.183 [0.132, 0.253] | 0.916 [0.862, 0.953] | 0.280 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.275 | 0.595 | 430 | 0.401 | 22.86 | 20.00 | 19.36 |
| oracle | 0.000 | 0.030 | 593 | 0.057 | 1.64 | 1.61 | 1.64 |
| imm | 0.260 | 0.573 | 439 | 0.440 | 19.09 | 19.75 | 20.03 |
| ekf | 0.223 | 0.589 | 461 | 0.468 | 16.33 | 17.86 | 15.88 |
| C | 0.010 | 0.108 | 587 | 0.117 | 2.68 | 2.84 | 2.99 |
| C-truthnom | 0.002 | 0.094 | 592 | 0.108 | 2.51 | 2.76 | 2.49 |
