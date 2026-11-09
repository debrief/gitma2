# Gate 4 validation stop: agent review panel

Five independent, read-only reviewers: evaluation statistics, estimation and numerics, TMA domain,
reproducibility and process, and red team. Each was briefed on the committed record (`README.md`,
`validation.json`, `by-head/`), the decision record, the baseline and the code, with the per-row
arrays of the scoring run, and returned a verdict with findings tagged [blocker], [major] or
[minor], with evidence. Their scratch scripts are not part of the record. Findings are condensed;
the numbers are theirs.

# Round 1

All five returned **approve-with-findings**: the stop at validation is correct, the rule was fixed
before any result and applied as written, the carried seed is the registered one, and seed 320 is
untouched. None raised a blocker. The majors concern the record's explanations, the learning
claim and the criteria's design; the README has been rewritten accordingly (commit after this
file's first version).

## Statistics: approve-with-findings
- Every point in the README reproduces to 3 dp from `errors.npz`; intervals agree within bootstrap
  noise (G4-d [−0.332, −0.154] against [−0.355, −0.137]); G4-e exact; carried rule (median 2.765,
  st-s3), validation rule (points only) and shuffled rule applied as written.
- [major] "Narrow and seed-dependent" is not supported: re-binning under resampling, some bin misses
  ±0.05 in 87% of resamples for st-s3 and 47% / 43% for st-s1 / st-s2; the top bin is under-stated
  for every seed (+0.055, +0.040, +0.022); every head's P is under-dispersed (slope of hit on P
  1.38, 1.22, 1.15); st-s3's top bin interval [+0.016, +0.097] is real miscalibration.
- [major] The per-bin check is a point check without sampling allowance: clustered sd per bin
  0.018–0.023, so ±0.05 is about 2.5 sd; the temperature itself would miss it in 28% of resamples.
  Pre-registered and unchangeable now; record as a design flaw (use an interval or a calibration-
  slope test next time).
- [minor] Ties: st-s2 has a 1,320-row isotonic plateau split by row order between bins 4 and 5
  (s3's verdict unaffected). [minor] "Usable" overstated for course: P's sd 0.065, AUC 0.60; the
  head adds 0.044 nats on course over the temperature. [minor] G4-d's scaling is sound: the head
  beats the temperature in every component. [minor] Missing rows (39, the same for all) are
  charged conservatively; excluding them widens the head's lead (−0.255). [minor] 0.0045, not
  0.004; sd 0.018 clustered, not 0.016.

## Estimation and numerics: approve-with-findings
- [major] The course statement contradicts itself: P goes through the isotonic map, the stated
  density (scored by G4-c) does not; |P − density mass on ±X| averages 0.037, up to 0.20
  (temperature 0.33); top bin density 0.749, P 0.675, hit 0.730. Declare P the only course claim
  or recalibrate the density before any test.
- [major] The top-bin miss is the isotonic map's: raw head P 0.761 against hit 0.730 in the top bin
  (slightly over-confident); PAV pooled the top two of 10 knots (about 197 tuning rows each, sd
  about 0.034) to 0.677, capping P there for 13.8% of rows. The temperature's map pools 7 of 10
  knots to 0.583 (about 80% of rows state one P). The README's "under-confident on the rows it is
  most sure of" was wrong.
- [major] The shuffled control (errors permuted, sds kept) tests a null the temperature already
  rejects. Unregistered controls on the scoring rows: temperature refitted on the stream 2.995;
  sd-deciles × cells on the stream 2.907; heads 2.744–2.747.
- [minor] The normal approximation to the von Mises in P errs by up to 0.12 per row (a·sd up to
  about 35°; the cap limits X, not a·sd); use the exact mass. [minor] Interval score correct;
  speed coverage shift between stream and validation stated honestly. [minor] β tempering sound.
  [minor] Points unchanged (`write_fields` adds keys only).

## TMA domain: approve-with-findings
- [major] P is not conditionally reliable: settled rows P 0.626 / hit 0.73, not-settled rows (a
  quarter) P 0.617 / hit 0.30; the temperature the same. On open transitions the arc widens (21° to
  38°) at the same P and is reliable (−0.015). "The statement is usable" must be qualified.
- [major] P barely varies (5th–95th percentile 0.46–0.68); rows more than 90° off (9.5%, consistent
  with reciprocal-course ambiguity) carry mean P 0.62. Equal-count bins on so narrow a range test
  only the flat part of the map.
- [major] Nothing before minute 5 is measured, and minute 5 is the weakest slice (range coverage
  0.916, speed 0.903, reliability −0.051).
- [major] References are compared uncalibrated against a fitted E; a fair ceiling fits the same
  temperature to the oracle; the IMM's 22.5% no-estimate rows should be reported apart.
- [minor] Plain widths: range ×/÷1.74 median, 3.77 at the 95th percentile (11–35 km at 20 km);
  speed half-width 3.4 m/s median. `sharpness95_*` measures raw sds, not the statement. [minor]
  Beyond 30 km coverage is 0.907 (range) and 0.867 (speed). [minor] 21.6% of rows at the 45° cap
  (hit 0.71, P 0.655): close to "unknown" tactically; G4-c is easy to pass.

## Reproducibility and process: approve-with-findings
- Order and binding hold (decision 7270104 before training at 7270104; plan digest e357f8a7 at every
  later commit; `decision_sha256` matches). `tma2-g4predict` (st-s1 best, temperature) and
  `tma2-g4 --split validation` reproduce byte for byte from the results branches. Seed 320
  untouched; no `carried.json`, as after a stop.
- [major] A local trial training before the decision record produced st-s1 weights identical to
  CI's (`601c820b…`), and its in-sample numbers drove the sd^β redesign. Allowed (constitution IV;
  the control got stronger) but not disclosed: now an addendum in the decision README.
