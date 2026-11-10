# Gate H tuning: the robust control's settings grid (spec 010 T015)

**Tuning data only; not a gate result.** Run 42730139942 (`headroom/tune-grid`, plan
`configs/headroom/tune-grid.json`), commit 973f599, clean tree. Seed 320, the first 300 σ = 1°
scenarios, 1181 G5 rows; the primary condition (`all-central`) and mismatch off; 27 settings
(research R5). Each job's `headroom.json` is here as `<condition>.<variant>.json`; the records are
on `results/headroom-tune-grid-<condition>-<variant>-42730139942`.

On these rows the plain solve's median range error is 0.1386 and the attainable
ceiling's 0.1114.

| Huber constant | Correlation shrink | Control, primary | R, primary | Cost on clean data | Cost, rows all answer |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 0 | 0.1155 | +3.7% [−2.3, +9.9] | +1.4% [−4.8, +8.8] | −0.1% [−6.9, +10.1] |
| 1.0 | 0.25 | 0.1155 | +3.7% [−3.1, +9.6] | +2.0% [−4.9, +9.0] | −0.1% [−7.0, +10.6] |
| 1.0 | 0.5 | 0.1170 | +5.0% [−3.4, +11.4] | +3.1% [−4.2, +9.5] | +0.4% [−6.5, +11.5] |
| 1.345 | 0 | 0.1138 | +2.1% [−4.5, +8.3] | +2.6% [−3.7, +8.2] | +0.6% [−6.4, +7.9] |
| 1.345 | 0.25 | 0.1147 | +2.9% [−4.7, +8.1] | +3.1% [−3.2, +8.2] | +0.9% [−5.8, +8.1] |
| 1.345 | 0.5 | 0.1153 | +3.4% [−4.8, +10.5] | +2.8% [−3.2, +7.8] | +0.8% [−5.8, +8.2] |
| 2.0 | 0 | 0.1126 | +1.1% [−5.5, +7.2] | +4.0% [−3.0, +7.6] | +0.2% [−5.1, +5.9] |
| 2.0 | 0.25 | 0.1146 | +2.9% [−5.3, +8.8] | +2.8% [−3.4, +6.8] | −0.2% [−5.3, +5.2] |
| 2.0 | 0.5 | 0.1138 | +2.1% [−5.9, +9.8] | +2.3% [−3.6, +5.7] | +0.2% [−5.8, +5.3] |

The minimum-bearings setting (30, 60, 120) changes nothing to four figures (largest difference
2.7e-08): every scored row already has more than 120 bearings. The table shows 60.

## Choice

**Huber constant 2.0, no shrinkage, minimum bearings 60** (`configs/gateh/gh-draft.json`), by the
declared rule: the lowest median range error on the primary condition.

## Critical reading

- **The grid barely matters.** The nine distinct settings span 0.1126 to 0.1170 on the primary
  condition, inside every interval. The choice is the rule's, not a finding.
- **The chosen value is at the edge of the grid** (the loosest Huber constant). A looser one
  might be slightly better still. It was not explored: a wider search for a gain this far inside
  the noise would be tuning to seed 320.
- **The clean-data cost cannot be resolved here.** Its point value runs from +1.4% to +4.0% with
  intervals about ±6 points wide, and on the rows every estimator answers it is within ±1% for
  every setting. The differences between the two columns come from a handful of rows the control
  does not answer, not from the typical row.
- **300 scenarios is small.** Validation (1,000) and test (5,000) will be much tighter.
