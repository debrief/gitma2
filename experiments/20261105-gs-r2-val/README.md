# Gate S round 2: validation re-scored on the corrected segmentations

Gate S panel round 1 found that C (and so L) read later bearings on prefixes inside an open
transition (`review.md` in `experiments/20261105-gs-r2/`, R1). The fix is 7fe8874. Every
segmentation the gate depends on was re-made at that commit on CI, with the same parameters,
weights and data (`segment.yml`: `results/segment-{man2-val-c-42031087882,
segL-val-s1-42031091757, segL-val-s2-42031096857, segL-val-s3-42031102049,
segL-val-shuffled-42031108574}`; every header clean at 7fe8874). GLR + confirm was re-made on CI
too (`results/glr-confirm-man2-val-glr-42045836931`). Both scorings ran on CI with `score.yml` at
5541e54 (`results/score-r2-val-c-42060275909`, `results/score-r2-val-l-42060281962`).

Seed 314, ordinals 500–1499, 3,934 G5 rows; 97.5% scenario-clustered intervals.

| Question | Round 1 (`experiments/20261104-gs-val/c-final`, `20261105-segL-val`) | Round 2 (here) |
| --- | --- | --- |
| C-gap gap recovered (range) | 0.891 [0.871, 0.911] | 0.891 [0.871, 0.910] |
| Mode (R3): gap − chord | +0.006 [−0.002, +0.014] | +0.0058 [−0.0028, +0.0127]: gap |
| S2 on validation: C − GLR + confirm | +0.632 [0.558, 0.734] | +0.632 [+0.561, +0.734] |
| Carried rule (median of s1, s2, s3) | s1 0.8868, s3 0.8877, s2 0.8910: s3 | s1 0.8867, s3 0.8873, s2 0.8908: **s3** |
| Shuffled rule: segL-shuffled − C | −0.0020 [−0.0093, +0.0047]: pass | −0.0016 [−0.0089, +0.0050]: **pass** |
| L − C (s1 / s2 / s3) | −0.005 / −0.000 / −0.004 | −0.0045 / −0.0004 / −0.0039 |

The fix changes the segmentations of prefixes inside open transitions only, and on validation it
moves nothing that a rule decides. (Small differences between the two scorings and round 1 are
partly runner noise: the physics-layer errors reproduce byte for byte only on the same CPU family.
The two scorings here ran at the same commit on different runners; the one-leg median is 0.581251
in `c/` and 0.580468 in `l/` and round 1. Each rule compares estimators within one run.) the mode, the carried model (s3, `carried.json` unchanged) and
the shuffled rule are as before.

Validation C's segmenter digest (2e05b4b6…) differs from the gate's (60e6ee63…) because the
T021 plan sets `mode: chord`; confirmation never reads the mode (it sets only the reported cost),
so the intervals are the gate's segmenter's, and `--modes` hands them over in each mode (panel
round 2).

**New in round 2 (panel round 1, R5 and R6):**
- **GLR + confirm handed over as C is** (`glr_confirm_gap`, gap mode, a point knot as T_min rows):
  gap recovered 0.255 [0.149, 0.350], against 0.259 for note 08's point-knot hand-over. The
  hand-over explains almost none of S2's margin (at most about 0.02 on test, where the gap
  hand-over helps GLR + confirm slightly on the rows every estimator answers); C's gain is in its
  segmentation (the extra nominator, transition modelling and confirmation).
- **Gross rows and efficiency** (known-manoeuvres bound):

  | Estimator | No estimate | Range > 50% | Range median, finite rows | Efficiency (range) |
  | --- | --- | --- | --- | --- |
  | one leg | 23.2% | 55.8% | 0.414 (3,020 rows) | 15.5 |
  | frozen IMM | 22.5% | 53.1% | 0.392 (3,047) | 13.2 |
  | naive | 0% | 39.5% | 0.410 (3,934) | 8.2 |
  | GLR + confirm | 20.3% | 47.5% | 0.293 (3,134) | 10.6 |
  | C, gap | 0.6% | 11.7% | 0.119 (3,910) | 2.8 |
  | oracle | 0.03% | 2.3% | 0.064 (3,933) | 1.6 |

  On MAN2's long manoeuvring windows the naive baseline's median range error (0.410) is below
  one leg's (0.580) and the IMM's (0.539): the references fail outright on about a fifth of the
  rows. C's headline gap recovered (0.891) is measured from one leg's median, which those rows
  inflate.
- Strata by range band, number of changes, latest change kind, speed-only and transition
  duration: `c/metrics.json` and `l/metrics.json`, under each estimator's `strata`.

Files: `c/` and `l/` hold each scoring's `metrics.json`, `report.md`, `plan.json` and `run.json`
(`errors.npz` is on the results branches).
