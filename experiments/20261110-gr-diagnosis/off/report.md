# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–149

150 scenarios, 593 G5 rows (436 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.671 | 64.97 | 7.08 | 1.172 [1.013, 1.352] | — | — | — |
| oracle | 0.061 | 7.59 | 0.85 | 0.106 [0.082, 0.138] | — | — | — |
| imm | 0.572 | 59.40 | 6.99 | — | — | — | — |
| ekf | 0.647 | 59.84 | 5.90 | — | — | — | — |
| C | 0.131 | 14.73 | 1.43 | 0.229 [0.162, 0.301] | 0.884 [0.835, 0.932] | 0.313 | nan |
| C-truthnom | 0.114 | 13.78 | 1.25 | 0.200 [0.146, 0.274] | 0.912 [0.858, 0.950] | 0.281 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.273 | 0.595 | 431 | 0.400 | 22.42 | 19.25 | 19.37 |
| oracle | 0.000 | 0.029 | 593 | 0.061 | 1.59 | 1.68 | 1.65 |
| imm | 0.261 | 0.545 | 438 | 0.400 | 17.62 | 19.26 | 18.82 |
| ekf | 0.216 | 0.592 | 465 | 0.472 | 16.19 | 17.65 | 14.95 |
| C | 0.008 | 0.110 | 588 | 0.130 | 2.90 | 2.85 | 2.93 |
| C-truthnom | 0.003 | 0.098 | 591 | 0.114 | 2.60 | 2.54 | 2.51 |
