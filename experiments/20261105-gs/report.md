# Segmentation scoring: data/gs-test/test.f32pack, ordinals 0–5058

5059 scenarios, 19921 G5 rows (14670 settled); frozen IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`; intervals 97.5%, 2000 resamples, clustered.

| Segmenter | Range | Course ° | Speed kt | Range vs IMM | Gap (range) | Contam. P90 | False split |
| --- | --- | --- | --- | --- | --- | --- | --- |
| one_leg | 0.589 | 68.47 | 6.39 | 1.021 [0.996, 1.046] | — | — | — |
| oracle | 0.065 | 7.39 | 0.96 | 0.112 [0.108, 0.117] | — | — | — |
| imm | 0.577 | 56.01 | 6.07 | — | — | — | — |
| ekf | 0.521 | 60.09 | 5.71 | — | — | — | — |
| C | 0.118 | 14.66 | 1.58 | 0.205 [0.195, 0.215] | 0.898 [0.889, 0.908] | 0.277 | 0.000 |
| L | 0.118 | 14.60 | 1.59 | 0.204 [0.194, 0.214] | 0.899 [0.890, 0.908] | 0.276 | 0.000 |
| glr_confirm | 0.514 | 47.90 | 4.65 | 0.891 [0.854, 0.929] | 0.143 [0.101, 0.186] | 0.294 | 0.000 |
