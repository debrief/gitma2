# Spec 027 test record (seed 356): the previous window as a prior

## Run and scoring

- **Engagements:** 30 + 30 realistic engagements of 6 and 12 hours, both contacts
  (`configs/long/cp-test.json`).
- **Settings:** the registered ones (scale 4, tail 1,200 s, α = 0.001; decision record
  `experiments/20261119-cp-decision/`, code `09a7edae…`).
- **CI:** run 44448485807, commit 274154e, AMD EPYC 9V45. 120 jobs took 76 runner-hours.
- **Raw outputs:** in `raw/`.

Scored once:

    uv run tma2-long study27 --raw experiments/20261119-cp/raw \
        --config configs/long/cp-test.json --out experiments/20261119-cp

**Provenance:**
- `study.json` records `git_dirty: true` only because the record's folder was untracked when
  it ran. The scoring code is that of the decision record.
- `supplement.json` comes from `scripts/research/cp_supplement.py`.

## Soundness

| check | value | |
|---|---|---|
| S1 windows ran | 720 of 720, no engagement missing | pass |
| S2 ctl ÷ true-history fit (per-engagement geometric mean) | 1.44 [1.30, 1.58] | pass |
| contact-1 coverage of the carried 95% region | 0.953 [0.930, 0.974] (300 hand-overs) | |

## The rule's output: **not shown, at this size** (no harm)

ctl ÷ ctl-prior is a geometric mean over windows of per-window median error. Above 1 favours the
prior. Chains' first windows are excluded, and the interval comes from a bootstrap over
engagements.

| split | windows (engagements) | range | course | speed |
|---|---|---|---|---|
| **weak geometry (registered)** | 215 (94) | **1.105 [0.963, 1.273]** | 1.12 [0.97, 1.31] | 1.16 [0.95, 1.40] |
| other | 240 (60) | 1.14 [1.035, 1.27] | 1.22 [1.08, 1.38] | 1.07 [0.91, 1.23] |
| contact 1 | 299 (60) | 1.11 [1.006, 1.22] | 1.17 [1.04, 1.31] | 1.04 [0.89, 1.20] |
| contact 2 | 156 (57) | 1.16 [0.988, 1.37] | 1.18 [0.99, 1.39] | 1.26 [1.006, 1.55] |

- **Gain:** the lower limit on the weak split is 0.963, not above 1, so gain is not shown.
- **Harm:** no upper limit is below 1 on any split, in range, course or speed.

## Against the forecasts (decision record)

| forecast | outcome |
|---|---|
| weak split, range: about 1.2–1.4, lower limit above 1 with probability about 0.6 | 1.105 [0.963, 1.273]: smaller, not shown |
| other split, range: about 0.95, harm with probability about 0.3 | 1.14 [1.035, 1.27]: wrong in sign |
| weak split: the course gain larger than the range gain | 1.12 against 1.105: about equal |
| guard falls back on 1–4% | 1.8% (8 of 443) |
| contact-1 coverage 0.88–0.92; contact 2 lower | 0.953; contact 2 0.90 [0.86, 0.94] |

## Reported beside (decided by nothing)

### The prior's own effect

ctl-carry ÷ ctl-prior shares the carried start, so it isolates the prior:

| split | ctl-carry ÷ ctl-prior |
|---|---|
| weak | 1.14 [1.03, 1.27] |
| other | 1.22 [1.11, 1.34] |
| contact 1 | 1.16 [1.07, 1.26] |
| contact 2 | 1.22 [1.09, 1.36] |

On this seed ctl ÷ ctl-carry is 0.95 [0.89, 1.02] on contact 1. That is level with spec 026's
1.017, but on the other side of 1. So `ctl-carry`'s start is no help here, and the prior is what
helps.

### Typical window

From `supplement.json`, trimmed 10% at both ends:

| split | trimmed geometric mean | median | windows better | ×2 better / worse |
|---|---|---|---|---|
| weak | 1.07 [0.97, 1.17] | 1.03 | 54% | 13% / 11% |
| other | 1.10 [1.03, 1.19] | 1.03 | 56% | 17% / 10% |

The gain is small in the typical window and broad, not a tail.

### Where the gain sits

The gain is mostly a better estimate of the same history, not a different history. Among
windows where `ctl` and `ctl-prior` declare the same number of manoeuvres:
- other: 1.13 [1.02, 1.26], 205 windows;
- weak: 1.12 [0.98, 1.29], 152 windows.

Where the declared histories differ the intervals are wide: other 1.23 [0.88, 1.75] over 35
windows; weak 1.06 [0.79, 1.45] over 63.

### Other comparisons

- **Contact-1 windows near a gap** (the contact-1 part of the weak split): 0.98 [0.79, 1.25],
  59 windows. The prior adds nothing measurable after a gap.
- **Guard:**
  - It fell back on 8 windows. On those, the unguarded answer was 1.85 times `ctl`'s error
    (ctl ÷ noguard 0.54), so the guard removed real damage.
  - Over all windows, guarded and unguarded are nearly equal: weak 1.105 against 1.099.
- **References**, as ÷ ctl-prior:
  - C″ is 2.9–4.9 times ctl-prior's error.
  - The fit told the true manoeuvre history is 0.72 (weak) and 0.86 (other) times it.
- **Duration:** 6 h 1.12 [0.97, 1.28]; 12 h 1.13 [1.03, 1.26].
- **Cost:** the prior's two searches took 18.6 of 75.9 hours, about 24% of the run.
- **Answered:** 76% of windows for every system.

## What this does and does not support

- **Registered question:** does the prior help where the window's own geometry is weak? Not
  shown.
- **What the test does show:** carrying the previous window's state as a prior gives a small,
  broad improvement of about 10% in the geometric mean (3% in the median window). It is
  clearest on the tended contact's ordinary windows, in range and course. It comes mostly from
  a better estimate of the same manoeuvre history. The prior does not narrow which history is
  chosen.
  - The registered rule did not ask this question, so it is a reading, not a decision.
- **Weak split:** it is mostly contact 2 (156 of 215 scored windows). The "at most one ownship
  turn" clause never fires in this simulator.
