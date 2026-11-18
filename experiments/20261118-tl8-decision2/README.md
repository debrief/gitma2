# Spec 025 decision record, second registration

Registered 2026-11-18 on the owner's decision (option A) after the first registration
(`experiments/20261118-tl8-decision/`) stopped at validation (`experiments/20261118-tl8-val/`:
the soundness statistic had no power). Before seeds 352 (validation) and 353 (test) exist.
Nothing is trained; CPU only.

## What is bound

- Plan `configs/timelate/tl-k.json`, SHA-256
  `bbba4603afff3748dcaa588b4bb2d07bda5dcfe9ed1416914374dbd21bc92294` (never edited after this
  record). It is `tl-j.json` with only the soundness block and description changed.
- Code: time-late modules digest (`JOIN_FILES`)
  `ec046dc0966a571913a8744279dd4a3c1c86de1fcc62cd4df13423b496e04348`, unchanged from the first
  registration (the solve is identical). The scorer's `study8.soundness` gains the
  per-engagement statistic; the decided ratios and the rule are computed as before.
- Runs: `configs/timelate/runs/tl-k-val.json` (seed 352, Annex B, 110 engagements),
  `configs/timelate/runs/tl-k-test.json` (seed 353; Annex B 70, busier targets 140, 2% wild
  bearings 70, held course 70).

## Unchanged from the first registration

Systems, rows, statistic, the rule (gain: range interval of alone ÷ joint wholly above 1;
harm: any of range, course, speed wholly below 1 on any split), what follows, sizes,
forecasts. See `experiments/20261118-tl8-decision/README.md`.

## Soundness (validation, seed 352; stops the study if it fails)

- **Statistic**: for each engagement with at least 10 rows whose span bound is below 0.05,
  the median over those rows of |range error| ÷ bound ÷ 0.6745 for the true history fitted to
  the bearings with its times held (`ref-span-fixed`). The statistic is the geometric mean
  over those engagements (95% interval from resampling engagements, reported).
- **Pass**: the statistic within [0.8, 1.5], and the joint solve answering at least 0.95 of
  periods.

Why: a fit's rows share one error, so an engagement is one draw; the first statistic pooled
rows from about 20 engagements and its interval was [0.48, 1.59].

Power, from the 43 per-engagement values of the spent runs (tuning seed 349's second run and
validation seed 350; development data): with 40 engagements a sound reference lands in
[0.8, 1.5] with probability 0.96, with 60 0.98; a reference whose errors are 0.3 times or
2.2 times as large fails with probability at least 0.96 at 60. About 55% of engagements have
10 tight rows, so 110 engagements give about 60.

## Known before registration

- The statistic was chosen after seeing the first validation fail. On the spent seeds it
  reads 1.20 [0.80, 1.84] (tuning) and 0.91 [0.63, 1.31] (validation 350): it would have
  passed both. That is why it is decided only on fresh seeds; the choice is by the reasoning
  above (one draw per engagement), not by those values.
- Seeds 350 and 351 are spent (351 was only counted, never scored).
- Spec 024's `ctl-carry` is still not merged; as before, a reading if it merges in time.
