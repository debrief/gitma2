# Contract: file formats

Identical to gitma's (`specs/001-iteration-0-pipeline/contracts/file-formats.md` and
`packages/data/src/{ndjson,f32pack,canonical}.ts` at `d0aec60`). A file written by either
repository is read by the other.

## Canonical JSON

- Object keys sorted (code-point order), no whitespace, UTF-8.
- Numbers formatted as ECMAScript `Number::toString`: shortest round-trip digits; integral values
  with |x| < 1e21 without a fractional part; decimal notation for 1e-6 ≤ |x| < 1e21, otherwise
  exponent notation `d.ddde+NN` / `d.ddde-NN`; `-0` never occurs (stored floats map it to `+0`).
- Optional fields absent (never `null`).

## NDJSON (`<split>.ndjson`)

Line 1: `DatasetHeader`. Lines 2…: one `Scenario` per line, `scenario_count` of them. No blank
lines. Readers validate every record, check `schema_version` compatibility (same major, file
minor ≤ build minor) and `generator_version` ∈ readable set, and fail with file, line and reason.

## Float32-pack (`<split>.f32pack`)

All little-endian.

```
offset 0   "TMAPACK\0"                    8 bytes magic
       8   u32  format version = 1
      12   u32  H = header JSON length (padded)
      16   header JSON (canonical, space-padded to a multiple of 4)
    16+H   u32  N = scenario count
   20+H    u64 × (N+1) absolute block offsets; offsets[N] = file size
           blocks…
block:     u32  M = metadata JSON length (padded)
           metadata JSON (canonical ScenarioMetadata, space-padded to 4)
           u32  S = samples
           f32  ownship  S × (t, x, y, course, speed)
           f32  target   S × (t, x, y, course, speed)
           f32  observations S × (t, bearing, valid 0|1)
```

Readers reject: bad magic, unsupported version, truncated header or table, `N ≠ scenario_count`,
`offsets[N] ≠ file size`, truncated block, corrupted JSON, `S ≠ metadata.samples` or block length
mismatch, with gitma's messages.

**Round trip.** `ndjson → f32pack → ndjson` is byte-identical because every stored float is
already float32 and track ids / record kinds are implied.

## `digests.json`

`{"<file name>": "<sha256 hex>"}` for every split file written, sorted keys, written last.

## Conformance fixtures (`tests/fixtures/gitma/<name>/`)

`COMMIT` (gitma commit and command lines), `ranges.json`, `heldout-ranges.json`,
`<split>.f32pack` × 4, `test.ndjson`, `digests.json`. The comparison rule is in
`research.md` R8.
