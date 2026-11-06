# Gate S decision record (contract)

Committed as `experiments/<date>-gs-decision/decision.json` (type `GateSDecision`), with a
`README.md`. It must be committed before any L training (FR-070). Amendments are new files listed
by digest. A gate manifest names every amendment it applied.

| Field | Content | Fixed by |
| --- | --- | --- |
| plan | path and SHA-256 of the training/scoring plan | — |
| seeds | validation 314, test 315, L stream 317 (generator 0.6.0), each with its data digest | R7 |
| parameters | SegmentParameters (data-model.md), all final | validation measurements, phase 1 |
| search_penalty | the value giving ≤ 5% false splits on the tuning scenarios | R1 |
| mode | `gap` or `chord` (the lower median range error on validation G5 rows; ties go to the chord) | R3 |
| gap_normalisation | `raw` | R7 |
| s1_limit | O's contamination P90 limit on ownship legs (proposed 0.02) | spec FR-071 |
| s3_limits | L's contamination median and P90 limits; false-split limit (proposed: not worse than the reference by more than 0.01 contamination, false split ≤ 5%) | spec FR-071 |
| s2_validation | C − GLR + confirm, gap recovered on validation, with interval; the S4 reference this implies | phase 1 |
| carried_rule | median of three seeds by validation gap recovered (range) | spec FR-044 |
| shuffled_rule | the control's gap recovered minus the reference's; its interval must include zero or lie below it | constitution IV |
| forecast | expected values and intervals for S1–S4 | the author |
| follow_on | copied from Annex A §A.9 | Annex A |
