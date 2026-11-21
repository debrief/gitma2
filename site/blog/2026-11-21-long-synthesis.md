---
title: "The long-engagement track as a whole: what seven studies established, and what they did not"
date: 2026-11-21T15:00
tags: [write-up, spec-034]
---

The long-engagement track asked whether the project's time-late system holds up over engagements of
hours rather than one two-hour period, and whether carrying information from one window to the
next makes it better. Seven studies, all in one simulator, give these answers:
- **Stitched 2-hour windows held up on the tended contact.** The registered study covered 6 to 12
  hours. Beyond that there is one engagement each at 24 and 48 hours, which are anecdotes.
- **A carried start is not shown to help accuracy.** It saves about 31% of the search where it
  runs, and on its own it can cost accuracy.
- **A carried prior beats the same window alone where that window cannot see range.**
  - On 1-hour windows it reads about 1.7 to 2.4.
  - On 2-hour windows it reads 1.54 on one seed and 1.37 pooled over three, all of it beyond
    35 km.
  - Against a joint solve over the same past bearings it is not shown to be better.

The owner adopted 2-hour `ctl-prior` on 2026-11-21. This post closes the track unless the owner
reopens it.

Spec: `specs/034-long-synthesis/`. Figures of record:
`experiments/20261121-long-synthesis/tables.md`, generated from the test records by
`scripts/research/long_synthesis.py`. Two reviewers checked this account against the records
before it was published: `experiments/20261121-long-synthesis/review.md`.

<!-- truncate -->

## The question

Real engagements last hours. The project's time-late system, `ctl` (the evidence search with a
declared history, from the time-late track), works on one period of up to two hours. The track
asked three things:
- whether `ctl` on overlapping windows, stitched together, keeps its accuracy over 6 to 48 hours;
- what the real-time systems and the IMM do over the same spans;
- whether information carried from one window into the next (a start, then a prior) improves the
  next window.

Everything here comes from one simulator (`src/tma2/long/sim.py`) with Annex B targets. Spec 023's
ownship steered on the true target. From spec 024 on, a realism layer added steering on measured
bearings with a ±30% range belief, gaps, detection that falls to 50% at 40 km, and a second
contact. Those realism settings were chosen by hand, not measured. Nothing was trained.

## What is standing

**`ctl` on 2-hour windows overlapping 30 minutes, stitched mid-overlap** (spec 023). This is the
time-late system for long engagements, and the control in every later study.
- **Latency:** a window answers only when it closes, so each estimate comes up to 2 hours after
  the earliest bearing it uses.
- **Manoeuvre cap:** `ctl` declares at most ten manoeuvres per window.

**2-hour `ctl-prior` for the tended contact, up to 12 hours** (adopted by the owner, 2026-11-21).
This is `ctl` with the previous window's state and covariance carried in as a Gaussian prior. The
prior is widened (scale 4, tail 1,200 s) and guarded by a χ²(4) test at α 0.001 (spec 028). Its
faults stand beside its gains:
- **Where the gain is.** On blind 2-hour windows the gain is a far-range effect: about 2.2 beyond
  35 km and about 1.0 under.
  - It was read on the half of blind windows where contact held: 85 of 165, with 80 lost to
    contact.
  - Range and contact loss move together in this design, so they cannot be separated.
  - The prior was handed on from a window containing an ownship turn in 83 of 85 cases.
  - Across seeds it read 1.32, 0.87 and 1.54.
  - It was decided on contact 1 only, in one simulator.
- **The carried covariance is not calibrated.** It is too wide in the core and too narrow in the
  tail, and covers 0.79 across an ownship turn, so it must not be shown as an uncertainty.
- **The guard rarely fires:** 1.8% of guarded windows in spec 028, none of the blind windows in
  spec 032.
- **Known defect:** the hand-over refit starts from the full-window fit, so it can keep overlap
  information. Spec 028 recorded this and did not repair it.
- **Placement:** every chained study placed its windows past true target manoeuvres, so no
  hand-over ever fell inside one.
- **Cost:** the job that runs `ctl-prior` alongside `ctl`, `ctl-carry` and a no-guard variant
  cost about 190–320 CPU-seconds per engagement-hour (specs 031 and 032). The cost of
  `ctl-prior` alone was not separated.

## What was shown

### Feasibility: specs 023 and 024

These ran one engagement per length, so they are anecdotes, not results.
- **Stitched `ctl`** held 1.6–2.7% median range error at 6, 12, 24 and 48 hours, with no penalty at
  the seams.
- **The real-time systems** (the carried model E and C″) sat at 13–23%.
- **The IMM** degraded over 48 hours and answered 81% of evaluations.
- **With spec 024's realism,** the tended contact stayed at 1.5–2.2%. The untended contact (the
  one the ownship does not steer for) kept only 10–22% of its bearings beyond 6 hours. Where it
  was held, `ctl` was at about 6–8%.
