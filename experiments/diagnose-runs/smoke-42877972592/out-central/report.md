# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–2

3 scenarios, 12 G5 rows (6 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.543 | 46.61 | 5.75 | 0.776 [0.343, 1.021] | — | — | — |
| oracle | 0.064 | 19.04 | 0.50 | 0.091 [0.034, 0.200] | — | — | — |
| imm | 0.700 | 67.04 | 3.95 | — | — | — | — |
| ekf | 0.630 | 32.56 | 5.38 | — | — | — | — |
| C | 0.142 | 40.33 | 2.33 | 0.203 [0.114, 0.730] | 0.836 [0.324, 0.936] | 0.467 | nan |
| C-truthnom | 0.142 | 22.46 | 0.50 | 0.203 [0.109, 0.730] | 0.836 [0.332, 0.960] | 0.467 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.083 | 0.667 | 11 | 0.543 | 8.70 | 2.04 | 28.42 |
| oracle | 0.000 | 0.083 | 12 | 0.064 | 2.03 | 1.40 | 3.11 |
| imm | 0.083 | 0.833 | 11 | 0.700 | 10.79 | 4.20 | 16.35 |
| ekf | 0.000 | 0.833 | 12 | 0.630 | 14.85 | 5.36 | 23.07 |
| C | 0.000 | 0.333 | 12 | 0.142 | 4.85 | 1.67 | 12.35 |
| C-truthnom | 0.000 | 0.167 | 12 | 0.142 | 4.85 | 1.67 | 8.48 |
