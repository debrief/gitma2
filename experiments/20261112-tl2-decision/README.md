# Spec 014: decision record for the registered study (2026-11-12)

Written after the tuning seed (333: `experiments/20261112-tl2-tuning/`,
`experiments/20261112-tl2-thin/`) and before seeds 334 and 335 exist. A registered study,
not a gate (plan, Complexity Tracking): nothing is carried or stopped by a threshold, but
what is decided, its forecasts and the rule for the recommendation are fixed here.
`decision.json` binds the plan `configs/timelate/tl-c.json`, the two run files, the ranges
files and the time-late code by digest. The plan is never edited after this commit.

## What is decided on test seed 335

| | Quantity | Forecast |
| --- | --- | --- |
| D1 | Share of the search's gain over C″ that refitting C″'s own manoeuvre times obtains (Annex B, 400 periods) | 0.75; the interval includes 0.6, excludes 0.3 |
| D2 | Wrong-history periods: ambiguous, search failure, evidence failure (threshold 3, 120 s match) | 0.45, 0.10, 0.45 |
| D3 | Attainable headroom against 1.10: a perfect search under the same evidence; a perfect evidence as well | inconclusive (about 1.1); material (about 1.3) |
| D4 | False-manoeuvre rate on 400 held-course periods: search, C″, flat-prior search, mixed-prior search | 0.80, 0.03, 0.02, 0.10 |
| D5 | Recommendation on a learned whole-period model | by the rule below |

**Rule for D5** (research R9, fixed before the tuning run): pursue a learned whole-period
model only if the headroom with a perfect evidence (`ident-all`) is material. If it is, the
model is registered against the search, the mixed-prior search and the refit under the same
prior, on the Annex B, shifted and held-course splits. Otherwise no GPU budget is spent on it.

**Soundness stop** (validation seed 334, 150 Annex B and 150 held-course periods): the
reference fitted from neutral starts with times held within [0.8, 1.3] of the bound on
tightly bounded rows, and at least 90% of true-history fits with a cost the noise explains.
Fail: seed 335 is not generated.

## Reported, not decided

The flat-prior search; Gate T's search beside the corrected one; the shifted split (300);
correlated and outlying bearing errors (100 each, the same engagements as the first 100
Annex B periods); whole engagements (60); the smoothed EKF; manoeuvre counts and timing at
60, 120 and 240 s; splits by true manoeuvre count, ownship turns, position in the period and
range band; class shares at thresholds 1 and 5; candidate calibration.

## Added after the tuning seed, before registration

`search-mix`: Annex B's prior mixed half and half with a target that never manoeuvres. The
tuning seed showed the informed search declaring a manoeuvre on 81% of held-course periods;
this is the smallest classical change that could answer it. The half is a stated value, not
tuned. Seen before registration: six tuning periods (0 false manoeuvres of 6).

## Known weaknesses, stated beforehand

- The class threshold (3) is a convention; ambiguity moves from 0.08 to 0.27 of periods
  between thresholds 1 and 5 on the tuning seed. Both are reported.
- The composites are oracles of identification on the periods they replace: the headroom is
  attainable only by an identifier that is right wherever the evidence allows.
- "Evidence failure" includes true histories the prior makes improbable; no evidence built on
  Annex B's statistics would prefer them.
- The held-course split is outside Annex B by construction; D4 measures behaviour there, not
  a fault in the prior on Annex B data.
- Thinning: nothing adopted (the rule could not be met by 90 periods); full data throughout.
- Not run in this registration: the prior-mismatch diagnostic (US6), an IMM smoother.
- The tuning seed's C″ ÷ search ratio (1.72) is well below Gate T's test seed (2.27): seeds
  differ, and one test seed decides D1 to D4.
