# Addendum 2 (2026-11-26, before validation is launched)

Nothing above is changed. Recorded before any validation figure exists.

1. **The three fine-tunes were interrupted and resumed.** Modal disabled the workspace at about
   $45 of spend on 2026-11-23, 1 h 53 min into each run (`../20261123-ft-runs/`). The owner
   raised the limit and the three jobs were re-run on 2026-11-26 under their original run ids,
   so each continued from its saved state on the volume (14,075, 16,476 and 12,389 of 26,000
   updates) with its bound plan and the code of commit d386257. The stream is a function of the
   update number, so a resumed run sees the scenarios an uninterrupted one would have; the
   optimiser state and the schedule are restored. Up to 15 minutes of updates before the
   interruption were redone. The registered configuration is otherwise as bound.
2. **The hybrid's weight grid on validation is 0.125, 0.25, 0.5, 1** (addendum 1 said 0.5, 1,
   2, 4). Reason: a development reading with the pilot checkpoint on spent seed 321
   (`../20261123-rmis-pilot-dev/`) found the smallest weight best, at the grid's edge. That
   reading was seen before this change; it used a model that is not one of the three seeds and
   a seed that is neither validation nor test. The rule for choosing is unchanged.
3. **What the pilot reading means for the forecasts**: they stand as written on 2026-11-23.
   The pilot reading (C″-robust ÷ pilot 2.02 under the primary condition, 2.42 held out; about
   5% cost on clean data; range coverage 0.94 to 0.96 unfitted) is one seed of a schedule a
   sixth as long, on a spent seed. It agrees with the forecasts for M1 and M3, is above the
   forecast range for M2, and suggests M5's "not honest on held-out" may be wrong.
