# Spec 038 development run A (spent seed 321; not a result)

300 engagements of seed 321, in distribution, clean (`off`) and under the primary mismatch
condition (`all-central`). CI run 45988818139 at commit 8284ecd4; plan
`configs/headroom/gd-dev-a-in.json`. Collected by `scripts/research/gd_collect.py`; `tables.md`
by `scripts/research/gd_tables.py`. Ratios are C″-robust ÷ system in range.

What it was for: choosing the hardened controls' settings and the own-prior weight by the rules
of `specs/038-gain-decomposition/research.md` R1 to R3.

| | clean | primary |
|---|---|---|
| fine-tuned regressor | 1.656 [1.473, 1.873] | 2.084 [1.864, 2.320] |
| robust solve told the true manoeuvre times | 1.703 | 2.024 |
| threshold × 1.5 / 2 / 3 / 4 | 0.928 / 0.892 / 0.863 / 0.824 | 1.007 / 1.042 / 1.059 / 1.137 |
| edit: wild / effective sd / both | 1.007 / 0.980 / 0.986 | 1.177 / 1.069 / 1.159 |
| ownship-only regressor alone | 0.282 | 0.578 |
| own prior in C″'s solve, weight 0.25 / 0.5 / 1 / 2 / 4 | 0.710 / 0.857 / 0.967 / 0.998 / 1.002 | 0.923 / 0.986 / 1.034 / 1.025 / 1.016 |

Choices (written to `configs/gd/protocol.json`, `chosen`):
- **Threshold 4.** No value helps pooled over clean and primary; 4 is the least bad and at the
  grid's edge, so 6 and 8 run beside it on run B.
- **Edit: wild bearings only.** It closes about 0.22 [0.10, 0.34] of the log gap to the
  regressor under the primary condition and costs nothing on clean data. The effective sd adds
  nothing.
- **Own-prior weight 2**, bracketed by 1 and 4. At no weight does the prior move the solve by
  more than 3%.
- A combined control (edit and threshold 4) is added to run B.

Stop rule (FR-042): no control closes half the gap; C″-robust stays the comparator.

Things seen here that the registration must carry:
- The regressor is 1.66 better than C″-robust on clean data too, and a robust solve told the
  true manoeuvre times is level with it on both. The gap is the segmentation with or without
  bearing errors.
- The ownship-only regressor alone is at the IMM's level (0.39 median range error).
