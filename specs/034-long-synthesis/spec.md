# Spec 034: the long-engagement track as a whole (synthesis of specs 023–032)

**Created**: 2026-11-21

**Status**: a synthesis. No gate, no registered result, nothing trained, no new seed.

**Input**: owner, 2026-11-21, after PR 56. Asked about closing the long-engagement track with a
synthesis of specs 023 to 032, the owner answered "yes, please try it". This follows spec 019's
pattern for the time-late track.

**SRD traceability**: §1 (scope), §7 (time-late).

## What this spec does

- **One account of the long-engagement track:** specs 023, 024, 026, 028, 029, 031 and 032.
  - **What stands:** `ctl` on 2-hour windows; `ctl-prior` adopted for the tended contact
    (owner, 2026-11-21).
  - **What each study decided, and under which convention.**
  - **What was withdrawn or narrowed by the panels.**
  - **What was never tested.**
  - **What would justify reopening the track.**
- **Figures of record:** `scripts/research/long_synthesis.py` reads them from the registered test
  records of specs 026, 028, 029, 031 and 032 (`study.json`).
  - It writes `experiments/20261121-long-synthesis/tables.md` and `summary.json`, and the
    figures of the slides post. Nothing is typed by hand.
  - Specs 023 and 024 were one engagement per length, so they are anecdotes. They are quoted
    from their generated `tables.md`.
- **Out of scope:** the joined-periods track (specs 025, 027, 030 and 033) is a different
  simulator and question. It is mentioned only where it bears on the long-engagement track, and
  spec 033 is still open.
- **Review:** reviewers read the account against the records before it is published. Their
  findings go in `experiments/20261121-long-synthesis/review.md`.

## Requirements

- **FR-001:** every number in the tables comes from a committed record, with its system, its
  comparator and its convention stated: which windows, which exclusions, and which contact.
- **FR-002:** each figure is quoted in the wording of the panel that decided it: "not shown, at
  this size", not "no".
- **FR-003:** the standing systems are stated with their known faults beside their gains.
- **FR-004:** spread is reported, not only geometric means: the median and the shares better,
  twice as good and twice as bad, wherever the record holds them.
- **FR-005:** what was never tested is listed, and so are the conditions for reopening.

## Success criteria

- **SC-001:** the reviewers find every quoted figure in the records and no claim beyond them.
- **SC-002:** a write-up, a slides post and a deck are published. AGENTS.md records the track
  as closed, unless the owner reopens it.
