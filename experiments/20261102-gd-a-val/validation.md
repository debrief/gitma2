# Gate D validation report

Seeds (validation seed 304, σ = 1° G5 rows; ratio = median range error ÷ the IMM's 0.0952):

| Detector | Variant | D-downstream-all ratio | Held-leg G5 false alarms |
| --- | --- | --- | --- |
| gd-causal-s1 | causal | 1.2067 | 0.0000% |
| gd-causal-s2 | causal | 1.1931 | 0.0000% |
| gd-causal-s3 | causal | 1.2731 | 0.0000% |
| gd-cls | causal | 1.2673 | 0.0000% |
| gd-late-s1 | time_late | 2.0031 | 0.0000% |
| gd-late-s2 | time_late | 2.8194 | 0.0000% |
| gd-late-s3 | time_late | 2.8343 | 0.0000% |

Carried: causal: gd-causal-s1, time_late: gd-late-s2

| Check | Result | Value | Interval | Limit |
| --- | --- | --- | --- | --- |
| gd-causal-s1:D-delay | fail | inf | [inf, inf] | 1 |
| gd-causal-s1:D-miss | inconclusive | 0.0001118 | [0, 0.000442] | 0 |
| gd-causal-s1:D-false | pass | 0 | [0, 0] | 0.002756 |
| gd-causal-s1:D-downstream-all | fail | 1.207 | [1.151, 1.265] | 1 |
| gd-causal-s1:D-downstream-settled-range | pass | 0.9738 | [0.9585, 0.9878] | 1.1 |
| gd-causal-s1:D-downstream-settled-course | pass | 0.9818 | [0.9444, 0.9979] | 1.1 |
| gd-causal-s1:D-downstream-settled-speed | pass | 0.9745 | [0.9608, 0.9932] | 1.1 |
| gd-causal-s1:D-kind | reported | nan | [nan, nan] |  |
| gd-causal-s1:D-gap | reported | 0.08991 | [nan, nan] |  |
| gd-late-s2:D-delay | fail | inf | [inf, inf] | 1 |
| gd-late-s2:D-miss | inconclusive | 0.0001118 | [0, 0.000442] | 0 |
| gd-late-s2:D-false | pass | 0 | [0, 0] | 0.002756 |
| gd-late-s2:D-downstream-all | fail | 2.819 | [2.66, 2.968] | 1 |
| gd-late-s2:D-downstream-settled-range | fail | 2.374 | [2.192, 2.583] | 1.1 |
| gd-late-s2:D-downstream-settled-course | fail | 3.695 | [3.229, 4.156] | 1.1 |
| gd-late-s2:D-downstream-settled-speed | fail | 1.992 | [1.842, 2.178] | 1.1 |
| gd-late-s2:D-kind | reported | nan | [nan, nan] |  |
| gd-late-s2:D-gap | reported | -2.137 | [nan, nan] |  |

Validation rule (Annex A §A.5): no variant is carried; the phase stops at validation and the test split stays unscored.
