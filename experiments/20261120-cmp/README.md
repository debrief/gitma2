# Spec 030 test (seed 366): all three readings "ctl-prior worse"

Test record for spec 030 (`specs/030-held-comparators/`). It was scored once, under the decision
record `experiments/20261120-cmp-decision/`.

## Run and scoring

- **Engagements:** 30 + 30 held-course engagements, contact 1 (`configs/long/cmp-test.json`).
- **Systems:** (a) 1-hour `carry2`, (b) 2-hour `carry2`, (c) `jointheld`.
- **CI:** run 44672623154, commit e1cd7d1, Intel Xeon Platinum 8370C. 180 jobs took 82.4
  runner-hours: (a) 22.3, (b) 47.7, (c) 12.4.
- **Raw outputs:** in `raw/`.
- **One file added by hand:** engagement 1 has no held window. Its `jointheld` job wrote a
  header with `windows: []` and no `.npz`, so `raw/cmp-test-c1-jointheld-1.npz` is an empty
  archive made with `np.savez_compressed`. It changes no number: the engagement has no held
  windows to decide.

Scored with:

    uv run tma2-long study30 --raw experiments/20261120-cmp/raw \
        --config configs/long/cmp-test.json --out experiments/20261120-cmp

`study.json` records `git_dirty: true` only because this folder was untracked when it was scored.
The commit was e1cd7d1 and no tracked file differed.

## Soundness (registered)

| check | value | |
|---|---|---|
| S1 parts present | all 60 engagements; 720 of 720 windows ran | pass |
| S2 1-hour ctl ÷ true-history fit (per-engagement geometric mean) | 1.39 [1.22, 1.58] | pass |
| S3 held-window coverage of the carried 95% region | 0.896 (183 hand-overs) | pass |

## The registered rule

**Counts:** 218 held windows. 183 were handed on and 179 decided, from 56 engagements.

**Readings** (held windows; the system named ÷ 1-hour `ctl-prior`; geometric mean [95% interval
over engagements]):

| estimand | range | median | 1-hour prior better | course | speed | reading |
|---|---|---|---|---|---|---|
| D1: 2-hour `ctl` | 0.730 [0.579, 0.917] | 0.90 | 43% | 0.68 | 0.62 | **ctl-prior worse** |
| D2: joint solve | 0.774 [0.632, 0.954] | 0.78 | 41% | 0.65 | 0.63 | **ctl-prior worse** |
| D3: 2-hour `ctl-prior` | 0.488 [0.386, 0.619] | 0.58 | 26% | 0.45 | 0.46 | **ctl-prior worse** |

The 10% trimmed means are 0.755, 0.758 and 0.479.

**Against the forecasts** (in the decision README):
- **D1 and D2:** forecast at 1.1–1.3 (1-hour `ctl-prior` better). Wrong in direction. Tuning had
  leant that way (1.30, 1.28) and validation the other way (0.75, 0.84).
- **D3:** forecast at 0.6–0.85, "worse" with probability 0.6. Right in direction, and the effect
  was larger than forecast.

**What this says.** On held-course engagements, the carried prior on 1-hour windows does not
replace a longer window. Both 2-hour `ctl` and the joint solve beat it. Best of all is the carried
prior on 2-hour windows.

## Reported, not decided

**Median range error on held windows:**

| system | median error |
|---|---|
| 1-hour `ctl` | 0.224 |
| 1-hour `ctl-prior` | 0.102 |
| 2-hour `ctl` | 0.090 |
| joint solve | 0.070 |
| **2-hour `ctl-prior`** | **0.042** |
| span reference (told the true history over the span) | 0.031 |

**Other readings** (`study.json`, `beside`):
- **Spec 029 replicated:** 1-hour ctl ÷ ctl-prior is 1.71 [1.40, 2.14].
- **One-turn windows, D1:** 0.717 [0.615, 0.84].
- **D1 by range band:**

  | band | ratio |
  |---|---|
  | under 15 km | 0.70 [0.40, 1.22] |
  | 15–25 km | 0.77 |
  | over 25 km | 0.717 [0.525, 0.973] |

- **D2 by range band:** 0.744 under 15 km, 0.938 at 15–25 km, 0.686 [0.506, 0.954] over 25 km.
- **Cost per window:** (a) 112 s; (b) 477 s per 2-hour window; (c) 204 s per held window.

**Supplement** (`supplement.json` from `scripts/research/cmp_supplement.py`; decides nothing):
- **2-hour `ctl` ÷ 2-hour `ctl-prior`:** the prior helps on top of the longer window.
  - Held windows: 1.49 [1.27, 1.77], median 1.14.
  - One-turn windows: 1.26 [1.08, 1.45], median 1.01.
- **Joint solve ÷ 2-hour `ctl-prior`** (held): 1.56 [1.27, 1.93].
- **Engagements weighted equally:**

  | estimand | ratio |
  |---|---|
  | D1 | 0.747 [0.574, 0.958] |
  | D2 | 0.749 [0.600, 0.928] |
  | D3 | 0.474 [0.375, 0.604] |
