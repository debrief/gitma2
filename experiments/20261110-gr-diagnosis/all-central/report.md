# Segmentation scoring: /home/runner/work/_temp/data/train.f32pack, ordinals 0–149

150 scenarios, 593 G5 rows (436 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.692 | 68.48 | 7.55 | 0.942 [0.857, 1.053] | — | — | — |
| oracle | 0.133 | 13.07 | 1.77 | 0.181 [0.148, 0.238] | — | — | — |
| imm | 0.734 | 73.56 | 8.91 | — | — | — | — |
| ekf | 0.657 | 62.25 | 6.21 | — | — | — | — |
| C | 0.306 | 34.79 | 3.06 | 0.417 [0.326, 0.565] | 0.690 [0.539, 0.798] | 0.344 | nan |
| C-truthnom | 0.277 | 33.61 | 2.92 | 0.377 [0.298, 0.509] | 0.743 [0.616, 0.827] | 0.333 | nan |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.287 | 0.614 | 423 | 0.427 | 23.89 | 23.50 | 19.96 |
| oracle | 0.000 | 0.071 | 593 | 0.133 | 3.09 | 3.29 | 3.49 |
| imm | 0.324 | 0.622 | 401 | 0.420 | 22.20 | 29.04 | 25.69 |
| ekf | 0.224 | 0.602 | 460 | 0.487 | 18.45 | 18.05 | 15.02 |
| C | 0.002 | 0.302 | 592 | 0.306 | 7.48 | 7.46 | 6.03 |
| C-truthnom | 0.000 | 0.292 | 593 | 0.277 | 6.76 | 6.81 | 5.45 |
