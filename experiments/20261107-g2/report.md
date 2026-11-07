# Segmentation scoring: /home/runner/work/_temp/data/test.f32pack, ordinals 0–4982

4983 scenarios, 19609 G5 rows (14403 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.580 | 66.95 | 6.31 | 1.023 [0.998, 1.049] | — | — | — |
| oracle | 0.064 | 7.51 | 0.94 | 0.113 [0.108, 0.118] | — | — | — |
| imm | 0.567 | 56.52 | 6.03 | — | — | — | — |
| ekf | 0.520 | 59.87 | 5.59 | — | — | — | — |
| naive | 0.398 | 90.84 | 3.73 | 0.702 [0.674, 0.731] | — | — | — |
| C | 0.116 | 15.14 | 1.61 | 0.205 [0.194, 0.215] | 0.899 [0.891, 0.908] | 0.273 | 0.000 |
| e-s3 | 0.103 | 14.24 | 1.49 | 0.182 [0.173, 0.192] | 0.924 [0.915, 0.931] | — | — |
| ew-s3 | 0.109 | 14.60 | 1.56 | 0.191 [0.182, 0.202] | 0.914 [0.905, 0.922] | — | — |
| glr_confirm | 0.498 | 47.52 | 4.78 | 0.878 [0.838, 0.915] | 0.159 [0.117, 0.204] | 0.286 | 0.000 |
| glr_confirm_gap | 0.510 | 48.19 | 4.50 | 0.898 [0.853, 0.949] | 0.137 [0.078, 0.188] | 0.286 | 0.000 |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.240 | 0.555 | 14896 | 0.407 | 15.36 | 19.27 | 14.72 |
| oracle | 0.000 | 0.025 | 19605 | 0.064 | 1.57 | 1.82 | 1.82 |
| imm | 0.233 | 0.548 | 15049 | 0.407 | 14.29 | 16.99 | 14.77 |
| ekf | 0.200 | 0.513 | 15695 | 0.388 | 12.64 | 16.10 | 12.22 |
| naive | 0.000 | 0.370 | 19609 | 0.398 | 7.90 | 21.10 | 6.29 |
| C | 0.005 | 0.115 | 19509 | 0.115 | 2.70 | 2.97 | 2.78 |
| e-s3 | 0.005 | 0.100 | 19510 | 0.102 | 2.46 | 2.84 | 2.62 |
| ew-s3 | 0.005 | 0.111 | 19507 | 0.108 | 2.57 | 2.91 | 2.72 |
| glr_confirm | 0.212 | 0.499 | 15446 | 0.316 | 11.71 | 11.63 | 10.21 |
| glr_confirm_gap | 0.215 | 0.504 | 15396 | 0.307 | 11.40 | 11.35 | 9.22 |
