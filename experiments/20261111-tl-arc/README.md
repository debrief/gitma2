# Spec 013: the arc-model solve (tuning seed 329; never a gate result)

Owner decision 2026-11-11, after the first checkpoint (`../20261111-tl-diagnosis/`): add a
classical solve that models a manoeuvre as a turn at a constant rate and a speed change at a
constant rate between two times (`src/tma2/timelate/arc.py`), and measure how much of the
chord reference's factor it recovers when the kind is not told.

Data: 60 periods cut from 5-second MAN2 engagements of seed 329 (`configs/timelate/tl-ranges.json`,
ordinals 0–59 of `train`), 57 with determined rows (31,537 rows; bound on relative range below
0.5). Scripts as run: `scripts/research/tl_arc.py` (four shards of 15), `tl_arc_pool.py`
(output: `pooled.txt`), `tl_arc_starts.py` (the start-point study). Rows within a period are
correlated; efficiencies are pooled over rows and carry no interval. Ratios of the median over
periods of each period's median range error carry a period bootstrap.

## What was measured

| Solve | Manoeuvre times | Efficiency: range, course, speed | Median period range error | Periods over 10% |
| --- | --- | --- | --- | --- |
| Chord (the old reference) | true | 1.87, 2.27, 1.95 | 0.044 | 0.25 |
| Arc, kind told | true | 1.23, 1.16, 1.15 | 0.029 | 0.16 |
| Arc, kind judged from the data | true | 1.43, 1.31, 1.38 | 0.036 | 0.21 |
| Chord (C″ to the period's end, no fade) | C″'s | 3.84, 4.97, 3.86 | 0.113 | 0.54 |
| Arc, kind judged | C″'s | 5.32, 7.27, 5.24 | 0.158 | 0.60 |
| One leg | none | 20.7, 15.8, 20.1 | 0.318 | 0.88 |

Ratios of median period range error [95% interval over periods]:

- chord ÷ arc, true times: 1.20 [0.86, 1.86]. **Not separated** on 57 periods.
- chord ÷ arc, C″'s times: 0.72 [0.41, 1.28]. Not separated; the point says the arc is worse.
- arc on C″'s times ÷ arc on true times: 4.3 [2.3, 6.4].
- chord on C″'s times ÷ chord on true times: 2.6 [1.5, 4.0].
- arc kind judged ÷ kind told: 1.27 [1.00, 1.87]. The kind was judged right for 85 of 108
  manoeuvres.

## Reading

1. Told the true times, the arc solve is near the bound (1.2 with the kind, 1.4 without)
   where the chord is at 1.9. The efficiency gain is clear over rows; the gain in the median
   period's range error (0.044 to 0.036) is not separated at this sample size.
2. On C″'s own transitions the arc solve is no better and probably worse. A stricter model is
   less forgiving of a missed or mistimed manoeuvre; the chord's extra freedom was absorbing
   segmentation error. The arc solve is therefore **not** a drop-in final solve for C″.
3. The segmentation is the larger factor either way: 2.6 with the chord, 4.3 with the arc.
   With the arc reference, the headroom above C″ read as a track is about a factor of three
   in median range error (0.113 against 0.036), where the chord reference showed 2.6.

## How the solve was made to work (all on tuning data)

- A manoeuvre's `start_index` is the first row already inside it: the span starts one row
  earlier. With this, the model reproduces a true track to a median of 10 m.
- From the chord solution, plain least squares wound turns round (course changes of −800°)
  in 5 of 12 engagements. Turns are bounded below 172°, speed changes to 6 m/s, and an
  iteration moves any angle at most 0.5 rad.
- A cost consistent with the bearing error does not show the fit is right: a mirror solution
  with one turn's sign wrong was consistent. Each manoeuvre's course change is restarted from
  four values (±46°, ±100°) and the lowest cost kept.
- Kind: every manoeuvre is fitted as a turn, then given both changes, then changes are dropped
  while the cost rises by less than 6.63 (chi-square(1), 1%).
- On 24 whole engagements, kind told: 1.56, 1.21, 1.42 from the chord start against 1.32,
  1.09, 1.24 from the truth: some starts still end in a worse minimum.

## Limits

- 57 periods; one tuning seed; thresholds and start values were chosen on these same data.
- "True times" are the generator's rows (5-second grid); no real system has them.
- The arc model is the generator's own manoeuvre model, apart from a "both" manoeuvre's two
  durations. Its advantage over the chord is partly that match; on real data a target need
  not turn at a constant rate.
- The search costs 10 to 30 fits a period (about 2 to 10 s on one core).

## Consequence

The reference for spec 013 becomes the arc solve on the true times, kind judged (kind told
reported beside). The planned full-period re-test is where the headroom is: it must find the
manoeuvres the causal segmenter missed, and the arc cost is the natural test statistic for
that (a manoeuvre is added, moved or removed when the whole-period fit says so).
