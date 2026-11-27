# Addendum 1 (2026-11-23, while the three fine-tunes train; before validation is launched)

Nothing above is changed. This records what the decision record said was still to be written,
as it now exists, before any validation figure has been seen.

1. **The hybrid** (`src/tma2/regress/hybrid.py`, `tma2-hpredict --kind hybrid`): C″'s
   segmentation and Gate H's robust final solve, with three more residual rows on the state at
   the reported row: range along the regressor's line of sight and the two velocity components,
   each (layer − regressor) ÷ (weight × the regressor's stated sd). `physics/layer.py` is not
   edited and C's code digest is asserted unchanged in its test. Departures from the plan's
   wording: the solve keeps the layer's own start rather than starting from the regressor; the
   velocity prior is isotropic at the row's `sd_speed_mps`; the range prior is linearised. The
   one setting is the weight, chosen on validation from 0.5, 1, 2, 4 by the pooled
   C″-robust ÷ hybrid range ratio on off and all-central. The comparator `c2-prior` is the same
   solve with a static ln-range prior (mean and sd of validation's true ln range) and no
   velocity rows.
2. **Uncertainty** (`regress/mread.py` additions; the file's digest in `digests.json` therefore
   no longer matches: functions were added, none changed, and no reading existed):
   `fit_scale` (the multiplier of the head's stated half-width that covers 0.95 of validation's
   off and all-central rows, per quantity, the three seeds pooled), `fit_temperature` (the
   control: a half-width per quantity and per third of the regressor's own estimated range,
   covering 0.95 of the same rows), `winkler` (the 95% interval score of a symmetric interval)
   and `score_ratio` (mean score of the head ÷ the control's with an engagement bootstrap; on
   rows where the head states an interval, so course is compared where a course is stated).
   Fitting: `scripts/research/rmis_fit.py`.
3. **Scoring plans** are written by `scripts/research/rmis_plan.py` from the protocol and the
   checkpoints' digests. Validation: 300 engagements, off, all-central, ho-both. The hybrid runs
   on off and all-central only (its registered conditions). `configs/rmis/all-conditions.json`
   joins the two conditions files unchanged.
4. **Still owed before the test scoring**: addendum 2 with the fitted scales, the control's
   widths, the hybrid's weight, the static prior, and whether the held-out condition hurts C″
   at all (if it hurts no system, M2 is reported as "no test", as the spec's edge case says).
