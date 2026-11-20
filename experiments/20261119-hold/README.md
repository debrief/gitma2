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

**What is compared.** A turn-free 1-hour window given its predecessor's state is compared with
the same 1-hour window alone. The windows were shortened from 2 hours so that turn-free windows
exist. Two comparisons were **not** tested:
- `ctl` on its standing 2-hour windows;
- a joint solve over two consecutive windows.

**Classes** (windows / handed on / scored):

| class | windows | handed on | scored |
|---|---|---|---|
| held | 219 | 183 | 176 |
| one turn | 441 | 382 | 354 |

The 36 held windows that were not handed on are windows where contact was lost: median range
68 km, previous window unanswered in 97% of them, `ctl` answers 6. Counted as ties, held is
2.34 [2.01, 2.75].

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

## Panel sensitivities and limits

The panel's sensitivities are in `supplement.json` (`scripts/research/hold_supplement.py`) and
`review.md`. None changes the outcome.

**Weighting:**
- Each engagement weighted equally: held 2.31.
- The median engagement: 2.20.
- Share of engagements above 1: 86%.

**By window median true range:**

| range | held | one turn |
|---|---|---|
| < 15 km | 1.66 [1.34, 2.09] (42 windows) | 1.02 [0.81, 1.33] |
| 15–25 km | 2.15 [1.52, 3.01] (55) | 1.23 [0.98, 1.51] |
| > 25 km | 3.19 [2.50, 4.07] (79) | 1.28 [1.06, 1.53] |

**Other readings:**
- **Gaps:** a hand-over after a gap still gains: held 1.95 [1.39, 2.78] (44 windows), against
  2.59 for contiguous hand-overs.
- **Coverage:** the 0.945 is a pass of the soundness band, not a calibration. The median NEES
  is 0.74 against χ²(4)'s 3.36, so the region is too wide for most hand-overs and too narrow for
  a few.
- **One-turn windows:** reported, not decided. The median is 1.12, and 18% of windows are twice
  as bad.
- **`ctl-carry`'s scope:** the carried start alone costs 11% on one-turn windows (0.89). Spec
  026's adoption of `ctl-carry` as a cost measure therefore holds only for 2-hour windows with
  several turns. Recommended: no `ctl-carry` without the prior.

**Limits:**
- One simulator family (spec 024's simulated realism), contact 1 only, 1-hour windows.
- Hand-overs never fall inside a target manoeuvre: the window chain moves each start past a true
  manoeuvre (inherited from spec 023). Held windows that were moved gain 1.71 (14 windows),
  against 2.49.
- Spec 028's hand-over defect is kept. Held windows after held windows gain most (2.98, 27
  windows), and this is not separable from the defect.

## What this supports

Knowledge of the previous track usefully constrains this leg's solution where the leg alone
cannot resolve range. This is supported:
- in this simulator;
- for the tended contact;
- on 1-hour windows;
- against the same window alone.

On turn-free windows ctl ÷ ctl-prior is 2.41 [2.06, 2.83]. The median window improves by 2.15
and 76% of windows are better. The seeds agree: tuning 2.10, validation 1.91, test 2.41. The
median error falls from 0.227 to 0.074. On windows with one turn the shift is smaller, 1.22, and
is reported, not decided.

**Not measured or not tested:**
- whether the prior narrows the set of manoeuvre histories;
- whether a 2-hour window or a joint solve over consecutive windows would do as well.

**Panel:** round 1, three reviewers, each approve with findings (`review.md`).
