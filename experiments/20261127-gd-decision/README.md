# Spec 038 decision record: where the regressor's gain comes from

Written 2026-11-27, before any engagement of test seed 372 exists. A registered study, not a
gate; nothing is trained and nothing is carried. Development: `experiments/20261127-gd-dev-a/`
(seed 321) and `experiments/20261127-gd-dev-b/` (seed 370).

## What is bound

- Protocol `configs/gd/protocol.json`, the ranges and conditions files, the code that predicts,
  scores and reads, and the workflow: SHA-256 of each in `digests.json`. C's code digest
  `4d2c084f…` (unchanged). Regressor checkpoints by digest (spec 037's three fine-tuned, spec
  012's three unchanged and the ownship-only one).
- Test: seed 372, generated in its runs only; the first 500 engagements with a 1° bearing sd per
  split and condition; scored once. Plans `configs/headroom/gd-test-{in,shift,far}.json`, written
  by `scripts/research/gd_plan.py test`.
- Systems. Comparator **C″-robust** (C″ with Gate H's robust final solve). Hardened controls,
  each C″ with the robust final solve and a changed segmenter input or threshold, told nothing:
  `c2-edit` (wild bearings edited out of what C sees), `c2-thr` (confirmation threshold × 4),
  `c2-edit-thr` (both; **the hardened control the readings decide on**). `own`: the ownship-only
  regressor (it reads the ownship track, and two bearings reach its rows: the first sets its
  frame, the current one its direction). `own-hyb`: C″-robust's solve with `own` as a prior at
  weight 2. `robust-true`: the robust solve told the true manoeuvre times. Fine-tuned regressors
  pooled over three training seeds.
- Statistic: per-engagement median error over the scored rows both sides answer; paired log
  ratios; 2,000 bootstrap resamples of engagements, seed fixed in the code; 95% intervals.

## Readings and their lines

**G (gap closed).** g = ln(C″-robust ÷ c2-edit-thr) ÷ ln(C″-robust ÷ fine-tuned), range, in
distribution, primary condition. "Most" if the interval is wholly at or above 0.5; "little" if
wholly at or below 0.2; otherwise "between", reported with its interval. Reported beside, no
line: the same for `c2-edit` and `c2-thr`; on the kinds outside the mix; course and speed; on
the shifted and far splits; and each control's ratio to C″-robust on clean data (a cost if the
interval is wholly below 1).

**P (prior share).** p = ln(C″-robust ÷ own-hyb) ÷ ln(C″-robust ÷ fine-tuned), range, in
distribution, clean and primary separately; the same lines. Reported beside: `own` alone; course
and speed; the other splits.

**S (where the prior is wrong).** ln(C″-robust ÷ fine-tuned) on the shifted split minus in
distribution, and on the far split minus in distribution; range; clean and primary: four
readings. "Shrinks" if the interval is wholly below 0; "holds" if it lies within ±ln 1.15;
otherwise "not separated". Course, speed and absolute errors beside.

**T (reported, no line).** robust-true ÷ fine-tuned on every split and condition, in range,
course and speed.

**Owed slices (reported, no line)**, for C″-robust ÷ fine-tuned: by time since the last true
target change (under 5 min, 5 to 15, over 15); by whether the first bearing is an outlier; by
whether C″'s structure was right at the first scored row (every true change begun 120 s or more
before it matched within 120 s and no other transition declared), read on the later rows only;
efficiency by thirds of the bound; on rows every named system answers; shares answered.

**Stop rule (FR-042), already read**: on run B the hardened control's point value is 0.453,
under one half. C″-robust is the headline comparator.

## Forecasts (basis: run B, 300 engagements of seed 370; a forecast from one development seed)

| reading | run B | forecast |
|---|---|---|
| G, primary | 0.453 [0.347, 0.561] | between (0.35 to 0.55) |
| G beside: outside the mix | 0.34 | 0.25 to 0.45 |
| clean cost of c2-edit-thr | 0.940 [0.857, 1.034] | a cost (about 0.92; the interval may or may not clear 1) |
| P, clean | 0.02 [−0.01, 0.04] | little |
| P, primary | 0.04 [0.02, 0.07] | little |
| S, shift, clean | 0.888 [0.756, 1.047] | not separated or shrinks: a coin's toss, said so |
| S, shift, primary | 0.855 [0.728, 0.998] | not separated or shrinks: a coin's toss |
| S, far, clean | 0.807 [0.680, 0.950] | shrinks |
| S, far, primary | 0.821 [0.694, 0.958] | shrinks |
| T, in, clean / primary | 0.96 / 1.14 | level clean; regressor ahead in range under mismatch, behind in course and speed |
| T, shift, clean | 0.74 | the solve told the true times ahead |
| C″-robust ÷ fine-tuned, in, clean / primary | 1.62 / 2.29 | 1.5 to 1.8 / 2.0 to 2.4 |

## What the outcomes will be taken to mean

- G "most": the earlier headline was mostly an unhardened segmenter. "Between" or "little": a
  share stated, and the rest is a segmentation gap that classical hardening of this kind does
  not close.
- P "little" on both: the regressor's gain is not the unconditional prior given the ownship
  track. That does not rule out prior knowledge used together with the bearings (manoeuvre
  statistics inside the model's implicit segmentation); S is the reading for that.
- S "shrinks": part of the lead depends on the training statistics; the absolute lead that
  remains is given beside. S on the far split moves initial range only, and the fine-tuned
  models met far ranges in a fifth of their training stream.

## Known limits, stated beforehand

- One simulator, bearing sd 1°, real-time estimates at 5 to 20 min after the ownship's zig.
- The hardened controls were chosen on two seeds from a small family (two tools, one grid);
  a better classical segmenter is not ruled out by "little" or "between".
- The edit's flags at the last four bearings before a scored row use only bearings up to that
  row; elsewhere the edit reads four bearings ahead of the bearing it judges (40 s), which the
  scored rows never see.
- `c2-edit-thr` and `c2-thr` cost accuracy on clean data; a system that pays that cost is not a
  free replacement for C″.
- At 500 engagements a share's interval is about ±0.09 where the gap is a factor of two and
  wide where the gap is small (far and shifted, clean).
- The hybrid with the fine-tuned prior is scored for training seed 1 only.
