# Spec 039 decision record: a classical control given the generator's priors

Written 2026-11-28, before any engagement of test seed 373 exists. A registered study, not a
gate; nothing trained; nothing carried by it. Development: `experiments/20261128-pic-dev/` and
`experiments/20261128-pic-dev2/` (spent seed 370).

## What is bound

- The files in `digests.json` (protocol, prior table, ranges, plans, the code that predicts,
  scores and reads, the time-late code the cut control calls, the workflow). C's code digest
  `4d2c084f…` (unchanged). Regressor checkpoints by digest.
- Test: seed 373, generated in its runs only; the first 500 engagements with a 1° bearing sd on
  each of three splits (in distribution; busier targets; far initial ranges), clean and under the
  primary mismatch condition; scored once. Plans `configs/headroom/pic-test-{in,shift,far}.json`.
- Systems.
  - **C″-robust**: the standing system with Gate H's robust final solve. The comparator.
  - **robust-true**: the robust solve told the true manoeuvre times.
  - **true-prior**, **c2-prior**: the range-profile read-out told the generator's distribution of
    range and its speed support (untempered, grid 20; `headroom/profile.py`), on the true
    segmentation and on C″'s.
  - **cut-ctl**: spec 016's time-late control (`ctl-d1-q0.01`, unchanged) run on the bearings up
    to the scored row and read at its last moment (`headroom/cut.py`). Causal; told Annex B's
    manoeuvre statistics and a broadened version, pooled; it also edits wild bearings, uses an
    effective bearing sd and fits arcs, not chords.
  - Fine-tuned regressors, three training seeds pooled.
- Statistic: per-engagement median error over the scored rows both sides answer; paired log
  ratios, first ÷ second (above 1: the second is better); 2,000 bootstrap resamples of
  engagements; 95% intervals. A share is a ratio of mean logs with its interval, with the ratio
  of medians and the 10%-trimmed version beside it.

## Readings and their lines

**K (the cut control; the headline, in distribution).**
- K1: cut-ctl ÷ fine-tuned, range, clean and primary. "Regressor better" if wholly above 1,
  "control better" if wholly below 1, otherwise "not separated". Course and speed beside.
- K2: the share of the log gap C″-robust → fine-tuned that cut-ctl closes, range, clean and
  primary. "Most" if wholly at or above 0.5; "little" if wholly at or below 0.2; else "between".
- K3: C″-robust ÷ cut-ctl in range, course and speed, on each of the six split and condition
  pairs. "Better than C″-robust" if wholly above 1 in range and not wholly below 1 in course or
  speed.
- K4 (reported): cut-ctl ÷ robust-true; cut-ctl ÷ fine-tuned by thirds of the range bound;
  shares answered; seconds per estimate from the jobs' logs.

**Q1 (the range prior with the true structure).** On rows in the loosest third of the range
bound, in distribution, clean and primary: the share of ln(robust-true ÷ fine-tuned) that
true-prior removes. Lines as K2; "not defined" where the denominator's interval contains 0.
Beside: robust-true ÷ true-prior in each third ("a cost" if wholly below 1 in the tight third).

**Q2 (the range prior in a causal system).** The share of the log gap C″-robust → fine-tuned
closed by c2-prior, in distribution, clean and primary. Lines as K2.

**Q3 (reported).** Every pair on the busier-target and far-range splits, with C″-robust ÷
robust-true and robust-true ÷ fine-tuned beside, so that it can be seen which side moved.

## Forecasts (basis: seed 370, 300 engagements, one development seed)

| reading | development | forecast |
|---|---|---|
| K1 clean | 1.029 [0.915, 1.156]; course 0.75, speed 0.66 | not separated in range; control better in course and speed |
| K1 primary | 1.490 [1.342, 1.641] | regressor better (1.3 to 1.6) |
| K2 clean | 0.95 [0.75, 1.22] | most |
| K2 primary | 0.51 [0.39, 0.62] | between |
| K3 in distribution | 1.59 clean, 1.52 primary | better than C″-robust on both |
| K3 shifted, far | not run in development | better on the shifted split (the pooled prior was built for it); far: a guess, better |
| Q1 primary | 0.51 [0.06, 1.09] | between, with a wide interval |
| Q1 clean | not defined (no loose-third advantage) | not defined |
| Q1 cost, tight third | 0.87 [0.76, 1.00] clean, 0.88 [0.74, 1.02] primary | a coin's toss whether it clears 1: said so |
| Q2 | 0.11 [0.00, 0.23] clean; −0.01 primary | little on primary; clean a coin's toss between little and between |

## What the outcomes will be taken to mean

- K2 "most" on clean data and K1 "not separated": a classical causal system told how targets
  manoeuvre accounts for the regressor's lead over C″ on clean bearings. Since cut-ctl differs
  from C″ in its segmenter, its motion model and its prior at once, this does not say which of
  the three does it; it says a classical system reaches the regressor.
- K1 "regressor better" under mismatch: a lead remains there for the learned model, of the stated
  size, over a classical system that already edits wild bearings and inflates its sd.
- Q1 "most": the regressor's advantage over a solve told the true times, where the bound is
  loose, is knowledge of the range and speed distributions. "Little" or a cost in the tight
  third: this form of prior is not it, or is too crude an integration.
- Q2 "little": a range prior does not help when the structure is C″'s.

## Known limits, stated beforehand

- One simulator; bearing sd 1°; rows 5 to 20 min after the ownship's zig.
- cut-ctl was built and tuned on the same generator family in specs 013 to 018 (time-late, 5 s
  bearings, cut periods). Its settings are used unchanged here at 10 s bearings on prefixes; it
  has known faults recorded in those specs (it under-counts manoeuvres and can invent them on
  held course). No held-course split is scored here.
- The profile is not a marginal, and under mismatch it is too narrow; the tempered version was
  worse on development data and is not carried.
- The prior table is MAN2's; on the far split it is wrong by construction.
- K3's wording applies to these splits only. Whether cut-ctl should replace C″ for real-time
  estimates is the owner's decision and is not made by this record.
