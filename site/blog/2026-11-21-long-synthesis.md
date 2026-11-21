---
title: "The long-engagement track as a whole: what seven studies established, and what they did not"
date: 2026-11-21T15:00
tags: [write-up, spec-034]
---

The long-engagement track asked whether the project's time-late system holds up over engagements of
hours rather than one two-hour period, and whether carrying information from one window to the
next makes it better. Seven studies later the answer is short:
- **Stitched 2-hour windows hold up.** On the tended contact, the error does not grow with the
  engagement's length, at least up to 48 hours in one engagement of each length.
- **A carried start does nothing that matters.**
- **A carried prior helps exactly where a window cannot see range by itself.** It is about twice as
  good as the window alone there. Elsewhere it is close to level.

The owner adopted 2-hour `ctl-prior` on 2026-11-21. This post closes the track.

Spec: `specs/034-long-synthesis/`. Figures of record:
`experiments/20261121-long-synthesis/tables.md`, generated from the test records by
`scripts/research/long_synthesis.py`.

<!-- truncate -->

## The question

Real engagements last hours. The project's time-late system, `ctl` (the evidence search with a
declared history, from the time-late track), works on one period of up to two hours. The track
asked three things:
- whether `ctl` on overlapping windows, stitched together, keeps its accuracy over 6 to 48 hours;
- what the real-time systems and the IMM do over the same spans;
- whether information carried from one window into the next (a start, then a prior) improves the
  next window.

Everything here is one simulator (`src/tma2/long/sim.py`, Annex B targets), with realism from
spec 024: measured-bearing steering, gaps, range-dependent detection, a second contact. Nothing was
trained.

## What is standing

- **`ctl` on 2-hour windows overlapping 30 minutes, stitched mid-overlap** (spec 023). This is the
  time-late system for long engagements and the control in every later study.
- **2-hour `ctl-prior` for the tended contact, up to 12 hours** (adopted by the owner, 2026-11-21).
  It is `ctl` with the previous window's state and covariance as a Gaussian prior, widened (scale
  4, tail 1,200 s) and guarded by a χ²(4) test at α 0.001 (spec 028).

  Its faults are recorded beside it:
  - The carried covariance is not calibrated. It is too wide in the core and too narrow in the
    tail, and covers 0.79 across an ownship turn, so it must not be shown as an uncertainty.
  - The hand-over refit starts from the full-window fit, so it can keep overlap information
    (recorded in spec 028, not repaired).
  - Every chained study placed its windows past true target manoeuvres, so no hand-over ever fell
    inside one.

## What was shown

**Feasibility (specs 023 and 024; one engagement per length, anecdotes, not results).**
- Stitched `ctl` held 1.6–2.7% median range error at 6, 12, 24 and 48 hours, with no penalty at
  the seams.
- The real-time systems (the carried model E and C″) sat at 13–21%. The IMM degraded over 48 hours
  and answered 81% of evaluations.
- With spec 024's realism, the tended contact stayed at 1.5–2.2%. The untended contact, which the
  ownship does not steer for, was 10–22% beyond 6 hours.
- `ctl` caps at ten manoeuvres per window and costs 1 minute (30-minute window) to 114 minutes
  (6-hour window) per period.
- An incremental C was 1.7× cheaper and worse, so it was not adopted.

**The registered studies.** In every row, above 1 means the carried system, or the side named, is
better. The full table, with spread and conventions, is in `tables.md`.

| spec | question | ratio | median window | outcome |
|---|---|---|---|---|
| 026 | carried start, tended contact | 1.017 [0.958, 1.082] | 1.00 | non-inferior |
| 026 | untended ÷ tended contact | 1.466 [1.119, 2.052] | – | untended worse |
| 026 | IMM hours 6–12 ÷ 0–6 | 1.056 [0.819, 1.309] | – | drift not shown |
| 028 | carried prior, weak geometry (turning ownship) | 1.105 [0.963, 1.273] | 1.03 | not shown, at this size |
| 029 | carried prior, blind 1 h windows (against the same window alone) | 2.414 [2.062, 2.825] | 2.15 | gain |
| 031 | 2 h `ctl` ÷ 1 h `ctl-prior` | 0.730 [0.579, 0.917] | 0.90 | `ctl-prior` worse |
| 031 | joint solve ÷ 1 h `ctl-prior` (same past) | 0.774 [0.632, 0.954] | 0.78 | `ctl-prior` worse |
| 032 | carried prior, blind 2 h windows | 1.537 [1.156, 2.029] | 1.25 | `ctl-prior` better |
| 032 | joint 3.5 h ÷ `ctl-prior` (same past) | 1.113 [0.840, 1.445] | 1.24 | not separated |
| 032 | carried prior, one-turn 2 h windows | 1.259 [1.056, 1.500] | 1.21 | no harm |

Read together:
- **A carried start is a cost saving, not an accuracy gain.**
  - Spec 026's non-inferiority rests on level windows. Without each chain's first window it reads
    1.021 [0.9502, 1.100].
  - Its gain is in cost: on spec 026's test the searches from the carried start took 5.8 CPU-hours,
    against 10.1 from nothing.
  - On the untended contact it leans the other way (0.942).
