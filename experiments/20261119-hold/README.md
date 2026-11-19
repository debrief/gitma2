# Spec 029 test record (seed 364): the carried prior where the ownship holds course

## Run and scoring

- **Engagements:** 30 + 30 engagements of 6 and 12 hours in which the ownship holds each leg for
  1–2 hours (`configs/long/hold-test.json`).
- **Windows:** contact 1, in 1-hour windows overlapping 15 min.
- **Settings:** the registered ones (decision record `experiments/20261119-hold-decision/`, code
  `c39cb031…`).
- **CI:** run 44578629985, commit ec66def, AMD EPYC 7763. 60 jobs took 22.7 runner-hours.
- **Raw outputs:** in `raw/`.

Scored once:

    uv run tma2-long study29 --raw experiments/20261119-hold/raw \
        --config configs/long/hold-test.json --out experiments/20261119-hold

`study.json` records `git_dirty: true` only because the record's folder was untracked when it
was scored.

## Soundness

| check | value | |
|---|---|---|
| S1 windows ran | 720 of 720, no engagement missing | pass |
| S2 ctl ÷ true-history fit (per-engagement geometric mean) | 1.29 [1.15, 1.45] | pass |
| S3 held-window coverage of the carried 95% region | 0.945 [0.913, 0.974] (183 hand-overs) | pass |

## The rule's output: **gain** (no harm)

ctl ÷ ctl-prior is a geometric mean over windows of per-window median error; above 1 favours the
prior. Chains' first windows and windows with no hand-over are excluded. The interval is a
bootstrap over engagements.

| class | windows (engagements) | range | course | speed |
|---|---|---|---|---|
| **held (no ownship turn)** | 176 (58) | **2.41 [2.06, 2.83]** | 1.96 [1.66, 2.31] | 2.24 [1.79, 2.78] |
| one turn | 354 (60) | 1.22 [1.06, 1.40] | 1.21 [1.06, 1.39] | 1.15 [0.99, 1.33] |
| more | 0 | | | |

- **Gain:** on held windows the lower limit is 2.06, above 1.
- **Harm:** no upper limit is below 1. The "more" class is empty, so its check is vacuous.

### The typical held window

| measure | value |
|---|---|
| median ratio | 2.15 |
| trimmed 10% at both ends | 2.29 [1.94, 2.70] |
| windows better | 76% |
| twice as good | 51% |
| twice as bad | 9% |

The gain is in the typical held window, not in a tail.

## Against the forecasts (decision record)

| forecast | outcome |
|---|---|
| held, range: 1.5–2.0, lower limit above 1 with probability about 0.75 | 2.41 [2.06, 2.83]: above the forecast range |
| one turn, range: 1.2–1.5, no harm anywhere | 1.22 [1.06, 1.40]; no harm |
| ctl-prior on held windows near the true-history fit | better than it (fit ÷ ctl-prior 1.83 [1.45, 2.32]) |
| guard falls back on 1–3% | 0.9% (5 of 532) |
| held coverage 0.85–0.95 | 0.945 |
| about 70% of windows answered | 84% |

## Reported beside (decided by nothing)

### Median range error per window

| | ctl | ctl-carry | ctl-prior | fit told the true history | C″ |
|---|---|---|---|---|---|
| held | 0.227 | 0.161 | **0.074** | 0.136 | 0.998 |
| one turn | 0.089 | 0.101 | 0.064 | 0.060 | 0.179 |

On held windows `ctl-prior` beats the fit told the true manoeuvre history. That fit sees only the
window's own bearings, so on a held window range is left open for it. The prior brings
information from outside the window. It is not a ceiling.

### The prior's own effect

ctl-carry ÷ ctl-prior shares the carried start, so it isolates the prior:
- held: 2.12 [1.78, 2.54];
- one turn: 1.37 [1.21, 1.54].

The carried start alone gives ctl ÷ ctl-carry of 1.14 [0.98, 1.33] on held windows. On one-turn
windows it is 0.89 [0.82, 0.97], so the start alone costs about 11% there. The prior recovers
that and gains about 22% more.

### Other readings

- **Duration:** held 2.10 [1.60, 2.72] at 6 h and 2.58 [2.13, 3.13] at 12 h.
- **Guard:**
  - It fell back on 5 of 532 windows.
  - Guarded against unguarded: held 2.41 against 2.38; one turn 1.218 against 1.218.
- **Coverage of the carried 95% region:**
  - held 0.945 [0.913, 0.974];
  - one turn 0.890 [0.854, 0.924];
  - all 0.908.
- **Answered:** `ctl` 0.835, `ctl-prior` 0.838.
- **Cost:** the prior's two searches took 7.1 of 22.7 runner-hours.

## What this supports

Where the ownship holds course for an hour or two, carrying the previous window's state and
uncertainty into the next window's fit and evidence roughly halves the median range error. This
holds on the tended contact of this simulator's realistic engagements:
- in turn-free 1-hour windows, a geometric mean of 2.4, median 2.1, with 76% of windows better;
- in windows with one ownship turn, a smaller gain of 1.2.

**Limits:**
- one simulator family, with held legs as the only change;
- 1-hour windows, chosen so that turn-free windows exist;
- the hand-over defect spec 028's panel recorded is kept.
