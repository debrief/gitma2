# Segmentation scoring: /home/runner/work/_temp/data/validation.f32pack, ordinals 500–1499

1000 scenarios, 3934 G5 rows (2933 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.581 | 65.97 | 6.20 | 1.079 [1.022, 1.135] | — | — | — |
| oracle | 0.064 | 7.41 | 0.96 | 0.118 [0.106, 0.131] | — | — | — |
| imm | 0.539 | 52.32 | 5.79 | — | — | — | — |
| ekf | 0.498 | 57.45 | 5.20 | — | — | — | — |
| naive | 0.410 | 88.77 | 4.04 | 0.761 [0.689, 0.835] | — | — | — |
| C | 0.120 | 15.54 | 1.62 | 0.223 [0.200, 0.247] | 0.890 [0.869, 0.909] | 0.282 | 0.083 |
| glr_confirm | 0.447 | 44.39 | 4.57 | 0.830 [0.758, 0.925] | 0.259 [0.157, 0.333] | 0.289 | 0.083 |
| glr_confirm_gap | 0.453 | 43.88 | 4.10 | 0.841 [0.750, 0.945] | 0.248 [0.140, 0.346] | 0.289 | 0.083 |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.232 | 0.558 | 3020 | 0.414 | 15.45 | 19.43 | 13.76 |
| oracle | 0.000 | 0.023 | 3933 | 0.064 | 1.55 | 1.76 | 1.76 |
| imm | 0.225 | 0.531 | 3047 | 0.392 | 13.20 | 15.53 | 13.67 |
| ekf | 0.188 | 0.500 | 3196 | 0.363 | 11.65 | 14.53 | 11.25 |
| naive | 0.000 | 0.395 | 3934 | 0.410 | 8.18 | 21.73 | 6.33 |
| C | 0.006 | 0.116 | 3911 | 0.120 | 2.79 | 2.98 | 2.72 |
| glr_confirm | 0.203 | 0.475 | 3134 | 0.293 | 10.58 | 10.09 | 9.35 |
| glr_confirm_gap | 0.204 | 0.479 | 3133 | 0.278 | 10.28 | 9.67 | 8.00 |
