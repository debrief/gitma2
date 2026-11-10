# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–149

150 scenarios, 593 G5 rows (436 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.663 | 65.47 | 7.29 | 1.148 [1.022, 1.347] | — | — | — |
| oracle | 0.070 | 9.00 | 1.06 | 0.121 [0.096, 0.154] | — | — | — |
| imm | 0.578 | 63.47 | 7.14 | — | — | — | — |
| ekf | 0.649 | 58.39 | 6.13 | — | — | — | — |
| C | 0.128 | 15.16 | 1.66 | 0.221 [0.173, 0.297] | 0.902 [0.851, 0.936] | 0.310 | nan |
| C-truthnom | 0.117 | 14.45 | 1.48 | 0.203 [0.150, 0.270] | 0.920 [0.879, 0.961] | 0.298 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.277 | 0.597 | 429 | 0.417 | 22.28 | 22.02 | 19.72 |
| oracle | 0.000 | 0.039 | 593 | 0.070 | 1.88 | 2.14 | 1.99 |
| imm | 0.261 | 0.546 | 438 | 0.386 | 16.71 | 20.03 | 19.11 |
| ekf | 0.223 | 0.589 | 461 | 0.474 | 16.38 | 17.52 | 15.14 |
| C | 0.005 | 0.123 | 590 | 0.127 | 2.83 | 3.02 | 3.20 |
| C-truthnom | 0.000 | 0.103 | 593 | 0.117 | 2.71 | 2.65 | 2.70 |
