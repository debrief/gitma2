# CLI contracts: spec 006

## tma2-generate (extended)

```
uv run tma2-generate --seed <uint64> --count <n> --out <dir> --ranges configs/man2-ranges.json \
    --heldout-ranges <f> [--noise-free] [--allow-dirty] [--format f32pack|ndjson|both]
```

- Accepts the new ranges fields. Validation errors, in gitma's style:
  - `target_leg_length_s cannot be combined with target_course_change_count_weights,
    target_manoeuvre_spacing_s, target_manoeuvre_after_zig_s or target_manoeuvre_margin_s`;
  - `ownship_wander or ownship_oscillation needs ownship_wander_weights`;
  - `target_change_kind_weights needs target_leg_length_s`.
- The header records `generator_version: 0.6.0`, the ranges, and per scenario `ownship_wander`
  and `zig_on_manoeuvre`.
- Output for ranges without the new fields is byte-identical to 0.5.0 (except the version
  string in the header, which the digest check excludes as it did for earlier versions).

## tma2-ranges (new)

```
uv run tma2-ranges --describe <ranges.json> [--sample <n> --seed <uint64>]
```

- Prints the effective model: generator semantics selected, window, leg-length law with its
  5th/50th/95th percentiles, kind weights, turn and acceleration rates with implied transition
  durations, wander settings.
- With `--sample`, generates n scenarios in memory and prints measured leg-length quantiles,
  share of legs ≤ 10 min, transition-duration quantiles, changes per engagement, wander kinds
  drawn, zig-on-manoeuvre count. Exit 0; this is a diagnostic.

## tma2-p0 (extended)

```
uv run tma2-p0 --experiment experiments/<id> [--oracle-data <dir>] [--gitma-imm <file>]
```

- The window rows come from the experiment's ranges (`rows_for`), not a constant.
- On ranges with `target_leg_length_s`, the before-manoeuvre check is the "on the zig leg" check
  (research R3) and reports the skipped count; other checks unchanged. Exit 3 when the gate is
  not passed.

## Conformance export

`uv run python -m tma2.export.onnx_export --out <dir> [--rows 360|720]`, both artefacts built and
checked in CI.
