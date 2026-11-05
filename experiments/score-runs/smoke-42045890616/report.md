# Segmentation scoring: /home/runner/work/_temp/data/validation.f32pack, ordinals 500–502

3 scenarios, 12 G5 rows (9 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.576 | 77.48 | 11.86 | 0.672 [0.387, 1.132] | — | — | — |
| oracle | 0.119 | 2.12 | 1.90 | 0.138 [0.026, 0.233] | — | — | — |
| imm | 0.857 | 103.13 | 7.77 | — | — | — | — |
| ekf | 0.676 | 74.94 | 11.35 | — | — | — | — |
| naive | 0.486 | 55.35 | 6.93 | 0.566 [0.150, 1.472] | — | — | — |
| C-gap | 0.180 | 16.96 | 3.33 | 0.210 [0.180, 0.551] | 0.865 [0.448, 1.059] | 0.154 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.083 | 0.667 | 11 | 0.576 | 14.06 | 15.89 | 27.25 |
| oracle | 0.000 | 0.000 | 12 | 0.119 | 2.95 | 1.00 | 2.88 |
| imm | 0.083 | 0.833 | 11 | 0.857 | 14.12 | 16.66 | 16.30 |
| ekf | 0.083 | 0.667 | 11 | 0.676 | 18.01 | 12.58 | 17.76 |
| naive | 0.000 | 0.500 | 12 | 0.486 | 18.45 | 13.09 | 10.13 |
| C-gap | 0.000 | 0.250 | 12 | 0.180 | 3.15 | 2.09 | 3.11 |
