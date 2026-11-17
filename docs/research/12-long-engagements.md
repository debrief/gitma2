# 12. Longer engagements: 6 to 48 hours (spec 023, issue #42)

**Status**: investigation, 2026-11-17. Not a gate, nothing trained, no GPU. Record:
`experiments/20261117-long/` (`tables.md` generated from `summary.json`). One simulated
engagement per duration (seed 348), so every figure here is an anecdote about four engagements,
not a rate.

## Question

The owner asked (issue #42) what it would take to apply our TMA to engagements of 6, 12, 24 and
48 hours, and to show such engagements on the viewer and time-late pages.

## What was done

1. **A long-engagement simulator** (`src/tma2/long/sim.py`), separate from generator 0.6.0 so
   that its output stays byte-identical. The target follows Annex B's statistics (legs of
   N(25, 9.1) minutes, at least 5; 80% course, 10% speed, 10% both; 30–120° turns at 0.25–1°/s).
   The ownship runs 20–40 minute legs with a turn at the start of each, alternating the side of
   the line of sight, and keeps the target between 3 and 25 km by closing (sprinting at 11 m/s)
   or opening on the next leg. It steers on the true target position.
2. **Windows** (`src/tma2/long/windows.py`): a long engagement is cut into windows that every
   estimator already reads (time from 0, positions from the ownship's at the window's start,
   truth re-indexed).
3. **Real-time** (`src/tma2/long/realtime.py`): every 10 minutes, E (the carried Gate 2 model,
   its exported graph) and C″ on the last 2 hours, one leg on the last 30 minutes, and the IMM
   over the whole engagement.
4. **Time-late** (`src/tma2/long/timelate.py`): the standing control `ctl` on a chain of 2-hour
   windows overlapping by 30 minutes, stitched at the overlaps' middles; and `ctl` timed on
   single periods of 0.5 to 6 hours.
5. **Pages**: a long-engagement section on `/viewer` and on `/timelate`, precomputed in Python.

## What was found

All numbers are from `experiments/20261117-long/tables.md` (CI run 44090506705, AMD EPYC runners,
one core a job). Medians are over the rows a system answered under the project's plausibility
rule (range at most 100 km, speed at most 25 m/s).

### It runs, on windows

Every system ran to the end of all four engagements, in 33 CI jobs (about 25 CPU-hours).

| | 6 h | 12 h | 24 h | 48 h |
|---|---|---|---|---|
| target manoeuvres / ownship turns | 14 / 12 | 26 / 22 | 58 / 50 | 106 / 92 |
| time-late `ctl`, median range error | 2.0% | 1.9% | 2.7% | 1.6% |
| time-late C″ read as a track | 20.5% | 15.0% | 8.5% | 9.0% |
| true-history fit (a reference, told the times) | 0.6% | 0.8% | 0.7% | 1.2% |
| real-time E, every 10 min | 17.4% | 17.5% | 14.3% | 20.9% |
| real-time C″ | 23.2% | 17.1% | 13.2% | 19.9% |
| real-time IMM (answered) | 19.0% (1.00) | 35.2% (1.00) | 15.0% (0.96) | 30.9% (0.81) |

- **Time-late holds up.** Stitched from 2-hour windows, `ctl` keeps its usual accuracy at every
  length. Error within 15 minutes of a seam is no worse than elsewhere (1.4–3.2% against
  1.6–2.5%). It declared 14, 24, 56 and 101 manoeuvres against 14, 26, 58 and 106 true
  (counts, not matched one by one).
- **Real-time is as good as its window.** E and C″ see two hours; their median range error is
  13–21%, much of it in the minutes after a target manoeuvre, and it swings by block (6–59% over
  six-hour blocks of the 48-hour engagement). These rows are every 10 minutes, not Gate 2's
  scored rows, so the figures are not comparable with Gate 2's.
- **The IMM degrades over a long engagement.** Over 48 hours it answers 81% of evaluations and its
  six-hour block medians reach 61–78% in the last twelve hours; over 24 hours it is the best
  real-time system in two blocks. One engagement cannot say whether that is drift, the ownship's
  sprints or this target.

### What would not work as it stands

1. **`ctl` on a whole long period.** On one period of the 24-hour engagement, its run time grows
   faster than the period: 1.0 min (0.5 h), 3.1 (1 h), 9.1 (2 h), 28 (3 h), 41 (4 h), 114 (6 h).
   Its search allows at most ten manoeuvres (`max_manoeuvres`), which 4 hours already exceed
   (11 true, 10 declared; 6 hours: 16 true, 10 declared). A 48-hour period holds about 100.
2. **E's window.** The exported graph takes exactly 720 rows (2 hours at 10 s). E cannot use
   anything older than two hours, and every estimate re-runs C's confirmation over the whole
   window: 27–37 s per estimate on one core, flat in engagement length but far from a
   bearing-by-bearing update.
3. **The IMM's cost.** Filtering the whole engagement once took 6 s (6 h), 8 s (12 h), 57 s
   (24 h) and 426 s (48 h) on 10-second data: it grows much faster than linearly. The cause is
   not established.
4. **The Cramér–Rao bound over a whole engagement** (`timelate.bound.period_bound`): 0.5 s and
   0.4 GB at 6 hours, 9 s and 1.0 GB at 24 hours, 59 s and 4.5 GB at 48 hours
   (`bound-cost.jsonl`). Every efficiency figure the project reports needs it; past 48 hours it
   needs a windowed form.
5. **Single-zig assumptions.** C″'s zig veto, the IMM's start and the real-time rows' "five
   minutes after the zig" read one `zig_index`. On long engagements the veto had to be applied
   at every ownship turn (`windows.turns_veto`); the IMM starts after the first turn only.
6. **Generator 0.6.0.** Its table holds 32 target changes (about 14 hours of Annex B legs at
   their mean length, under 3 hours at their shortest) and its ownship makes one zig and an optional second. The long
   simulator is separate; making it the generator would need a schema change and conformance
   fixtures of its own.
7. **The browser.** At 10-minute steps a 48-hour engagement is about 290 estimates, each needing
   C's segmentation of a fresh 2-hour window: about 290 live runs of C in JavaScript (25–93 s
   per 2-hour engagement in spec 021), or 290 sets of precomputed graph inputs whose size was not
   measured here. The pages show Python's estimates instead.

### Not measured here

- **Realism of the scenario.** The ownship steers on the true target; contact is never lost; one
  target for 48 hours; bearing noise is stationary. Each of these would matter more over 48 hours
  than over two.
- **Geometry.** Over 48 hours the target travels hundreds of kilometres; windows are re-centred on the ownship, so the
  flat-earth model is used over at most a few tens of kilometres at a time (its error over
  150 km, about 1 part in 10^4, is far below the bearing noise's effect).
- **Rates.** Four engagements give anecdotes. A study with error rates would need tens of
  engagements per duration: about 25 CPU-hours each at this cost.

## Recommendation (the owner's choice)

1. **Carry state between windows** (recommended first): start each time-late window from the
   previous window's solution and prior, and each real-time estimate from the last confirmed
   legs, instead of re-solving cold. This is the cheapest change that makes long engagements a
   chain rather than a pile of independent windows.
2. **An incremental C**, keeping confirmed legs and dropping old ones, so a real-time estimate
   costs the same at hour 48 as at hour 2.
3. **Realism before rates**: the ownship steering on its own solution, contact gaps and a second
   target, then a registered study on a fresh seed (the next is 349).
