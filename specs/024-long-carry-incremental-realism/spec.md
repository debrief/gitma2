# Feature Specification: Long engagements, the three recommendations of note 12

**Feature Branch**: `024-long-carry-incremental-realism` (developed on `ccr-fd0a0c59-4nxg4k`, PR 46)

**Created**: 2026-11-17

**Status**: Implemented (an investigation, not a gate; nothing trained; no GPU; no new seed)

**Input**: Owner, 2026-11-17, on PR 46: "implement 3 recommendations". Note 12's recommendations:
1. carry state between windows;
2. an incremental C;
3. scenario realism before a registered study.

**SRD traceability**: §1 (scope), §7 (the site). No gate criterion is touched; nothing registered.

## Decisions taken (AGENTS.md: decide and record)

- **Carry (1)** is built for the time-late chain, where it is a real change to the search.
  `ctl-carry` is `ctl` with its start from nothing replaced by a start from the previous
  window: the declared track where the windows overlap, the declared manoeuvres inside the
  overlap, and C″'s answer after it. `ctl` and `ctl-carry` are solved side by side on every
  window from the same pieces (`long/carry.py`). `ctl` is checked against spec 023's record.
  For the real-time systems, "start from the last confirmed legs" is what the incremental C
  does, so (2) covers it.
- **Incremental C (2)**: one confirmation (C″'s, and E-s's) per *block* of evaluations, on the
  block plus the two hours before it. Each estimate keeps the confirmed segmentation of its last
  720 rows (`long/incremental.py`). With one evaluation per block it is spec 023's per-window
  run, row for row (unit test). Block length: 2 hours.
- **Realism (3)** (`configs/long/realistic.json`, `long/sim.py` `_World`): all drawn from a
  stream of its own, so on seed 348 the first target's track and bearing noise are spec 023's
  and the comparison with spec 023 is paired.
  - The ownship steers on its measured bearing and a range belief, true × exp(0.3 · N(0, 1)),
    instead of the truth. When it has no contact, it closes on where it last believed the
    target to be.
  - Contact gaps of 10–60 minutes, at 0.15 an hour for each contact.
  - Detection falling off with range: one half at 40 km, 4 km wide.
  - A second target with Annex B's statistics, for which no ownship manoeuvre is planned.
    Where both contacts are reported within 1°, their bearings are swapped with probability
    one half (mis-association).
- **The registered study** that note 12 put after realism is **not run here**: it needs a
  decision record and fresh seeds, and it should be designed on what this investigation shows.
  It is proposed in note 13 with its estimands. Alternative considered: registering it now,
  which would fix estimands before knowing whether the second contact can be scored at all.
- No new seed: spec 023's seed 348 with the realism stream; the next fresh seed is still 349.

## Requirements

- **FR-001** `ctl-carry` beside `ctl` on every window of the four engagements, with each
  window's run time and its search time split by start.
- **FR-002** The incremental real-time run on the four engagements: its estimates and its run time
  per estimate, beside spec 023's per-window run.
- **FR-003** The realistic engagements, contacts 1 and 2: the incremental real-time run, `ctl` and
  `ctl-carry`. Contact 1 is paired with spec 023's engagement.
- **FR-004** A record (`experiments/20261117-long2/`, tables generated), note 13, page sections,
  kickoff and slides posts.

## Success criteria

- **SC-001** Every run finishes on CI. Spec 023's `ctl` is reproduced within the solver's
  tolerance on the windows checked.
- **SC-002** The incremental run equals the per-window run for blocks of one evaluation (unit
  test), and its cost per estimate is reported.
