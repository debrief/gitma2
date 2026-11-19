---
title: "Long engagements: the previous window as a prior"
date: 2026-11-19T12:00
tags: [write-up, spec-028]
---

Spec 026 found that handing the previous 2-hour window's track to the next window as a starting
guess changed nothing in accuracy. The owner expected more: "knowledge of the previous track can
usefully constrain the range of permutations for this leg".

This study tests that expectation as a prior. The previous window hands on its estimate of the
target's position, course and speed at the next window's first row, with its uncertainty.
That estimate enters the next window's fit and the evidence that ranks manoeuvre histories.

The registered rule's output is **not shown, at this size**, with **no harm** anywhere. Beside
the rule, the prior gives a small average shift: about 10% in geometric mean and 3% in the
median window. Spec: `specs/028-carry-prior/`. Record: `experiments/20261119-cp/`.

<!-- truncate -->

## What was registered

**Design** (decision record `experiments/20261119-cp-decision/`, before seeds 355 and 356
existed):
- **Systems:** `ctl`, `ctl-carry` (spec 026's carried start) and `ctl-prior` are solved on every
  window of a chain, in one job per contact.
- **The hand-over:**
  - The carried estimate uses no bearing the next window also uses.
  - Its Laplace covariance is scaled by 4 and widened for manoeuvres the earlier bearings could
    not yet show.
  - A χ²(4) guard drops the prior where the window's own bearings reject it.

**The rule:** ctl ÷ ctl-prior per window, with the engagement bootstrap and each chain's first
window excluded.
- **Gain:** the lower limit is above 1 on windows of weak geometry: the untended contact, a
  window near a contact gap, or one with at most one ownship turn.
- **Harm:** an upper limit is below 1 on any split, in range, course or speed.

## What happened

**Test** (seed 356, 60 realistic engagements of 6 and 12 hours, both contacts, scored once):

| split | ctl ÷ ctl-prior, range |
|---|---|
| **weak geometry (registered)** | **1.105 [0.963, 1.273]** |
| other windows of the tended contact | 1.14 [1.035, 1.27] |
| tended contact | 1.11 [1.006, 1.22] |
| untended contact | 1.16 [0.988, 1.37] |

The panel's sensitivities do not change the outcome:
- clustered by engagement, the weak split is 1.105 [0.951, 1.279];
- without the 13 windows where nothing was handed on, it is 1.112 [0.964, 1.297].

**Soundness:**
- 720 of 720 windows ran.
- On the tended contact, the carried 95% region covered the truth 95.3% of the time.

## What the panel narrowed

The panel was three reviewers, each approve with findings (`experiments/20261119-cp/review.md`).

- **The owner's case was not sampled.** The ownship turns every 20–40 minutes, so a window with
  no useful ownship manoeuvre never occurs in this simulator. The weak split is in effect the
  untended contact plus windows near gaps. On the gap windows of the tended contact the ratio
  is 0.98 [0.79, 1.25].
- **What the prior does, beside the rule:**
  - About 1.1 in geometric mean on the tended contact's ordinary windows, in range and course,
    on validation and test.
  - The median window is 1.03 and 44% of windows are worse. That is an average shift with many
    losses.
  - It is not concentrated where the declared manoeuvre count changed. Whether the same history
    was kept was not tested.
  - So "narrows the permutations" is not shown, either way.
- **The prior against the carried start alone:** ctl-carry ÷ ctl-prior is 1.14 to 1.22 on every
  split. On this seed `ctl-carry` itself was level with `ctl` (0.95).
- **The guard did what it was for.** It fell back on 8 of 443 windows. There, the unguarded
  answer was 1.85 times `ctl`'s error.
- **Forecasts:** two of five were wrong, the other split's sign and the coverage level. Twelve
  tuning engagements had no forecast value.
- **Registration:**
  - The registered settings were extrapolated from a grid, not run as a chain on tuning.
  - The coverage check covered only the tended contact, while the decided split is mostly the
    untended one (coverage 0.76 on validation).
- **A recorded defect:** the hand-over's refit starts from the full window's fit. On flat
  valleys it can keep information from the overlap, counting those bearings twice. At this
  study's scale coverage did not show it.

## What it costs

The prior's searches add about 24% to the run's search time. The fit told the true manoeuvre
history is still 0.72 to 0.86 times `ctl-prior`'s error. On 12 tuning pairs, spec 025's joint
solve over two windows was 1.7 times better, at three times the time.

## Next (the owner's choice)

- **Recommended default:** adopt `ctl-prior`, with its guard, as the standing chained system
  for tended contacts up to 12 hours, scoped as "a small refinement, no harm shown". Then close
  the long-engagement track as a simulation study.
- **The test that answers the owner's question:** a simulator option where the ownship holds
  course for one to two hours, with `ctl-prior` scored there. It is cheap.
- **The larger lead:** a registered joint solve over consecutive windows. It is 1.7 times
  better on 12 pairs, at three times the cost.

Slides: [the slides post](/blog/2026/11/19/carry-prior-slides).
