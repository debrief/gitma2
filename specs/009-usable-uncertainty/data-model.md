# Data model: spec 009

## PredictionRow (additive, schema 0.30.0)

| Field | Meaning |
| --- | --- |
| `course_arc_rad` | X: the course arc half-width (≤ Xmax), radians |
| `course_arc_prob` | P: the stated probability that the true course lies within ±X of `course_rad` |
| `course_conc` | the von Mises concentration κ of the peaked part (for the log score) |
| `course_mix_p` | p: the peaked part's weight (1 − p uniform) |
| `range_ratio_q95` | the 95% half-width of ln(range ratio) |
| `speed_q95_mps` | the 95% half-width of speed |

All optional; absent rows are scored as "no statement" (not covered; course P = 0).

## StatementHeadConfig / StatementTemperatureConfig

As spec 008's head and temperature configs, with `xmax_rad`, the bounds of the four outputs, the
loss weights (standardised by the temperature's tuning means) and the isotonic map's knots
(fitted on tuning ordinals 0–499).

## Gate4Criteria / Gate4Decision

As Gate 3's, with: `coverage95` band; `reliability_overall` (±0.03), `reliability_bin` (±0.05) and
`bins` (5); `min_mean_prob` (0.5); the learning rule; the carried and shuffled rules; the forecast.

## Per-row calibration array (scorer)

Columns: |e| log range ratio, |wrapped e| course, |e| speed; the three half-widths (X, q_range,
q_speed); P, κ, p; the course log score; NEES (reference only); cov_ok; plausible.
