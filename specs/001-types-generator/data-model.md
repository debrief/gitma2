# Data model: Types and Generator (foundations, part 1)

Every persisted type is defined in `schema/tma.yaml` (LinkML 0.16.0, carried from gitma) and
generated into `src/tma2/types/generated/`. This document names the entities this feature uses,
their invariants, and the in-memory batch arrays that are *not* persisted. Field lists are the
schema's; see the generated data dictionary for descriptions and units.

## Persisted entities (schema)

| Entity | Role here | Invariants enforced beyond the schema |
| --- | --- | --- |
| `ParameterRanges` | Per-dataset sampling ranges; input to the generator; stored in every header | `window_s.min ≤ max`; `dt_s > 0`; `target_course_change_count_weights` requires angle, rate, after, margin, spacing (and speed-change ranges when the fraction > 0) and excludes `target_manoeuvre_fraction`; `zig_rule: across_los` requires `los_offset_rad` (all as gitma's error messages) |
| `ScenarioParameters` | One scenario's draws, all float32-rounded | Optional keys absent unless drawn (turn rate, zig2, 0.4.0 manoeuvre fields, `target_manoeuvres`) |
| `TargetManoeuvre` | A planned manoeuvre: kind, start time, change, rate | `start_time_s` is a whole sample |
| `PlatformState` | (t, x, y, course, speed) per sample | course in [0, 2π) as float32 and < 2π |
| `Track` | id (`ownship`/`target`) + states | `len(states) == metadata.samples` |
| `Observation` | (t, bearing, valid) | bearing 0 when invalid |
| `ManoeuvreSpan` | (kind, start_index, end_index) | ordered, non-overlapping, `start_index = k + 1` |
| `ScenarioMetadata` | seed (decimal string), index, parameters, samples, zig/turn indices, manoeuvre indices and spans, zig time, mean and min range | optional index keys present only when the feature exists (as gitma) |
| `Scenario` | record `scenario` + metadata + tracks + observations | lengths consistent |
| `DatasetHeader` | record `header`; schema and generator versions; seed; split; counts; bounds; ranges; redraws; `created_by`; commit; dirty | first record of every file; `index_end − index_start == scenario_count` |

**Versions.** `schema_version` compatibility: same major, file minor ≤ build minor.
`generator_version` readable set: `{0.1.0, 0.2.0, 0.3.0, 0.5.0}` as gitma's
`READABLE_GENERATOR_VERSIONS` (0.4.0 files are readable by gitma only through the current code;
gitma2 lists the same set and adds 0.4.0 if a fixture needs it).

**Splits.** `train [0, ⌊0.8c⌋)`, `validation [⌊0.8c⌋, ⌊0.9c⌋)`, `test [⌊0.9c⌋, c)`,
`heldout [c, c + ⌊c/10⌋)` with the held-out ranges.

## Generator-internal records (not persisted)

| Record | Content | Lifetime |
| --- | --- | --- |
| `RangesStruct` | `ParameterRanges` flattened to numeric scalars and small fixed arrays (σ list, count weights) with presence flags for optional groups, so the numba kernel takes no Python objects | per call |
| `RngState` | four uint32 words (xoshiro128**) | per scenario attempt stream; a second one for the manoeuvre count |
| `Truth` | float64 arrays own x/y/course, target x/y/course/speed; indices (zig, turn start, zig2, turn2 start, manoeuvre start/end); spans | per accepted attempt |

## Batch (in-memory, training path)

Produced by `tma2.features.batch.generate_batch(seed, batch_index, batch_size, ranges, start=0,
end=None)`; `R = rows_for(ranges)`.

| Array | Shape | dtype | Meaning |
| --- | --- | --- | --- |
| `index` | (B,) | int64 | scenario indices |
| `samples`, `zig_index` | (B,) | int32 | window length in rows; first row on leg 2 |
| `sigma`, `dropout` | (B,) | float32 | per-scenario noise σ (rad) and dropout fraction |
| `redraws` | (B,) | int32 | attempts discarded |
| `t` | (B, R) | float32 | seconds since window start; 0 beyond `samples` |
| `mask` | (B, R) | bool | row inside the window |
| `own` | (B, R, 4) | float32 | ownship x, y, course, speed |
| `tgt` | (B, R, 4) | float32 | target x, y, course, speed (truth labels) |
| `bearing` | (B, R) | float32 | observed bearing (0 when invalid) |
| `valid` | (B, R) | bool | bearing observed |
| `manoeuvring` | (B, R) | bool | a target manoeuvre span covers the row |
| `last_kind` | (B, R) | int8 | −1 none yet, 0 course, 1 speed |
| `since_zig_s` | (B, R) | float32 | `(row − zig_index) · dt`, negative before |
| `since_manoeuvre_end_s` | (B, R) | float32 | seconds since the last completed manoeuvre, −1 before any |
| `spans` | (B, 4, 3) | int32 | (kind, start_index, end_index) padded with −1 |

All stored-value arrays hold the same float32 values the file path writes (the kernel rounds
once; the file writer serialises those values), so a batch row equals the decoded file row.

## State transitions

Generation has no persistent state. A dataset directory moves from *absent* → *being written*
(temporary files) → *complete* (renamed files + `digests.json`); an interrupted write leaves only
temporary files, which readers ignore and the CLI removes on the next run with `--out` pointing
at the same directory.
