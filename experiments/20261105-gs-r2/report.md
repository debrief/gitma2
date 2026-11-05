# Segmentation scoring: /home/runner/work/_temp/data/test.f32pack, ordinals 0–5058

5059 scenarios, 19921 G5 rows (14670 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.589 | 68.47 | 6.39 | 1.021 [0.996, 1.046] | — | — | — |
| oracle | 0.065 | 7.39 | 0.96 | 0.112 [0.108, 0.117] | — | — | — |
| imm | 0.577 | 56.01 | 6.07 | — | — | — | — |
| ekf | 0.521 | 60.09 | 5.71 | — | — | — | — |
| naive | 0.397 | 90.76 | 3.70 | 0.688 [0.663, 0.718] | — | — | — |
| C | 0.118 | 14.68 | 1.58 | 0.205 [0.195, 0.215] | 0.898 [0.889, 0.907] | 0.278 | 0.000 |
| L | 0.118 | 14.62 | 1.59 | 0.204 [0.194, 0.214] | 0.899 [0.890, 0.908] | 0.277 | 0.000 |
| glr_confirm | 0.514 | 47.90 | 4.65 | 0.891 [0.854, 0.929] | 0.143 [0.101, 0.186] | 0.295 | 0.000 |
| glr_confirm_gap | 0.533 | 48.58 | 4.38 | 0.923 [0.875, 0.971] | 0.108 [0.056, 0.159] | 0.295 | 0.000 |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.245 | 0.561 | 15047 | 0.413 | 15.60 | 20.58 | 14.35 |
| oracle | 0.000 | 0.024 | 19914 | 0.065 | 1.63 | 1.87 | 1.83 |
| imm | 0.237 | 0.557 | 15201 | 0.423 | 14.42 | 17.85 | 14.54 |
| ekf | 0.199 | 0.514 | 15950 | 0.378 | 12.38 | 16.17 | 11.83 |
| naive | 0.000 | 0.369 | 19921 | 0.397 | 7.99 | 22.65 | 6.29 |
| C | 0.004 | 0.117 | 19840 | 0.117 | 2.72 | 2.95 | 2.75 |
| L | 0.004 | 0.117 | 19836 | 0.117 | 2.72 | 2.96 | 2.77 |
| glr_confirm | 0.214 | 0.507 | 15651 | 0.331 | 12.41 | 11.89 | 9.95 |
| glr_confirm_gap | 0.216 | 0.514 | 15619 | 0.325 | 12.37 | 11.74 | 8.99 |
