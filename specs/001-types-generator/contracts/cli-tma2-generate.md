# Contract: `tma2-generate`

Mirrors gitma's `tma-generate` (`packages/data/src/cli-generate.ts` at `d0aec60`).

```
tma2-generate --seed <uint64> --count <n> --out <dir>
              [--ranges <file>] [--heldout-ranges <file>]
              [--noise-free] [--allow-dirty] [--format ndjson|f32pack|both]
```

| Option | Required | Meaning |
| --- | --- | --- |
| `--seed` | yes | dataset seed, decimal string 0 … 2^64 − 1, parsed exactly |
| `--count` | yes | positive integer; train/validation/test cover `[0, count)`, held-out adds `⌊count/10⌋` |
| `--out` | yes | output directory, created if absent |
| `--ranges` | no | `ParameterRanges` JSON; default: gitma's iteration-1 `DEFAULT_RANGES` |
| `--heldout-ranges` | no (yes with target manoeuvres) | `ParameterRanges` JSON for the held-out split; default: `DEFAULT_RANGES` with 20–30 km initial range |
| `--noise-free` | no | σ list → [0], dropout → 0–0 for both ranges; recorded in `created_by` |
| `--allow-dirty` | no | proceed in a dirty or non-git checkout, recording `generator_git_dirty: true` |
| `--format` | no | `both` (default), `ndjson`, `f32pack` |

**Outputs** in `--out`: `<split>.ndjson` and/or `<split>.f32pack` for `train`, `validation`,
`test`, `heldout`, and `digests.json` (`{"<file>": "<sha256 hex>"}` for every file written).
Files are written to `<name>.tmp-<pid>` and renamed on completion.

**Header `created_by`**: `tma2-generate --seed S --count N[ --noise-free][ --ranges sha256:<digest>][ --heldout-ranges sha256:<digest>]` (the same shape as gitma's, with the program name changed).

**Stdout on success** (one JSON line):

```json
{"out": "<dir>", "splits": [{"split": "train", "scenarios": 80, "redraws": 12, "files": ["…"]}, …],
 "seconds": 1.23, "scenarios_per_s": 1234}
```

**Exit codes**: 0 success; 2 usage error or refusal (bad seed, bad count, bad format, ranges
with target manoeuvres but no held-out ranges, dirty tree without `--allow-dirty`, invalid ranges
JSON); 1 unexpected error. Messages go to stderr and match gitma's wording where gitma has one.

**Determinism**: for the same arguments and the same code commit, every output file is
byte-identical; `created_by`, `generator_git_commit` and `generator_git_dirty` are the only
header fields that depend on the environment.
