# Spec 019: what part of the true prior buys its gain? (development work, 2026-11-15)

CI run 43716758567 (`timelate/tl-h-dev`, commit 8c7a7a0, plan
`configs/timelate/tl-h-dev.json`). **Development work on used periods: the first 150
shifted periods of seed 347, spec 018's test seed. Nothing here is a registered result;
there is no decision rule.** 130 periods scored. Tables in `tables.md` (generated from
`summary.json` by `scripts/research/tl7_tables.py`) and `supplement.md`
(`scripts/research/tl7_refit.py`, from the per-row errors of this run and of spec 018's
test); the figures below are copied from them. Per-row errors: results branch
`results/timelate-tl-h-dev-43716758567`.

## What was run

The standing control unchanged, and the control's search, each time a search of its own,
under: the broadened prior (`lad-0`); that prior taking on the shifted targets' own
statistics a part at a time (legs, turn sizes, turn rates, speed changes, kinds of
manoeuvre: `lad-1` to `lad-5`, the last being the true prior); each part alone on the
broadened prior (`one-*`); and spec 018's family member nearest the truth with its own
search (`mem-L900-s0.35-a60`).

## What it shows (standing control ÷ system, range; above 1: the system is better)

| | Ratio | Without its ten best periods | Missed manoeuvres | False a period |
| --- | --- | --- | --- | --- |
| Standing control | – | – | 0.50 | 0.41 |
| Broadened prior | 0.98 [0.90, 1.06] | 0.91 | 0.52 | 0.45 |
| + legs | 1.05 [0.93, 1.20] | 0.92 | 0.46 | 0.59 |
| + turn sizes | 1.06 [0.90, 1.24] | 0.93 | 0.42 | 0.54 |
| + turn rates | 1.12 [0.94, 1.33] | 0.94 | 0.40 | 0.54 |
| + speed changes | 1.10 [0.93, 1.30] | 0.95 | 0.38 | 0.57 |
| + kinds: the true prior | 1.11 [0.94, 1.32] | 0.94 | 0.36 | 0.52 |
| Turn sizes alone | 1.00 [0.88, 1.14] | 0.88 | 0.48 | 0.40 |
| Turn rates alone | 0.96 [0.83, 1.10] | 0.83 | 0.50 | 0.38 |
| Speed changes alone | 0.96 [0.84, 1.09] | 0.84 | 0.49 | 0.42 |
| Kinds alone | 0.92 [0.82, 1.02] | 0.85 | 0.51 | 0.44 |
| Nearest member, own search | 1.03 [0.91, 1.19] | 0.90 | 0.39 | 0.53 |

- **No part carries the gain.** Along the ladder the ratio rises by steps of a few per
  cent from 0.98 to 1.11, none separated from its neighbour or from 1. Each part alone
  does nothing or costs a little (0.92 to 1.00). The gain appears only as the parts
  accumulate, legs first.
- **The gain is a tail at every rung.** Without its ten best periods of 130 every system
  is behind the control (0.83 to 0.95), the true prior included (0.94). The median
  per-period ratio is 1.00 to 1.06.
- **What moves steadily is the count.** Missed manoeuvres fall from 0.52 to 0.36 down the
  ladder while false ones stay near a half a period: the true prior finds more of what is
  there. That does not show in the typical period's error.
- **In course and speed the true prior is further ahead**: 1.21 [0.99, 1.51] and 1.24
  [0.99, 1.57] against the control, and separated from the broadened prior (1.32 [1.07,
  1.64] and 1.29 [1.03, 1.63]).
- **Search against refit: no difference.** The nearest family member with its own search
  is 1.03 [0.91, 1.19] of the control; the same member refitting shared candidates in
  spec 018's run, on the same 130 periods, is 1.03 [0.91, 1.19]. Across the two runs the
  refit ÷ own search is 0.99 [0.87, 1.12] (the control itself differs by 0.99 between the
  runs: another CPU family). The shared candidate set did not starve the family.
- **The nearest member is short of the true prior in speed** (1.29 [1.03, 1.63]) and not
  separated in range (1.08 [0.92, 1.25]): what it lacks is the truth's speed changes,
  turn rates and kinds.

## What it settles for the account

Spec 018's panel left two explanations confounded: the family's members only refitted
shared candidates, and the family lacked parts of the truth. The first is not it. The
second is real but small and diffuse: no single statistic, stated correctly, buys the
gain; the whole prior does, by about a tenth in range, in about ten periods in 130.

## Limits

- Used periods; 130 of them; nothing is separated from 1 in range. The readings are of
  direction, order and concentration.
- One order of the ladder. The single-part rungs show the parts do not act alone; other
  orders were not run.
- The "share in the ten best periods" column of `tables.md` is meaningless where the
  total gain is near zero; the ratio without them is the usable figure.
- About 450 seconds a period for the eleven searches; one shard of six periods took nearly
  three hours.

## Corrected after review (2026-11-15)

Three reviewers checked this record with the account. Two readings above are wrong as
written; `supplement.md` now carries the figures.

- **"The gain is a tail at every rung" is an artefact.** Dropping only a system's ten best
  periods pulls any widely spread ratio below 1 (the per-period log ratios have an sd of
  about 1). Trimmed of its ten best and ten worst periods the true prior is 1.14 (1.11
  untrimmed); it is better than the control in 55% of periods, over twice as good in 25%
  and over twice as bad in 13%. Neither typical nor a tail: two heavy tails that nearly
  cancel. The same holds for spec 018's "ten periods of 355 carry 87%" (trimmed at both
  ends: 1.10, unchanged).
- **"No part carries the gain" and "only whole" over-read the ladder.** Legs are the
  largest step (1.05), and legs, turn sizes and turn rates together reach the whole
  prior's figure in range (1.12 against 1.11). "Each part alone" was the other four parts
  without the legs. One order, 130 used periods, nothing separated: a direction, not a
  decomposition.
