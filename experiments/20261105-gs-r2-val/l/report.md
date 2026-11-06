# Segmentation scoring: /home/runner/work/_temp/data/validation.f32pack, ordinals 500–1499

1000 scenarios, 3934 G5 rows (2933 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.580 | 65.97 | 6.20 | 1.077 [1.022, 1.135] | — | — | — |
| oracle | 0.064 | 7.42 | 0.97 | 0.118 [0.106, 0.131] | — | — | — |
| imm | 0.539 | 52.32 | 5.79 | — | — | — | — |
| ekf | 0.498 | 57.45 | 5.20 | — | — | — | — |
| naive | 0.410 | 88.77 | 4.04 | 0.761 [0.689, 0.835] | — | — | — |
| C-gap | 0.120 | 15.52 | 1.62 | 0.223 [0.199, 0.246] | 0.891 [0.871, 0.910] | 0.280 | 0.083 |
| segL-s1-gap | 0.122 | 15.85 | 1.64 | 0.227 [0.205, 0.252] | 0.887 [0.866, 0.904] | 0.281 | 0.083 |
| segL-s2-gap | 0.120 | 15.91 | 1.63 | 0.223 [0.199, 0.248] | 0.891 [0.870, 0.911] | 0.270 | 0.083 |
| segL-s3-gap | 0.122 | 15.70 | 1.65 | 0.226 [0.203, 0.250] | 0.887 [0.866, 0.908] | 0.270 | 0.083 |
| segL-shuffled-gap | 0.121 | 15.61 | 1.63 | 0.224 [0.201, 0.248] | 0.890 [0.869, 0.909] | 0.273 | 0.083 |

Gross rows (no plausible estimate; range error over 50%), medians over the rows each estimator answers, and efficiency (median |e|/σ / 0.6745 against the known-manoeuvres bound). Strata are in `metrics.json`.

| Estimator | No estimate | Range > 50% | Finite rows | Range (finite) | Eff. range | Eff. course | Eff. speed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.232 | 0.558 | 3022 | 0.414 | 15.45 | 19.43 | 13.75 |
| oracle | 0.000 | 0.023 | 3933 | 0.064 | 1.55 | 1.76 | 1.76 |
| imm | 0.225 | 0.531 | 3047 | 0.392 | 13.20 | 15.53 | 13.67 |
| ekf | 0.188 | 0.500 | 3196 | 0.363 | 11.65 | 14.53 | 11.25 |
| naive | 0.000 | 0.395 | 3934 | 0.410 | 8.18 | 21.73 | 6.33 |
| C-gap | 0.006 | 0.117 | 3910 | 0.119 | 2.77 | 2.99 | 2.72 |
| segL-s1-gap | 0.006 | 0.117 | 3910 | 0.121 | 2.78 | 3.10 | 2.77 |
| segL-s2-gap | 0.006 | 0.114 | 3910 | 0.119 | 2.76 | 3.05 | 2.81 |
| segL-s3-gap | 0.007 | 0.114 | 3908 | 0.121 | 2.78 | 2.98 | 2.78 |
| segL-shuffled-gap | 0.006 | 0.115 | 3912 | 0.120 | 2.76 | 3.03 | 2.72 |