- **Run time:** one `ctl` period took 1 minute at 30 minutes long and 114 minutes at 6 hours, which
  is why the windows are 2 hours. A real-time estimate cost 27–37 s.
- **An incremental C** was 1.7× cheaper and less accurate, so it was not adopted.

### The registered studies

Each ratio is one system's median range error over another's, as a geometric mean over windows.
Rows marked † read the other way: above 1 means the untended contact is worse, or that the IMM
drifts. Everywhere else, above 1 means the carried system is better. The full table, with spread,
counts and conventions, is in `tables.md`.

| spec | question | ratio | median window | outcome |
|---|---|---|---|---|
| 026 | carried start, tended contact | 1.017 [0.958, 1.082] | 1.00 | non-inferior |
| 026 | untended ÷ tended contact † | 1.466 [1.119, 2.052] | – | untended worse |
| 026 | IMM hours 6–12 ÷ 0–6 † | 1.056 [0.819, 1.309] | – | drift not shown |
| 028 | carried prior, weak split | 1.105 [0.963, 1.273] | 1.03 | not shown, at this size |
| 029 | carried prior, blind 1 h windows, against the same window alone | 2.414 [2.062, 2.825] | 2.15 | gain |
| 031 | 2 h `ctl` ÷ 1 h `ctl-prior` | 0.730 [0.579, 0.917] | 0.90 | `ctl-prior` worse |
| 031 | joint solve ÷ 1 h `ctl-prior`, same past bearings | 0.774 [0.632, 0.954] | 0.78 | `ctl-prior` worse |
| 032 | carried prior, blind 2 h windows | 1.537 [1.156, 2.029] | 1.25 | `ctl-prior` better |
| 032 | joint 3.5 h ÷ `ctl-prior`, same past bearings | 1.113 [0.840, 1.445] | 1.24 | not separated, at this size |
| 032 | carried prior, one-turn 2 h windows | 1.259 [1.056, 1.500] | 1.21 | no harm |

### Read together

**A carried start (`ctl-carry`) is not shown to help accuracy, and it saves search time.**
- **Non-inferiority rests on ties.** Spec 026's result rests partly on each chain's first window,
  which equals `ctl` by construction. Without those windows it is 1.021 [0.9502, 1.100].
- **The saving:** on the windows that had a carried start, the search took 5.84 hours against 8.50
  from nothing, a 31% saving. Over all windows that is about 7%.
- **Where it leans the other way:**
  - the untended contact, 0.942 (0.920 without first windows);
  - spec 028, ctl ÷ ctl-carry 0.952 [0.893, 1.021] on contact 1;
  - spec 029, 0.89 [0.82, 0.97] on one-turn 1-hour windows.

  So a start is not used without the prior.

**A carried prior beats the same window alone where that window cannot see range.**
- **On 1-hour windows without an ownship turn:** about 1.7 to 2.4. That is spec 029's 2.41, and
  1.71 on spec 031's fresh seed.
- **On 2-hour windows the ownship cannot turn in:** 1.54 on spec 032's test seed, 1.37
  [1.05, 1.80] pooled over three seeds. It is about 2.2 beyond 35 km and about 1.0 under, and the
  median window is 1.25.
- **Where the window can see range,** it is a small average gain with many losses:
  - spec 028's contact-1 windows read 1.11 [1.006, 1.22], median 1.03, which its panel called "an
    average shift with many losses";
  - one-turn windows read 1.22 and 1.26.
- **Every one of these is against the same window alone.** Both panels called that "more data
  beats no data".

