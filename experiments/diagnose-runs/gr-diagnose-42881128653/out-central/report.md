# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–149

150 scenarios, 593 G5 rows (436 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.669 | 65.00 | 7.34 | 0.956 [0.884, 1.140] | — | — | — |
| oracle | 0.074 | 8.09 | 1.11 | 0.106 [0.086, 0.147] | — | — | — |
| imm | 0.700 | 64.67 | 7.96 | — | — | — | — |
| ekf | 0.647 | 59.86 | 5.97 | — | — | — | — |
| C | 0.236 | 27.18 | 2.70 | 0.338 [0.265, 0.485] | 0.728 [0.600, 0.807] | 0.300 | nan |
| C-truthnom | 0.218 | 25.55 | 2.53 | 0.312 [0.249, 0.449] | 0.758 [0.639, 0.828] | 0.268 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.270 | 0.600 | 433 | 0.434 | 22.59 | 20.34 | 19.23 |
| oracle | 0.000 | 0.034 | 593 | 0.074 | 1.89 | 2.13 | 2.24 |
| imm | 0.307 | 0.585 | 411 | 0.401 | 22.25 | 21.52 | 23.53 |
| ekf | 0.214 | 0.589 | 466 | 0.457 | 16.23 | 16.82 | 15.04 |
| C | 0.002 | 0.270 | 592 | 0.233 | 5.72 | 5.09 | 4.85 |
| C-truthnom | 0.002 | 0.261 | 592 | 0.218 | 5.15 | 5.11 | 4.59 |
