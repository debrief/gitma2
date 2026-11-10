# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–2

3 scenarios, 12 G5 rows (6 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.674 | 46.60 | 5.75 | 0.955 [0.345, 1.962] | — | — | — |
| oracle | 0.050 | 19.40 | 0.47 | 0.071 [0.034, 0.225] | — | — | — |
| imm | 0.706 | 66.85 | 4.29 | — | — | — | — |
| ekf | 0.649 | 29.72 | 5.69 | — | — | — | — |
| C | 0.169 | 34.67 | 0.93 | 0.239 [0.105, 0.239] | 0.810 [0.338, 1.063] | 0.467 | nan |
| C-truthnom | 0.065 | 28.89 | 1.26 | 0.092 [0.016, 0.178] | 0.976 [0.976, 1.063] | 0.467 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.083 | 0.667 | 11 | 0.674 | 8.58 | 2.01 | 28.39 |
| oracle | 0.000 | 0.083 | 12 | 0.050 | 1.80 | 1.32 | 3.23 |
| imm | 0.083 | 0.917 | 11 | 0.706 | 10.83 | 4.09 | 12.00 |
| ekf | 0.000 | 0.917 | 12 | 0.649 | 15.58 | 5.51 | 27.62 |
| C | 0.000 | 0.083 | 12 | 0.169 | 4.16 | 7.71 | 4.44 |
| C-truthnom | 0.000 | 0.083 | 12 | 0.065 | 1.59 | 1.65 | 4.56 |
