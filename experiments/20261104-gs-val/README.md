# Spec 005 phase 1 on MAN2 validation (seed 314)

Validation measurements that fix decision-record values (tasks T010, T021, T024). Seed 314,
`data/man2-val/validation.f32pack` (digest in `experiments/20261104-g0-man2/dataset-digests/`).
σ = 1° scenarios in file order (note 08's ordinals): tuning 0–499, scoring 500–1499.

## T010: cost of C at 720 rows (quiet machine, one core per process, four at once)

| Search grid step | Cost table, median | ≥ 600 rows, median | Worst |
| --- | --- | --- | --- |
| 6 rows | 3.0 s | 9.6 s | 12.0 s |
| 3 rows | 10.9 s | 36.7 s | 46.9 s |

**Decision:** the grid step is 6 rows (`search_step_rows`), equal to T_min. All four G5 rows lie on
one grid anchored at the first, so one table serves them. The full segmenter C (GLR statistic,
cost table, confirmation, four G5 prefixes) took 650 s for 16 scenarios on one core: about 41 s
per scenario, or about 10 s per scenario on a 4-core runner with four workers. That is FR-024's
budget, met at the margin and not exceeded. Larger runs use `.github/workflows/segment.yml`
(eight runners).

## T021: the search's per-leg penalty (`penalty.json`, `scripts/research/man2_penalty.py`)

MAN2 engagements almost always hold a target change, so R1's measure ("a transition on an
engagement without a change") has too few rows to calibrate on. The measure here is per G5
prefix: a false transition is one, after the zig plus L_min, starting more than ± 3 min from any
truth change. 1,971 prefixes of the 500 tuning scenarios:

| Penalty | Prefixes with a false transition | Truth changes found within ± 60 s |
| --- | --- | --- |
| 10 | 20.4% | 19.4% |
| 20 | 6.6% | 14.1% |
| **30** | **3.5%** | **12.7%** |
| 40 | 2.8% | 12.0% |
| 60 | 1.8% | 10.6% |
| 120 | 1.2% | 7.1% |

**Decision:** penalty 30, the smallest on the grid at or below 5%.

The search alone is a weak nominator on MAN2: even at penalty 10 it finds under a fifth of the
changes within ± 60 s, as R1 found on 0.5.0 (recall 0.56 there, on easier, shorter windows). GLR
alarms are C's main nominator.

## T024: O on the ownship tracks (`ownship.json`, all 10,000 scenarios)

All 20,000 ownship turns are found, with no extra transitions, and O's legs have zero
contamination against the truth labels for every wander kind (none, helm wander, autopilot
oscillation). **Caveat:** every MAN2 ownship turn is a zig of 30° or more, so the 10–15° and
15–30° turn-size strata of FR-063 are empty. S1 tests O on the data's turns only. The
constructed-track unit tests (12° and 15° turns, wander, oscillation) are the evidence for small
turns. Proposed S1 limit: contamination P90 ≤ 0.02 (the spec's proposal; O is at 0).

## Preliminary: C on the 1,000 scoring ordinals (`prelim-c/`, superseded by `c-final/` below)

C's segmentations came from the CI run `results/segment-man2-val-c-41876210154` (plan
`configs/segment/man2-val-c.json`: penalty 30, GLR threshold 4.665, tuned on ordinals 0–499).
They are scored by `tma2-gs --modes chord gap` on 3,934 G5 rows (2,933 settled). **Preliminary.**
The IMM column is the 0.5.0 setting (`imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16`), not yet
re-tuned on MAN2, and GLR + confirm is not yet scored. Both follow T032/T033.

| Segmenter | Median range (rel.) | Course ° | Speed kt | Gap recovered, range [97.5%] |
| --- | --- | --- | --- | --- |
| one leg (batch least squares) | 0.580 | 66.0 | 6.20 | 0 |
| oracle | 0.064 | 7.4 | 0.97 | 1 |
| C, chord | 0.123 | 16.0 | 1.64 | 0.885 [0.866, 0.904] |
| C, gap | 0.120 | 15.6 | 1.62 | 0.891 [0.871, 0.911] |

The segmentation measures are weaker than the downstream ones.
- **Boundary hits:** 10% of truth changes have both boundaries within ± 60 s, and 43% within
  ± 3 min.
- **Contamination:** P90 is 0.27.
- **False splits:** 8.3%, on only 24 change-free prefixes.
- **Leg-count accuracy:** 0.50, counted over all changes. It is not yet restricted to detectable
  ones; the detectability strata come from T033's statistics.

C places a transition where the cost needs a knot, not where the truth's turn begins and ends.
That suits the estimate, but it is weak on the definitions of contamination and boundaries.

**Gap or chord (R3, FR-031):** gap has the lower median range error (0.120 against 0.123), so
gap is the proposed mode. The paired difference gets an interval in the final scoring.

## Final validation scoring (`c-final/`): the references re-tuned, S2 and the mode

The same C segmentations, scored by `tma2-gs --modes chord gap --glr-confirm --detectability`
against the frozen MAN2 IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` and EKF
`ekf-sa0.00003-p4-r0.03125`. 3,934 G5 rows (2,933 settled) on 1,000 scenarios; medians; 97.5%
scenario-clustered intervals.

| Estimator | Range (rel.) | Course ° | Speed kt | Range ÷ IMM | Gap recovered (range) |
| --- | --- | --- | --- | --- | --- |
| one leg (batch least squares) | 0.580 | 66.0 | 6.20 | 1.077 [1.022, 1.135] | 0 |
| frozen IMM | 0.539 | 52.3 | 5.79 | 1 | — |
| frozen EKF | 0.498 | 57.5 | 5.20 | — | — |
| GLR + confirm | 0.447 | 44.4 | 4.57 | 0.829 [0.757, 0.924] | 0.259 [0.157, 0.333] |
| **C, gap** | **0.120** | **15.6** | **1.62** | **0.223 [0.199, 0.247]** | **0.891 [0.871, 0.911]** |
| C, chord | 0.123 | 16.0 | 1.64 | 0.229 [0.205, 0.252] | 0.885 [0.866, 0.904] |
| oracle | 0.064 | 7.4 | 0.97 | 0.118 [0.106, 0.131] | 1 |

**S2 on validation.** C (gap) − GLR + confirm, gap recovered in range: **+0.632 [0.558, 0.734]**.
Course gives +0.49 and speed +0.56, both intervals above zero. C beats GLR + confirm, which
implies that C is the S4 reference. S2 is decided again on test.

**Mode (FR-031).** The decision rule is the lower median range error, with ties going to the
chord. Gap gives 0.120 against the chord's 0.123, so **gap** is carried. The paired difference is
small and its interval includes zero (gap − chord, gap recovered: +0.006 [−0.002, 0.014]).

**SC-002** is reproduced (`sc002.md`).

**Segmentation measures**, identical for C's two modes:
- contamination: median 0, P90 0.272 (GLR + confirm 0.289);
- false split: 2 of only 24 change-free prefixes, 0.083, the same for GLR + confirm;
- leg-count accuracy on detectable changes: 0.67 (GLR + confirm 0.27);
- boundaries within ± 3 min: 0.43 overall, rising from 0.13 in the lowest detectability band to
  0.70 in the highest.

C places a transition where the cost needs a knot, not where the truth's turn begins, so it is
weak on boundaries and contamination but strong downstream.

**The trackers.** The EKF (0.498) beats the IMM (0.539) on range, but not on course. The IMM stays
the gated reference (D3); the EKF caveat is in `experiments/20261104-man2-tune-pass4/`. Both
were tuned on rows that include these ordinals, which favours them.
