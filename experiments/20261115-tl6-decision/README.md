# Spec 018: decision record (2026-11-15)

Written after two tuning runs on seed 345 (`experiments/20261114-tl6-tuning/`, the first
design, which gained nothing; `experiments/20261115-tl6-tuning2/`, the second) and
**before seeds 346 and 347 exist**. `decision.json` binds the plan
(`configs/timelate/tl-g.json`, `541aa8b4…`), the run files, the ranges, the time-late code
(`710c74e0…`; the control's modules are study L's, `e5040f5e…`, unchanged) and the scoring
files by SHA-256. Owner decision: 2026-11-14, option B. SRD §9 line proposed (the owner
merges).

## What is compared

- **The standing control** (`ctl-d1-q0.01`), run unchanged.
- **The adaptive control, declared** (`ada-d1-q0.01`): 30 manoeuvre priors (leg mean, leg
  spread, largest turn), the one with the most evidence in the period, declared by the
  control's rule. Not told the split.
- **The adaptive control, hedged** (`ada-h1`): the mean track of every member's candidates,
  with a stated sd of range (1.95 × the mixture's; the factor is from tuning).
- Beside, deciding nothing: the search told the true statistics; members chosen by groups
  of 5, 20 and all periods; each fixed member; the true-history reference.

## Conditions (each reads paired period error or coverage; none reads counts)

- **Gain**: on the shifted or shifted 2 split, control ÷ system **in range** has an
  interval wholly above 1.
- **Harm**: on any of the six splits, control ÷ system in range, course **or** speed has
  an interval wholly below 1.
- **Spread**: on Annex B and on shifted, two stated sds cover between 0.90 and 0.99 of rows.

Per system: a gain with no harm is proposed as the standing output (the hedge only with an
honest spread); a gain with harm is a trade and the owner decides; no gain and the
standing control stays.

Each condition can come out either way at the test's size; the figures are in
`decision.json` (`conditions_can_fire`). Sizes: Annex B 300, shifted 400, shifted 2 150,
held course 200, outliers 100, correlated 100 periods.

## Forecasts (restating tuning seed 345; not independent predictions)

- Declared: **a trade is most likely** (about one half): a gain on shifted targets, harm
  on Annex B targets in course. No gain: about a third.
- Hedged: a gain on shifted targets with harm on Annex B targets in course.
- Spread: honest on both splits about half the time.
- Groups of periods: level with choosing per period.
- The gain sits where the standing control misses a manoeuvre the bearings show.

## Order

Validation on seed 346 (soundness on Annex B data; a failure stops the study), then the
test on seed 347, once.

## Known limits

In `decision.json`. The two that matter most: this is the second design tried on the
tuning seed, so its tuning figures flatter it; and the standing control contains Annex B's
own prior while the family does not, so on Annex B targets the comparison favours the
control by construction.
