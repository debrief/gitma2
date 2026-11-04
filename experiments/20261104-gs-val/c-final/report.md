# Segmentation scoring: data/man2-val/validation.f32pack, ordinals 500–1499

1000 scenarios, 3934 G5 rows (2933 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.580 | 65.97 | 6.20 | 1.077 [1.022, 1.135] | — | — | — |
| oracle | 0.064 | 7.42 | 0.97 | 0.118 [0.106, 0.131] | — | — | — |
| imm | 0.539 | 52.32 | 5.79 | — | — | — | — |
| ekf | 0.498 | 57.45 | 5.20 | — | — | — | — |
| C-chord | 0.123 | 15.98 | 1.64 | 0.229 [0.205, 0.252] | 0.885 [0.866, 0.904] | 0.272 | 0.083 |
| C-gap | 0.120 | 15.59 | 1.62 | 0.223 [0.199, 0.247] | 0.891 [0.871, 0.911] | 0.272 | 0.083 |
| glr_confirm | 0.447 | 44.36 | 4.57 | 0.829 [0.757, 0.924] | 0.259 [0.157, 0.333] | 0.289 | 0.083 |
