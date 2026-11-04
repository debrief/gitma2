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
