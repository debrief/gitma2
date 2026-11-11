# Spec 012 decision record: the scaled end-to-end regressor control

Written 2026-11-11, before any scored GPU run. One GPU run precedes it: the 10-minute
throughput pilot (`../20261110-r-pilot/`), which scored nothing; the spec asked for the record
first, and that order was not kept for that run.

## What is fixed

- **Model**: causal transformer on rows folded in threes; 8 layers, width 256, 8 heads,
  feed-forward 1,024; 6.39 million parameters; β-NLL (β = 0.5) on ln range and velocity in the
  canonical frame (`src/tma2/regress/`). A **control**, never carried or exported.
- **Data**: on the fly from stream seed 326, generator 0.6.0 MAN2, a fifth of every batch from
  the held-course variant (`configs/regress/held-course-ranges.json`, plan research R8).
- **Schedule**: 85,000 updates of 256 scenarios (21.8 million scenarios), AdamW, peak learning
  rate 3e-4, 2,000 warm-up updates, cosine decay, mixed precision; three training seeds.
- **No reduction**: the throughput pilot measured 635 scenarios a second on a T4, above the 250
  at which the plan stands (research R3).
- **Plans**, bound by digest (never edited after this record):

| Plan | SHA-256 |
| --- | --- |
| `configs/regress/pilot-curve.json` | `13ab1f4b0db7…` |
| `configs/regress/r-a-s1.json` | `cdeec6e2ccd2…` |
| `configs/regress/r-a-s2.json` | `1301b48809c4…` |
| `configs/regress/r-a-s3.json` | `4e151fc3ef73…` |
| `configs/regress/r-a-own.json` | `c9ce7f66c8c8…` |
| `configs/regress/r-a-tenth.json` | `712db040b4d6…` |

## Budget (owner: $50 in total, 2026-11-10)

- Measured: the throughput pilot (10 minutes of training plus start-up) cost $0.11 on the
  owner's usage page, about $0.66 a T4-hour all in.
- Modal's limits as the owner left them enforce $45 ($30 credit, $15 spend limit).
- The workflow's ledger cap is 68 T4-hours (≈ $45). The six plans' hard limits sum to 40.8
  hours (≈ $27): pilot curve 2.7, three seeds 30, ownship-only control 3.2, tenth-of-data
  control 5. About $18 remains unallocated; any use of it (a larger model, as a look at the
  hardware's limits) is proposed to the owner with these results, not taken.

## Readings (FR-021, FR-022; `regress/reading.py`)

- **Held course** (held-course split of the scored seed, settled rows with no target change):
  *reaches the bound* if the 95% scenario-clustered intervals of efficiency for range, course
  and speed all lie wholly below 1.25; *flat floor* if one lies wholly above 2.0 with no
  improvement from the worst to the best geometry quartile; otherwise *partial*. The plain
  no-knot solve on the same rows is the check (expected 0.95–1.01).
- **After manoeuvres** (MAN2 split, rows on which a change has begun): regressor − C″ and
  regressor − IMM, paired, with intervals; by true-range quartile; in metres.
- The thresholds 1.25 and 2.0 were proposed to the owner on 2026-11-10 without objection and
  are adopted here as the recommended default (AGENTS.md).
- Validation seed 327 for the pilot's reading of curves and for checking the pipeline; test
  seed 328 scored once per trained seed. Three seeds are reported singly and pooled.

## Controls

- **Ownship only**: what the scenario prior yields without bearings (a shorter run: a lower
  bound on the prior, not a matched budget).
- **A tenth of the data**: the same model on a stream repeating its first 2.18 million
  scenarios for half the schedule; compared with the carried model's checkpoint at the same
  number of updates is not available, so it is compared with the pilot curve and the final
  models, and the write-up says which comparison is which.
- On the classical side, beside C″: C with a raised confirmation threshold, if the owner closes
  spec 011 at tuning (reported, not a reading).

## Forecasts (before any scored run)

- Held course: **partial**. Efficiency for range between 1.3 and 2.5, worse for speed, and
  improving with geometry rather than flat.
- After manoeuvres: worse than C″ in median range error, better than the IMM.
- Ownship only: median relative range error near 0.5.
- A tenth of the data: worse than the carried model by more than the seed-to-seed spread.

## Known limits

One architecture at one size; a floor would be weaker evidence than a reach (plan research R7).
GPU training is not bit-reproducible: seeds, GPU type and versions are in each run record.
