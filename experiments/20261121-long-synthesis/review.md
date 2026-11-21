# Spec 034: review of the long-engagement synthesis

Two reviewers read the first draft (commit 33288c4) against the committed records: one for
fidelity to the records and one for a critical reading. **Verdicts: both approve with findings.**
Neither found a fabricated figure. Every finding below was taken into the published version of
`site/blog/2026-11-21-long-synthesis.md` and `scripts/research/long_synthesis.py`.

## Fidelity reviewer: approve with findings

**Major:**
1. **The untended contact.** "10–22%" is the share of contact 2's bearings held beyond 6 h, not
   its error. Where held, `ctl` was at 6–8% (`20261117-long2/tables.md`). Corrected.
2. **The CPU saving.** "5.8 against 10.1 CPU-hours" is the all-windows figure that spec 026's panel
   corrected. On carried windows it is 5.84 against 8.50 search-hours, a 31% saving, about 7% of
   all windows (`20261118-ls/supplement.json`). Corrected.
3. **The carried start's costs were left out:**
   - 0.89 [0.82, 0.97] on one-turn 1 h windows (spec 029);
   - 0.952 [0.893, 1.021] on contact 1 (spec 028);
   - 0.920 on the untended contact without first windows (spec 026).

   Added, with "no start without the prior".
4. **The headline "about twice as good … exactly where".** About 2 holds on 1 h windows against the
   same window alone: 1.7–2.4 (specs 029 and 031). On 2 h windows it is 1.54 on one seed, 1.37
   pooled, and about 2.2 beyond 35 km against about 1.0 under. The same-past joint solve is not
   beaten. Rewritten.
5. **Generated table: spec 026 E1's convention contradicted itself.** It now states that the 60
   first windows are constructed ties, and adds the row without them (1.021 [0.9502, 1.100]).

**Minor, all corrected:**
- **Spec 028:** the weak split is the untended contact plus contact-1 windows near a gap. The
  no-useful-turn clause never fired. Its units are (engagement, contact) chains, the clustered
  interval is [0.951, 1.279], and the outcome reads "not shown, at this size". Its contact-1
  reading is 1.006 at the lower limit, "an average shift with many losses".
- **Spec 031:** D1 and D3 carry the later-bearings and turn caveat, and D3 against 2 h `ctl` is
  supplement only. The tuning flip's cause is "likely", not established. The replication row has
  its shares and engagement count.
- **Spec 032:** "half" means 85 of 165 blind windows (85 of 120 forecast). E1 is given with its
  pooled value. E2 reads "not separated, at this size". The population is contact kept, handed on
  and answered.
- **Specs 023 and 024:**
  - real-time error is 13–23%;
  - the run time is one period of growing length;
  - steering on measured bearings begins with spec 024.
- **Spec 026:** E2 at matched range is about 1.3–1.5.
- **Lost contact:** the joint solve's extrapolation there was measured but not registered.
- **The error table:** spec 028's row is labelled as all windows after the first, both contacts,
  and 2 h `ctl` (9.0%) is added.
- **Rows that read the other way** (E2, E3) are marked.
- **Spec 033:** "open in another session" became "a spec on main and no test record yet".

## Critical reviewer: approve with findings

**Major, all taken in:**
1. **The prior's gain is not confined to blind windows.**
   - Spec 028's other windows read 1.14, separated.
   - One-turn windows read 1.22 and 1.26.
   - Inside the blind case it is far-range only.

   The headline now says "where that window cannot see range", with the small gain elsewhere stated.
2. **"About twice as good" mixed window lengths and comparators.** Rewritten by window length, with
   the pooled 2 h figure and "more data beats no data".
3. **The standing system's faults were not stated beside its gains.** Added:
   - far range only;
   - half the blind windows lost to contact;
   - the prior handed on across a turn;
   - seed swings;
   - contact 1 and one simulator;
   - the guard's rate;
   - the job's cost per engagement-hour.
4. **"Longer windows beat a shorter window plus a prior" was not like for like.** It now gives the
   29 minutes of later bearings and the turn, and points to the joint solve as the same-past
   comparison.
5. **"A carried start does nothing that matters" contradicted the cost finding.** Rewritten as "not
   shown to help accuracy, saves about 31% of the search where it runs".
6. **The untested list missed what a deployment needs.** Added:
   - latency;
   - cost per engagement-hour;
   - the ten-manoeuvre cap;
   - the guard's rate;
   - error families outside the generator's;
   - targets outside Annex B;
   - the drift of the ownship's range belief;
   - real-time requirements.
7. **The reopening conditions were too narrow.** Added a deployment needing the untended contact or
   answers through lost contact, and a latency requirement 2 h windows cannot meet.

**Minor, taken in:**
- the 48-hour claim marked as anecdote, with the registered evidence ending at 12 h;
- the later-bearings caveat on the 4.2% figure;
- the spread of spec 031's D2 (median 0.78, about 4 in 10 windows better);
- spec 030's joint solve kept standing (k4 ÷ joint 1.40) and inflation not shown to matter;
- the untended contact as partly tested through spec 028's weak split.

With these taken in, both reviewers judged closing the track justified.