**Spec 028's weak split was not the owner's case.** Spec 028 was registered to test the
blind-window case, but the clause that should have found windows without a useful ownship turn
never fired: with turns every 20–40 minutes, a 2-hour window is never blind in this simulator. The
decided weak split was in fact the untended contact plus contact-1 windows near a gap. Clustered
by engagement, its interval is [0.951, 1.279] (spec 028's panel).

**The prior is a summary of past bearings, and it is not shown to beat having them.**
- **On 1-hour windows** it lost to a joint solve over the same past bearings (spec 031): 0.774,
  median 0.78. `ctl-prior` was better in about 4 windows in 10.
- **On 2-hour windows** it was not separated from a 3.5-hour joint solve (spec 032): 1.11, or 1.02
  with engagements weighted equally.
- **Its practical case is a compact hand-over:** four numbers and a covariance in place of hours of
  bearings.

**2-hour windows beat 1-hour `ctl-prior`, but not on equal terms** (spec 031).
- Both 2-hour `ctl` (0.730) and 2-hour `ctl-prior` (0.488) beat it.
- The stitched 2-hour rows include an ownship turn in 98% of windows and a median of 29 minutes of
  bearings after the hour.
- The like-for-like comparison is the joint solve above.
- 2-hour `ctl-prior` against 2-hour `ctl` was supplement only.

### Median range error on the windows each study decided

| study | `ctl` | `ctl-prior` | 2 h `ctl` | joint | reference told the truth |
|---|---|---|---|---|---|
| 028, all windows after each chain's first, both contacts (not the decided split) | 2.5% | 2.1% | – | – | 1.6% |
| 029, blind 1 h windows | 22.7% | 7.4% | – | – | 13.6% |
| 031, blind 1 h windows | 22.4% | 10.2% | 9.0% | 7.0% | 3.1% |
| 032, blind 2 h windows, contact held | 16.7% | 10.4% | – | 12.8% | 3.3% |

- **The reference is no ceiling.** It is fitted on its own span, so it cannot be a ceiling for a
  system that carries information in. That is why spec 029's reference is worse than `ctl-prior`.
- **2-hour `ctl-prior` in spec 031** reached 4.2% on the same windows, using the later bearings
  described above.

## What was withdrawn or corrected along the way

- **Spec 029's 1-hour recommendation is withdrawn.** It measured "more data beats no data", and
  spec 031 showed that a joint solve over the same past beats it.
- **Spec 028's "narrows the permutations"** (the owner's hypothesis about manoeuvre histories) is not
  shown either way. History counts were never measured.
- **Spec 031's tuning pointed the wrong way** (D1 1.30). The panel gave a likely cause: the tuning
  compared runs on two CPU families, on about 34 windows.
- **Spec 032 decided only half its blind windows** (85 of 165). The other 80 had lost contact. The
  study forecast 120 decided windows and got 85.
- **Single seeds swing.**
  - Spec 032's E1 read 1.32, 0.87 and 1.54 across tuning, validation and test.
  - Joint ÷ `ctl` read 1.25, 1.46 and 0.72; pooled it is 0.87 [0.67, 1.11], not separated.
  - Read pooled figures, not single seeds.

## What was never tested

- **Real bearings.** Every figure comes from one simulator whose realism was set by hand.
- **Bearing errors outside the generator's own family.** The time-late track showed `ctl` knows
  that family, and that outliers, correlated errors and bias cost it.
- **Targets that do not follow Annex B.**
- **The untended contact under a carried prior,** beyond spec 028's weak split, which was mostly
  that contact (1.105, not shown). The untended contact is the harder case: spec 026 found it about
  1.3–1.5 times worse at matched range.
- **Association between contacts,** beyond spec 024's 1° swaps.
- **An ownship steered by its own estimated track,** and the drift of its range belief over many
  hours.
- **Hand-overs inside a target manoeuvre,** and a repaired, neutral-start hand-over.
- **A calibrated carried covariance.**
- **Registered comparisons beyond 12 hours.** The 24- and 48-hour runs were one engagement each.
- **Lost-contact windows.** Neither 2-hour system answers them. The joint solve's extrapolation
  through them was measured (median error 0.19–0.29) but not registered.
- **Real-time requirements.** Every comparison here is time-late, with up to 2 hours of latency per
  window.

## What would justify reopening the track

- **Measured realism:** real or recorded bearings, with the detection, gaps and errors they
  actually have.
- **An ownship steered by its own track,** or association between contacts.
- **A deployment that needs the untended contact,** or answers while contact is lost. Both were
  outside every decided population.
- **A latency requirement** that 2-hour time-late windows cannot meet.
- **A case where the bearings cannot be kept and only a hand-over can travel.** There the comparison
  against the joint solve stops being the fair one, and the prior's compactness becomes the
  question.

## Related work not covered here

The joined-periods track (specs 025, 027, 030 and 033) asks how to use several short periods of
one target across gaps. It uses a different layout simulator.
- **Spec 025:** the joint solve stands.
- **Spec 027:** a carried start does not substitute for it.
- **Spec 030:** a carried prior helps where a period cannot answer alone. The joint solve stayed
  standing (k4 ÷ joint 1.40, on the line), and the prior's inflation was not shown to matter.
- **Spec 033 (long gaps)** has a spec on main and no test record yet.

## Records

**Test records** (each has its `review.md`):

| spec | record | seed |
|---|---|---|
| 026 | `experiments/20261118-ls/` | 351 |
| 028 | `20261119-cp/` | 356 |
| 029 | `20261119-hold/` | 364 |
| 031 | `20261120-cmp/` | 366 |
| 032 | `20261120-legs/` | 368 |

- **Feasibility:** `experiments/20261117-long/` and `20261117-long2/`, with research notes 12 and
  13.
- **Figures of record:** `experiments/20261121-long-synthesis/tables.md`, with the reviewers'
  `review.md`.
- **Seeds:** none new. The next fresh seed is 369.

Slides: [the slides post](/blog/2026/11/21/long-synthesis-slides).
