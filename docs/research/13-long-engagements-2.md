# 13. Long engagements, part 2: carrying state, an incremental C, realism (spec 024)

**Status**: investigation, 2026-11-18. Not a gate, nothing trained, no GPU, no new seed. Record:
`experiments/20261117-long2/` (`tables.md` generated from `summary.json`; CI run 44153682342,
66 jobs, AMD EPYC 9V74). One engagement per duration (6, 12, 24, 48 hours; seed 348): every
figure is an anecdote about four engagements, not a rate. Follows note 12, whose three
recommendations the owner asked to be implemented.

## What was built

1. **Carry state between time-late windows** (`long/carry.py`). `ctl-carry` is the standing
   control `ctl` with its start from nothing replaced by a start from the previous window:
   - the declared track on the rows the windows share;
   - the declared manoeuvres inside the overlap;
   - C″'s answer after the overlap.

   Both are solved on every window from the same pieces. This `ctl` equals spec 023's runner
   within 1 mm on the same machine (`ctl-check.json`).
2. **An incremental C** (`long/incremental.py`). It runs one confirmation, C″'s and E-s's, per
   2-hour block of estimates, on the block plus the two hours before it. Each estimate keeps the
   confirmed segmentation of its last 720 rows. With one estimate per block it is spec 023's
   per-window run exactly (unit test).
3. **Realism** (`long/sim.py` `_World`, `configs/long/realistic.json`), drawn from a stream of
   its own. Contact 1's target and bearing noise are therefore spec 023's, and the comparison is
   paired.
   - The ownship steers on measured bearings and a range belief with 30% log error. With no
     contact it closes on where it last believed the target to be.
   - Contact gaps of 10–60 minutes, at 0.15 an hour.
   - Detection is one half at 40 km and 4 km wide.
   - A second target that the ownship does not manoeuvre for. Its bearings are swapped half the
     time where the two contacts are within 1°.

## What was found

### 1. Carrying state: cheaper search, no accuracy gain shown

Window by window, ctl ÷ ctl-carry in median range error:

| set | windows | carry better / worse / level | twice better / twice worse | search CPU h, from nothing / from the carry |
|---|---|---|---|---|
| spec 023's engagements | 60 | 15 / 20 / 25 | 3 / 4 | 1.92 / 1.08 |
| realistic, contact 1 | 60 | 22 / 11 / 26 | 7 / 3 | 2.20 / 1.32 |
| realistic, contact 2 (windows with bearings) | 20 | 6 / 4 / 10 | 1 / 0 | 0.51 / 0.20 |

- The median per-window ratio is 1.00 in every set and length (0.97 to 1.02).
- Stitched over whole engagements, `ctl-carry` and `ctl` agree within about half a percentage
  point of range error, in both directions.
- The start from the carry costs about 55% of the search time of the start from nothing it
  replaces. That is about 13% of each window's total, which is dominated by C″, the start from
  C″ and the reference.
- On realistic contact 1 the carry wins more windows than it loses (22 to 11). On spec 023's
  engagements it loses more than it wins (15 to 20). With 60 windows each and one engagement per
  length, neither is evidence of a direction.
- **Reading**: carrying state as built here is an efficiency measure, not an accuracy one. The
  evidence search already reaches the same histories from C″'s start and from nothing.

### 2. The incremental C: cheaper, and worse later in each block

Seconds per estimate (E + C″, one core):

| | 6 h | 12 h | 24 h | 48 h |
|---|---|---|---|---|
| per window (spec 023) | 52.6 | 68.0 | 68.5 | 73.4 |
| incremental C | 31.8 | 36.3 | 41.7 | 40.1 |

Median relative range error, E and C″, on spec 023's engagements:

| | 6 h | 12 h | 24 h | 48 h |
|---|---|---|---|---|
| per window E / C″ | 17.4 / 23.2% | 17.5 / 17.1% | 14.3 / 13.2% | 20.9 / 19.9% |
| incremental E / C″ | 24.6 / 19.2% | 21.9 / 21.1% | 29.8 / 25.6% | 35.6 / 37.2% |

- It is about 1.7 to 1.8 times cheaper per estimate, and markedly worse at 24 and 48 hours.
  The share answered also falls, from 0.99–1.00 to 0.93–0.95.
- **Where**: by an estimate's position in its block (`block-position.txt`, 24- and 48-hour
  engagements), the first estimate of a block matches the per-window run. Medians are 0.156
  against 0.156, and 0.212 against 0.200; the first estimate has exactly the per-window inputs,
  and is identical in 50–71% of cases across the two CPU families. From positions 4–6 on, the
  incremental estimate is two to four times worse (0.37–0.51 against 0.08–0.25).
