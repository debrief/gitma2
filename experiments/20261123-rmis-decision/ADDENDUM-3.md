# Addendum 3 (2026-11-26, after validation, before the test is launched)

Bound here, from validation seed 370 only (`../20261126-rmis-val/`), and not changed after the
test run starts:

- Interval scales (range, course, speed): **0.9767, 1.1353, 0.8312**
  (`../20261126-rmis-val/interval-fit.json`, which also holds the temperature control's cuts and
  half-widths).
- The hybrid's prior weight: **0.25**. The static comparator `c2-prior`: ln range mean **9.690**,
  sd **0.649**, weight 1.
- The held-out condition `ho-both` hurts C″ on validation (0.112 to 0.332), so M2 is a test.
- Test plan: `configs/headroom/rm-test-371.json` (written by `scripts/research/rmis_plan.py
  test`): seed 371, 1,000 engagements a condition in 20 shards; decided conditions off,
  all-central, ho-both; reported out-central, corr-central, ho-osc, ho-both's two parts; the
  fine-tuned checkpoints by digest (`5ecb77e9…`, `9695333f…`, `e151ac91…`); the hybrid and the
  comparator on off and all-central.
- Pooling: `reading-ft.json` in each scoring job pools the three fine-tuned seeds (the job's
  `reading.json` pools all six regressors and is used for per-system figures and coverage only).
  M3 and M4 pool the same-seed log ratios (unchanged k ÷ fine-tuned k) within an engagement,
  computed from the run's `errors.npz` by a committed script.
- M5's interval score is compared on rows where the head states an interval; for course that
  is the rows with a stated arc.

Forecasts are not rewritten. Validation's figures were seen before this was written; they are
in `../20261126-rmis-val/README.md`.
