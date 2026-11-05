# Gate S on seed 315, record r2 (after panel round 1)

Machine verdict: **S1 pass, S2 pass, S3 pass, S4 inconclusive; reference C** (exit 3). The decision
record counts inconclusive as not passed, so C carries into Gate 2 and learning is recorded as not
shown (FR-072). The panel's verdict is in `review.md`.

**Why r2.** Panel round 1 (`review.md`) found that C, and so L, read later bearings on prefixes
inside an open transition (R1, a blocker): closing a transition polished its start with bearings
up to the closing row, and earlier prefixes reported that start. Fixed in 7fe8874. This record is
the bug-fix re-run: the decision record, plan, limits, rows, parameters, data and the carried
weights are unchanged. Record r1 (`experiments/20261105-gs/`) stays as reviewed in round 1.

**How it was made.** Every input on CI from a clean tree:
- C and L (segL-s3) on the test split at 7fe8874: `results/segment-gs-test-c-42031116381`,
  `results/segment-gs-test-l-42031120266` (C's segmenter digest equals the decision's parameter
  digest; L's equals the carried s3's).
- GLR + confirm: the frozen test shards `results/glr-confirm-gs-test-glr-41979573239` (no
  close-and-polish step, so unaffected by R1).
- The validation rules were applied again first (`experiments/20261105-gs-r2-val/`): mode gap,
  carried model s3, shuffled rule pass, all as before.
- Scoring: `score.yml` run 42068715251 at 9957471 (`results/score-r2-gate-42068715251`, with
  `errors.npz`); `manifest.json` records `git_dirty: false` and the SHA-256 of every input file.

5,059 σ = 1° scenarios, 19,921 G5 rows (14,670 settled); 97.5% scenario-clustered paired intervals,
2,000 resamples; medians `inverted_cdf` throughout (panel round 1).

| Check | Statistic | r1 | r2 |
| --- | --- | --- | --- |
| S1 | O's contamination P90, limit 0.02 | 0 [0, 0] pass | 0 [0, 0] **pass** |
| S2 | C − GLR + confirm, gap recovered (range) | +0.755 [+0.711, +0.798] pass | +0.755 [+0.711, +0.798] **pass** |
| S3 | L − C contamination median / P90 (limit +0.01) | 0 / −0.0005 [−0.0056, +0.0034] | 0 [−0.009, 0] / −0.0012 [−0.0056, +0.0036] |
| S3 | L − C false split (limit +0.05) | 0 [0, 0] | 0 [0, 0]: S3 **pass** |
| S4 | L − C, gap recovered (range) | +0.0014 [−0.0030, +0.0051] | +0.0012 [−0.0031, +0.0049] **inconclusive** |

**Beside the gate (reported, not gated):**

| Estimator | Range median | No estimate | Range > 50% | Range, finite rows | Efficiency (range) | Gap recovered |
| --- | --- | --- | --- | --- | --- | --- |
| one leg | 0.589 | 24.5% | 56.1% | 0.413 | 15.6 | 0 |
| frozen IMM | 0.577 | 23.7% | 55.7% | 0.423 | 14.4 | — |
| frozen EKF | 0.521 | 19.9% | 51.4% | 0.378 | 12.4 | — |
| naive | 0.397 | 0% | 36.9% | 0.397 | 8.0 | — |
| GLR + confirm | 0.514 | 21.4% | 50.7% | 0.331 | 12.4 | 0.143 |
| GLR + confirm, gap hand-over | 0.533 | 21.6% | 51.4% | 0.325 | 12.4 | 0.108 |
| C | 0.118 | 0.4% | 11.7% | 0.117 | 2.7 | 0.898 [0.889, 0.907] |
| L | 0.118 | 0.4% | 11.7% | 0.117 | 2.7 | 0.899 [0.890, 0.908] |
| oracle | 0.065 | 0.0% | 2.4% | 0.065 | 1.6 | 1 |

Reading:
- **S2's margin is segmentation, not hand-over.** GLR + confirm handed over as C is (gap mode)
  recovers 0.108, no more than its own point-knot hand-over (0.143).
- **The references fail outright on a fifth to a quarter of the rows**, and the naive baseline's
  median (0.397) is below one leg's, the IMM's and GLR + confirm's. C's 0.898 is measured from one
  leg's median, which those rows inflate; on the rows every estimator answers, the medians are in
  the finite-row column.
- **C is 2.7× the known-manoeuvres bound** in range, the oracle 1.6×.

Strata (range band, number of changes, latest change kind, speed-only, transition duration,
detectability) are in `metrics.json`. `first-run`: r1's records are in `experiments/20261105-gs/`.
