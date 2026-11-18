# Spec 025 decision record: several periods of one target, joined through the gaps

Registered 2026-11-18, before seeds 350 (validation) and 351 (test) are scored. Nothing is
trained; CPU only. A registered study, not a gate.

## What is bound

- Plan `configs/timelate/tl-j.json`, SHA-256 `ef64ab3ac7249867ffd4d6f74c4212f6b635ddc77ea114e097d51c54e111de5d`
  (never edited after this record).
- Code: time-late modules digest (`tma2-tlsolve`'s `JOIN_FILES`)
  `ec046dc0966a571913a8744279dd4a3c1c86de1fcc62cd4df13423b496e04348`, as in the second tuning
  run's shard headers. Runner `run8`, scorer `tma2-tlscore` (runner `run8`, `study8`).
- Runs: `configs/timelate/runs/tl-j-val.json` (seed 350, Annex B, 45 engagements),
  `configs/timelate/runs/tl-j-test.json` (seed 351; engagements Annex B 70, busier targets
  140, 2% wild bearings 70, held course 70; shards of 4).

## Systems

`ctl-d1-q0.01` (spec 016, unchanged) three ways on the same bearings: **alone** (each period),
**joint** (the span with the gaps' bearings marked missing), **full** (the span with every
bearing; a reading). Readings beside: C″ and one leg per period; the true history across the
span and per period, fitted with the prior (times free unless drifted) and to the bearings
alone with times held.

## Rows and statistic

Each period at rows 30 s apart from its start where the known-history bound on relative
range from the span's bearings (gaps without bearings) is below 0.5; the same rows for
every system. Per period the median error; per pair of systems the per-period ratio,
summarised by its geometric mean with a 95% interval from resampling engagements (2,000
resamples, seed 23), with the median per-period ratio and the shares better, twice as good
and twice as bad beside. Also on rows the period determines alone (own bound below 0.5).

## Soundness (validation, seed 350; stops the study if it fails)

- The true history across the span, fitted to the bearings with its times held
  (`ref-span-fixed`), has range efficiency within **[0.8, 1.5]** on rows whose span bound is
  below 0.05 (Annex B).
- The joint solve gives a track for at least 0.95 of periods.

The band's upper edge is 1.5, not spec 016's 1.3: on tuning the reference read 1.28, at
that band's edge (spec 018 panel: do not register a band whose edge the tuning value sits
on). The check exists to catch a reference that returns its start (efficiency below 1) or a
broken bound across masked rows; 1.5 still catches both.

## Rule (FR-010)

On each split: **gain** if the range interval of alone ÷ joint is wholly above 1; **harm**
if the interval of alone ÷ joint is wholly below 1 in range, course or speed on any split.
Otherwise **not shown**.

What follows:

- Gain on Annex B and no harm anywhere: the joint solve (`ctl` over the span with the gaps
  masked) becomes the standing time-late system for several periods of one target; `ctl`
  per period stays the system for a single period.
- Gain on Annex B with harm on a split: the joint solve is recommended only where that
  split's condition is absent, and the harm is written up; the owner decides.
- Not shown on Annex B: `ctl` per period stays; the result is written up.

The busier-target, wild-bearing and held-course splits are decided by the same rule and
reported; they say how far the result reaches, not whether it stands.

## Sizes and power (from tuning, seed 349)

By simulation from the tuning engagements (resampling engagements, bootstrap within):

| split | tuning alone ÷ joint | engagements registered | P(gain) at the tuning value |
|---|---|---|---|
| Annex B | 3.27 [2.25, 4.77] | 70 (about 60 scored) | 1.00 at 60 |
| busier targets | 1.52 [0.89, 2.60] | 140 (about 120 scored) | 0.92 at 120 (0.76 at 80) |
| 2% wild bearings | 2.75 [1.89, 4.01] | 70 | 1.00 at 60 |
| held course | 12.9 [6.6, 26.1] | 70 | 1.00 at 60 |

About one engagement in seven holds no two-period layout and is skipped (counted). The
busier-target power assumes the tuning value; if the true value is nearer 1.25 the outcome
there is close to a coin's toss, and that split is reported, not decided on its own.

## Forecasts

- Annex B: gain, about 3 (2 to 5). No harm.
- 2% wild bearings: gain, about 2.5. Held course: gain, about 10.
- Busier targets: gain, about 1.5, with a loss on periods that hold their own ownship turn
  and on gaps of 10 to 20 minutes; harm not shown.
- Gaps cost about a factor of two (every bearing ÷ joint near 0.5 on Annex B).
- Held course: the joint solve declares a manoeuvre in under 0.15 of engagements.

## Known before registration

- **Run-to-run variation.** The two tuning runs scored the same 45 Annex B engagements with
  the same plan settings (the second added two stored references) and gave alone ÷ joint
  3.27 and 3.03: `ctl`, C″ and the joint solve differ in the last bits between CI machines,
  which moves declared histories on about a quarter of engagements. Alone and joint for an
  engagement always run in the same job, so the pairing is unaffected; the figures carry
  this as a noise floor of about 8% at this size.
- **Seed 351 was generated once locally before this record**, only to count its σ = 1°
  engagements on the busier-target ranges (157 of 320, enough for 140); no system ran on it
  and the files were deleted. It is otherwise unused.
- Spec 024's `ctl-carry` is not merged; it is not part of this registration. If it merges
  before the test, it is run on the test engagements as a reading, never decided.
- The spike in research R1 ran on seed 348 (spec 023's) before that seed was known used;
  nothing is decided on it.

## Tuning record

`experiments/20261117-tl8-tuning/` (first run: four splits; `second/`: Annex B with the
soundness reference, soundness 1.28 on tight rows, joint answered 1.00).
