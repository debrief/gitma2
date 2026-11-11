# Data model: spec 013

## PeriodCut (in a period's meta)

`source_index`, `offset_rows`, `rows`, `dt_s`, `ownship_manoeuvres_inside`,
`target_manoeuvres_inside`, `began_before` (target manoeuvre in progress at the first row),
`cut_seed`. The period's `manoeuvres` are re-indexed to its own rows.

## NormalPoint (arrays beside the bearings)

`t`, `bearing`, `weight` (number of bearings stood for; variance σ² / weight), `first_row`,
`last_row`. A form's settings: `kind` (drop, fixed, adaptive, robust), `n` or `tolerance`,
`max_rows`.

## TrackSolution (one NDJSON record per period)

`ordinal`, `scenario_index`, `estimator`, `rows`: per row `timestamp_s`, `x_m`, `y_m`,
`course_rad`, `speed_mps`, `range_m`, `determined` (bool), `sd_log_range`; `manoeuvres`:
intervals in the period's rows; header with dataset digest, settings, C's digests, commit.

## Track score (`errors.npz`, `metrics.json`)

Per period and estimator: median and P90 over determined rows of relative range, metres,
course and speed errors; rows determined; manoeuvre counts. Pooled: medians over periods with
intervals; strata; headroom H.

## GateTCriteria / GateTDecision

`t_a` (efficiency band, compression cost limit), `t_b` (0.10, level 0.975), thresholds for
"undetermined", seeds, sizes, plan digest, C's digests, the full-period system's settings,
forecasts.
