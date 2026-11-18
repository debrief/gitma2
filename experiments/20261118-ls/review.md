# Spec 026: review panel, round 1 (2026-11-18)

Three agent reviewers, each given the files and a brief, with no conclusions handed to them:
- statistics and design;
- code and reproducibility;
- claims, scope and realism.

**All three: approve with findings.** The rules were applied as registered, and the decided
outputs stand:
- soundness passes;
- E1 non-inferior;
- E2 1.47 [1.12, 2.05];
- E3 drift not shown.

The panel narrows what those outputs may be taken to mean. Every recomputed figure below is
in `supplement.json`, from `scripts/research/long_study_supplement.py` (the registered
bootstrap). Each was checked against the reviewers' own scripts.

## Reproducibility (checked)

- `long_study_digests.py` at HEAD equals `experiments/20261118-ls-decision/digests.json`
  (code `938ef9a2…`, C `4d2c084f…`).
- Since the decision commit, only `configs/long/run.json` and an untracked charts script changed.
- Re-running `tma2-long study` reproduces `study.json` key for key; only the commit differs.
- Every shard header names commit a37d36d with a clean tree.

## Major findings and the narrowing they require

1. **E1's pass rests on windows that are level.**
   - 173 of 359 windows are identical. 60 of them are each chain's first window, where
     `ctl-carry` *is* `ctl` by construction: there is no previous window to carry from.
   - Without the first windows: 1.021 [0.9502, 1.100]. That clears the 0.95 line by 0.0002.
   - On the 186 windows where the two differ: 1.034 [0.923, 1.168], which would not pass a 5%
     margin.
   - By length: 12 h 1.005 [0.923, 1.096]; 6 h 1.044 [0.997, 1.111].
   - On the untended contact: 0.942 [0.880, 1.007] (twice worse 16, twice better 7). Without
     first windows: 0.920 [0.838, 1.011].
   - **Narrowed**:
     - the registered rule returned "non-inferior", by 0.008;
     - where the carried start changes the answer it is *not shown* to be within 5%;
     - the adoption rests on cost, not on shown accuracy;
     - it is limited to the tended contact on 6–12-hour engagements;
     - it is not recommended for an untended contact.
2. **E2 is this simulator's second contact, not "the cost of an untended contact".**
   - Contact 2 is drawn with no range keeping and scored only where detected. It answers 61% of
     its rows; in the bands, both contacts answer every row.
   - Within the 20–40 km band, contact 2 sits farther out than contact 1 (mean 30.6 against
     26.0 km).
   - In 2-km sub-bands the figure is 1.34 [1.01, 1.87], not 1.47. The far band falls from 1.66
     to about 1.3.
   - Bearing rate and ownship manoeuvres relative to the contact are not matched.
   - Mis-association is not exercised: 314 swapped bearings in about 389,000 rows.
   - **Narrowed**: "1.3 to 1.5 times worse on the rows where the untended contact is held, at
     matched range, under spec 024's unmeasured realism parameters". It includes residual
     geometry and detection thinning, and leaves out the cost of not holding the contact at
     all.
3. **E3's null is about answered rows only.**
   - The share answered falls from 0.91 to 0.74–0.79, and one engagement answers none of its
     late rows.
   - Counting unanswered rows as failures: 1.26 [0.88, 1.80].
   - With hours 2–6 as the base: 1.07 [0.83, 1.34].
   - The interval does not exclude a 30% rise.
   - **Narrowed**: "drift in the median error of answered rows is not shown at this size; the
     IMM answers fewer rows later". The IMM's tuning is MAN2's.

## Minor findings

4. **S1 counted a window that gave no answer.** Contact 1, engagement 19, window 3 had 46
   bearings, under the 60 the runner needs, and produced none. E1 uses 359 windows for this
   reason. The effect on any figure is negligible.
5. **The CPU saving was stated over all windows**, including the first, where no carried search
   runs.
   - On windows with a carried start: 8.50 h from nothing against 5.84 h from the carry, a 31%
     saving, not 42%.
   - The fit that builds the carried start is timed under "starts", so the saving is still
     slightly optimistic.
   - Overall the saving is about 7% of all windows' CPU.
6. **Provenance.**
   - The record named one CPU, but the shards ran on 7 CPU families (EPYC 7763, 9V74, 9V45;
     Xeon 6975P-C, 6973P-C, Platinum 8573C, 8370C).
   - E2 compares two jobs' outputs, as its registered limit says.
   - `study.json` records `git_dirty: true` because provenance is read with the record's new
     folder untracked (the known pattern). The scored code equals the bound digest.
   - The IMM's own code (`references/imm.py`, `detect/controls.py`) is outside `code_sha256`.
     It is unchanged since spec 007.
7. **Weighting.** The geometric mean pools window logs, so a 12-hour engagement weighs twice a
   6-hour one. E2 and E3 pool rows, weighting engagements by rows held. Registered, but not
   stated in the record.
8. **Forecasts** restated tuning, as the record says. E2's miss was visible on validation (2.00).
   Its stated mechanism, "once range is matched, most of the cost is geometry", was wrong: range
   banding left geometry in. No new explanation is offered untested.

## Recommended follow-on (the owner's choice)

**Stop the long-engagement track here as a simulation study.**
- Record `ctl-carry` as an optional cost measure for the tended contact, on engagements of up to
  12 hours.
- Treat E2 and E3 as descriptions of this simulator. More registered studies on hand-set
  realism parameters would mostly measure those parameters.
- Reopen the track only with one of three things:
  - measured realism: gap rates, detection curves and association statistics;
  - an ownship steered by the estimator's own track;
  - a tracker that handles association.
