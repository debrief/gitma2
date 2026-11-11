# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–149

150 scenarios, 593 G5 rows (436 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.677 | 68.58 | 7.27 | 1.109 [0.970, 1.290] | — | — | — |
| oracle | 0.111 | 11.87 | 1.39 | 0.182 [0.131, 0.239] | — | — | — |
| imm | 0.610 | 59.11 | 5.87 | — | — | — | — |
| ekf | 0.627 | 59.53 | 5.94 | — | — | — | — |
| C | 0.214 | 21.46 | 2.31 | 0.350 [0.255, 0.460] | 0.819 [0.736, 0.890] | 0.323 | nan |
| C-truthnom | 0.188 | 20.47 | 2.15 | 0.308 [0.216, 0.423] | 0.864 [0.781, 0.940] | 0.311 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.277 | 0.607 | 429 | 0.418 | 23.22 | 20.43 | 19.78 |
| oracle | 0.000 | 0.054 | 593 | 0.111 | 2.73 | 3.02 | 2.84 |
| imm | 0.250 | 0.568 | 445 | 0.430 | 17.71 | 20.86 | 14.78 |
| ekf | 0.221 | 0.595 | 462 | 0.450 | 15.79 | 17.13 | 14.69 |
| C | 0.002 | 0.201 | 592 | 0.213 | 4.85 | 4.49 | 4.54 |
| C-truthnom | 0.005 | 0.185 | 590 | 0.185 | 4.49 | 4.27 | 4.25 |
