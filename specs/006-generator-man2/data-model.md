# Data model: Generator 0.6.0

All types live in `schema/tma.yaml` (0.21.0 → 0.22.0) and are regenerated. Every new field is
optional; absent means 0.5.0 behaviour.

## ParameterRanges: new fields

| Field | Type | Meaning |
| --- | --- | --- |
| target_leg_length_s | {mean, sd, min} (s) | Target leg lengths ~ N(mean, sd) clipped at min, laid end to end with a uniform first phase. Present ⇒ the 0.5.0 count weights, spacing, after-zig and margin fields must be absent (validation error otherwise) |
| target_change_kind_weights | {course, speed, both} | Weights of what ends a leg; sum normalised |
| ownship_wander | {sd_rad, tau_s, clip_rad} | Helm wander parameters |
| ownship_oscillation | {amp_rad: {min, max}, period_s: {min, max}} | Autopilot oscillation parameters |
| ownship_wander_weights | {none, wander, oscillation, both} | Per-scenario selection; required when either wander field is present |

Existing fields reused with MAN2 values in `configs/man2-ranges.json`: `window_s` 2400–7200,
`target_turn_rate_rad_s` 0.25–1°/s, `target_speed_change_rate_mps2` 0.01–0.05,
`target_manoeuvre_angle_abs_rad` 30–120°, `target_speed_change_abs_mps` as phase 4.

## Scenario header: new fields

| Field | Type | Meaning |
| --- | --- | --- |
| ownship_wander | OwnshipWander or null | Drawn kind and parameters |
| zig_on_manoeuvre | bool | The ownship zig row lies inside a target transition span |

### OwnshipWander

| Field | Type |
| --- | --- |
| kind | enum none, wander, oscillation, both |
| sd_rad, tau_s, clip_rad | float, present for wander |
| amp_rad, period_s, phase_rad | float, present for oscillation |

## ManoeuvreSpan

`kind` gains `both`. `start_index` and `end_index` as before; an open span ends at the last row.

## Flat layout (`ranges.py`)

New `R_*` slots appended after `R_TM_SPACING`: leg mean/sd/min, three kind weights, wander
sd/tau/clip, oscillation amp min/max and period min/max, four wander weights. `R_LEN` grows;
absent groups are NaN. `MAX_TM = 24`.

## Experiment records

- `experiments/<date>-g0-man2/`: the pipeline gate's manifest, checks, panel `review.md`,
  including the "on the zig leg" check's skipped count.
- `experiments/<date>-man2-tune/`: grids, per-point results, frozen IMM and EKF names.
- `experiments/<date>-man2-refs/`: `spike.json` from `leg_spike.py report` on seed 314 (GLR +
  confirm threshold and downstream ratios), detectability quantiles.
- `digests.json` for seeds 314, 315, 316, and the superseded note for 312/313.