- **A carried prior helps where the window is blind to range.**
  - It roughly doubles accuracy on 1-hour windows without an ownship turn (spec 029: 2.41; 1.71 on
    a fresh seed in spec 031).
  - On 2-hour windows the ownship cannot turn in, the gain is about 1.5 (spec 032), concentrated
    beyond 35 km.
  - Where the ownship turns every 20–40 minutes, the windows are rarely blind and the effect is a
    small average shift (spec 028: 1.11 on contact 1, median 1.03).
- **The prior is a summary of past bearings, and it does not beat having them.**
  - Against a joint solve over the same past bearings it lost on 1-hour windows (spec 031: 0.774).
  - On 2-hour windows it was not separated (spec 032: 1.11, 1.02 with engagements weighted
    equally).
  - The practical case for it is a compact hand-over: four numbers and a covariance in place of
    hours of bearings.
- **Longer windows beat a shorter window plus a prior.** In spec 031, 2-hour `ctl` and 2-hour
  `ctl-prior` both beat 1-hour `ctl-prior`. Spec 029's 1-hour recommendation was withdrawn.

**Median range error on the windows each study decided** (from the records):

| study | `ctl` | `ctl-prior` | joint | reference told the truth |
|---|---|---|---|---|
| 028, 2 h windows, both contacts | 2.5% | 2.1% | – | 1.6% |
| 029, blind 1 h windows | 22.7% | 7.4% | – | 13.6% |
| 031, blind 1 h windows | 22.4% | 10.2% | 7.0% | 3.1% |
| 032, blind 2 h windows | 16.7% | 10.4% | 12.8% | 3.3% |

The reference is fitted on its own span, so it is no ceiling for a system that carries information
in. Spec 029's reference is worse than `ctl-prior` for that reason. In spec 031, 2-hour
`ctl-prior` reached 4.2% on the same windows.

## What was withdrawn or corrected along the way

- **Spec 029's recommendation is withdrawn.** It recommended 1-hour `ctl-prior`, a short window
  plus a prior, but that measured "more data beats no data", and spec 031 showed longer windows and
  the joint solve beat it.
- **Spec 028's "narrows the permutations"** (the owner's hypothesis about manoeuvre histories) is
  not shown either way. History counts were never measured.
- **Spec 031's tuning reading (D1 1.30) pointed the wrong way.** It compared runs on two CPU
  families, and was compared across runs. Within one job is the rule.
- **Spec 032's population was half of what was planned.** Holding a 2–4 h leg opens the range,
  80 of 165 blind windows lost contact, and those windows are outside the claim. The study
  forecast 120 decided windows; 85 came.
- **Seed-to-seed swings are large on these sample sizes.**
  - Spec 032's E1 read 1.32, 0.87 and 1.54 across tuning, validation and test.
  - Joint ÷ `ctl` read 1.25, 1.46 and 0.72. Pooled it is 0.87 [0.67, 1.11], not separated.
  - Quote pooled figures, not single seeds.

## What was never tested

- **Real bearings.** Every figure is from one simulator. Its realism (detection 50% at 40 km, gaps,
  a ±30% range belief) was set by hand, not measured.
- **The untended contact under a carried prior,** beyond spec 028's weak split. The contact the
  ownship does not steer for is the harder case (spec 026: 1.47 worse).
- **Association.** Contacts are never confused, beyond spec 024's 1° swaps.
- **An ownship steered by its own estimated track.** It always steered on the simulator's
  measured bearing and range belief.
- **Hand-overs inside a target manoeuvre,** and a repaired, neutral-start hand-over.
- **A calibrated carried covariance.** None was built.
- **Engagements beyond 12 hours** for any registered comparison. The 24- and 48-hour runs were one
  engagement each.
- **Lost-contact windows.** Neither 2-hour system answers them, and the joint solve's
  extrapolation through them is unscored.

## What would justify reopening the track

- Measured realism: real or recorded bearings with the detection, gaps and errors they actually
  have.
- An ownship steered by its own track, or association between contacts.
- A case where the bearings cannot be kept and only a hand-over can travel. There the comparison
  against the joint solve stops being the fair one, and the prior's compactness becomes the
  question.

## Related work not covered here

The joined-periods track (specs 025, 027, 030 and 033) asks how to use several short periods of
one target across gaps. It uses a different layout simulator. There the joint solve stands
(spec 025), a carried start does not substitute for it (spec 027), and a carried prior helps
where a period cannot answer alone (spec 030). Spec 033, on long gaps, is open in another session.

## Records

- **Test records:**

  | spec | record | seed |
  |---|---|---|
  | 026 | `experiments/20261118-ls/` | 351 |
  | 028 | `20261119-cp/` | 356 |
  | 029 | `20261119-hold/` | 364 |
  | 031 | `20261120-cmp/` | 366 |
  | 032 | `20261120-legs/` | 368 |

  Each record has its `review.md`.
- **Feasibility:** `experiments/20261117-long/` and `20261117-long2/`, with research notes 12 and
  13.
- **Figures of record:** `experiments/20261121-long-synthesis/tables.md`, with the reviewers'
  `review.md`.
- **Seeds:** none new. The next fresh seed is 369.

Slides: [the slides post](/blog/2026/11/21/long-synthesis-slides).