- The loss therefore comes from deciding the segmentation on up to two more hours of history and
  then cropping it, not from the final solve. Which part does it is **not established**. The
  candidates are not tested:
  - C's tests and E-s were set and trained on windows that begin at an engagement's start and
    are at most two hours long;
  - a leg or transition cut by the crop is handed to the layer as if it began at the window's
    first row.
- **Reading**: as built, the incremental C trades accuracy for cost and should not replace the
  per-window run. Shorter blocks (10–30 minutes) would recover part of the cost saving at less
  history beyond the window. They were not measured.

### 3. Realism

| | 6 h | 12 h | 24 h | 48 h |
|---|---|---|---|---|
| contact 1: bearings held | 67% | 82% | 85% | 83% |
| contact 1: ctl (spec 023's engagement, same target) | 1.7% (1.6%) | 2.1% (1.9%) | 2.2% (2.1%) | 1.5% (1.7%) |
| contact 2: bearings held | 82% | 22% | 20% | 10% |
| contact 2: ctl, on windows with ≥ 5 min of bearings (rows answered) | 6.9% (100%) | 5.9% (51%) | 7.3% (51%) | 8.4% (13%) |
| contact 2: true-history fit, same rows | 1.8% | 2.4% | 3.5% | 4.5% |

- **Contact 1**: the time-late control is unchanged in range error by the ownship steering on
  what it believes, by 15–33% of bearings lost, and by mis-association. It is level with spec
  023's engagements within the CPU-family noise of note 12. Manoeuvres falling in gaps are missed
  (6 hours: 11 declared of 14). The real-time systems are within the per-length spread they
  already had. Over 48 hours the ownship lost contact at 16 of 92 leg starts, and range reached
  80 km once.
- **Contact 2**: the contact the ownship does not manoeuvre for drifts away. Its median range is
  27–147 km and it is held 10–22% of the time beyond 6 hours. On the windows with at least five
  minutes of its bearings, the control's range error is 6–8%, three to five times contact 1's. The true-history fit is also two to three times
  contact 1's, so most of that is the geometry, not the search. This is the cost of an untended
  contact on the information itself.
- Only a handful of bearings were swapped: 0 to 8 per engagement, because the two contacts'
  bearings rarely come within 1°. Mis-association is therefore not exercised by these
  engagements.

## What this changes in note 12's list of challenges

- **"`ctl` on a whole long period"** stands. Chaining windows works, and carrying state does not
  improve it.
- **"E's window: every estimate re-runs C"**: the cost can be cut by 1.7×, but the incremental
  form loses accuracy. The challenge is open.
- **"The scenario is kind"**: for the tended contact, the standing time-late system tolerates
  these gaps and steering errors. An untended contact is the harder case, and the realistic
  scenario now shows it.

## The registered study (proposed; the owner's choice)

Note 12 put a registered study after realism. Proposed design (no seed spent yet):

- **Estimands**:
  - **E1** `ctl-carry` against `ctl`: the paired per-window ratio, non-inferiority at 0.95 on
    the geometric mean, with the CPU saving reported.
  - **E2** the cost of an untended contact: ctl's error on contact 2 ÷ on contact 1 over held
    windows, matched by range band.
  - **E3** the IMM's degradation with engagement length.
- **Data**: 6- and 12-hour realistic engagements only, 30 of each, at about 160 CPU-hours.
  48-hour engagements cost too much per sample to give rates.
- **Seeds**: 349 tuning, 350 validation, 351 test, registered in a decision record before any is
  generated.
- **Not in it**: the incremental C, until a block length that does not degrade is found on
  tuning data.

## Recommendation

1. Keep `ctl`. Carry `ctl-carry` only as a cost measure, if the cost matters.
2. Do not adopt the incremental C as built. If the real-time cost matters, measure shorter blocks
   on tuning data first.
3. Run the registered study above (E1–E3), or stop the long-engagement track here. The owner's
   choice.

## Decision, 2026-11-21 (owner)

The owner adopted 2-hour `ctl-prior` (`tma2-long carry2`, spec 028's registered settings) as the
standing chained time-late system for the tended contact, up to 12 h. `ctl` remains the control,
and the joint solve is the equal alternative where the bearings are kept. The evidence and its
limits are in spec 028 (`experiments/20261119-cp/`), spec 031 (`experiments/20261120-cmp/`) and
spec 032 (`experiments/20261120-legs/`). The limits:
- one simulator, contact 1;
- the gain on blind windows is far-range;
- windows are placed past true manoeuvres;
- the carried covariance is not calibrated;
- the hand-over defect is kept.