- [minor] The raw-E baseline on scoring rows before the record is allowed (T009; Gate 3 precedent).
  [minor] Stated files and verdict made in session, not on CI (seconds; reproducible);
  `run.json` of the stated files lacks the input file's digest (in the scoring run's
  `inputs.json`). [minor] The SRD amendment also corrects the Gate 3 row after its result (bands
  unchanged): flag it to the owner separately.

## Red team: approve-with-findings
- [major] The registered control is a restricted classical rule. Fitted on tuning rows 0–499 only,
  scored on 500–1499: each log scale linear in all three log sds (19 parameters) recovers 39% of
  the head's margin; quadratic (43 parameters) 72%; adding C's code, minute, open 73%; a linear
  rule on the head's 68 inputs nothing. About 0.07 remains, mostly course, unattributed. The
  record must say the gain is largely a classical function of E's sds; register a cross-sd control
  before any test.
- [major] The shuffled control cannot separate "per-row information" from "a better function of
  the sds"; a control permuting only the encoder state would.
- [minor] G4-d is not dominated by one component (course −0.051, range −0.088, speed −0.096); the
  range and speed gains are tail-driven (top 1% of rows carry 85% and 66%); trimmed −0.197.
  Dividing by |mean| would blow up if the course mean approached 0. [minor] st-s1's +0.040 top
  bin is within noise of failing too. [minor] Fit richer classical controls on the stream, as the
  head is.

## Outcome of round 1

Stop at validation upheld unanimously. Corrections made to the record: the stop's reading (not a
seed-dependent near-miss), the top-bin cause (the isotonic map), the conditional failure on
unsettled rows, the course density / P contradiction, the learning claim (largely reproducible
from E's sds), the trial-training disclosure. Recommended follow-on (for the write-up):

1. Course statement: exact von Mises mass; one probability (recalibrate the density, or state P
   only); a smoother recalibration than 10-knot PAV (fewer knots or a parametric map, fitted on
   more tuning rows); consider a two-mode course (estimate or reciprocal).
2. Conditional reliability gated by slice (minutes since the zig including minutes 1–5, open
   transitions, range band) and a causal "unsettled" proxy that lowers P.
3. Per-bin reliability as an interval or calibration-slope test, not a point band.
4. Controls registered before results: a cross-sd parametric rule (quadratic in the three log sds,
   fitted on the stream) and a shuffled control that permutes only the encoder state.
5. Calibrated references (the oracle with the same temperature) and plain-language widths.
