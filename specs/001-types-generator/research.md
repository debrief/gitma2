# Research: Types and Generator (foundations, part 1)

Sources: gitma at commit `d0aec60` (`packages/sim/src/{prng,scenario,geometry,ranges}.ts`,
`packages/data/src/{generate,f32pack,ndjson,canonical,io,provenance,versions}.ts`,
`packages/data/test/golden/*`, `site/scripts/prebuild.mjs`, `.github/workflows/ci.yml`,
`pyproject.toml`), read on 2026-10-31. Each item ends with a decision.

## R1 gitma's per-scenario algorithm and draw order

**Seeding.** `scenario_seed = splitmix64At(dataset_seed, index)` where
`splitmix64At(seed, n) = mix64(seed + (n + 1) · GAMMA)` with Steele–Lea–Flood constants, all mod
2^64. The scenario stream is xoshiro128** seeded from two further SplitMix64 outputs of the
scenario seed (`createRng`: words a_lo, a_hi, b_lo, b_hi; all-zero state → word 0 set to 1).
Under 0.5.0 ranges the **manoeuvre count** comes from a *second* stream,
`createRng(splitmix64At(scenario_seed, 1))`: one uniform picks the course-change count from
the cumulative weights, a second uniform decides the speed change. It is drawn once per scenario,
before any redraw, so redraws do not alter the realised count distribution.

**Primitives.** `uniform01 = ((u32 >>> 5) · 2^26 + (u32 >>> 6)) / 2^53` (two u32 draws);
`uniform(lo, hi) = lo + (hi − lo) · uniform01`; `logUniform = exp(uniform(log lo, log hi))`;
`gaussian`: Box–Muller `sqrt(−2 log(1 − u1)) · cos(2π u2)`, second variate discarded;
`uniformInt(n) = floor(uniform01 · n)`.

**Draw order per attempt** (`drawScenario`): samples (uniformInt over the window range in
samples), ownship speed, course0, |zig|, zig sign, zig fraction, range0 (log-uniform or uniform),
bearing0, target speed, target course, σ (uniformInt over the σ list), dropout fraction, then,
only if the ranges have `ownship_turn_rate_rad_s`, the turn rate. Then `planManoeuvres` (0.3.0):
if `zig_rule` is `across_los` draw the first LOS offset; if `zig2_delay_s` exists draw the delay
(f32) and then either the second LOS offset (across) or |zig2| and its sign; compute the first
zig angle from the geometry at sample `round(zig_fraction · samples)` on the straight two-leg
path, and the second from the two-leg truth at `zigIndex + round(delay / dt)` if that sample is
inside the window. Then `planTargetManoeuvre` (0.4.0, only with `target_manoeuvre_fraction`):
four draws regardless of whether the target turns. Then `planTargetManoeuvres` (0.5.0, only with
`target_course_change_count_weights`): for every *possible* course change (weights.length − 1 of
them) sign, |angle|, rate; the speed change's sign, |dv|, rate; the speed change's place; one
uniform per possible manoeuvre for timing. All are consumed whether used or not. Fit: a speed
change that leaves the target-speed range either way does not fit if a speed change was drawn;
timing slack `free = hiEnd − lo − total` must be ≥ 0 when there is at least one manoeuvre;
offsets are `min(free, floor(u · (free + 1)))` sorted ascending.

**Redraw rules** (`generateScenario`, up to 1,000 attempts, counted in `redraws`): parameters
that do not fit; a first or second turn that does not complete inside the window; minimum
range over the window below `min_range_m`. Observations are drawn **after** acceptance, from the
same stream: per sample one gaussian and one uniform (dropout), always both.

**Truth simulation.** Ownship: instantaneous zig when no turn rate; otherwise a constant-rate
arc from sample `zigIndex` (still on course c0) with `leg2` the first sample at or after the arc
ends (`turnRows` logic), `turn_start_index = zigIndex + 1`, `zig_index = leg2`; the second zig
likewise from `k2 = zig_index + round(delay / dt)`. Target: straight, then 0.4.0 single turn or
0.5.0 ordered manoeuvres with closed-form end states (`arcPosition`; constant acceleration along
course for speed changes), `manoeuvres` spans `[k + 1, k + turnRows(dur))`. Metadata rounds
`zig_time_s`, `mean_range_m`, `min_range_m` to float32.

**JavaScript semantics that must be matched.** `Math.round` is round-half-up (floor(x + 0.5));
Python's `round` is banker's: implement `js_round`. `Math.fround` = cast to float32 and back;
`+ 0` maps −0 to +0. `%` on doubles is `fmod` (sign of dividend). `Math.imul` and `>>> 0` are
uint32 arithmetic. `Math.hypot` → `math.hypot` (both sub-ulp accurate).

**Decision**: port `scenario.ts` line for line as a scalar algorithm, keeping every draw and
its order, including the draws that are consumed and discarded. Redraw and fit logic is copied
verbatim. A table in `scenario.py`'s docstring maps each Python function to its gitma source.

## R2 Vectorisation without changing stream consumption

Options: (a) batched NumPy with per-scenario RNG state arrays and masked redraw loops; (b) a
scalar per-scenario kernel under numba, parallelised over scenarios with `prange`; (c) pure
Python per scenario (too slow: gitma's JS does 550–1,000/s; CPython would do ~50/s).

(a) fails constitution II in practice: redraws make the number of stream draws per scenario
data-dependent, so a lock-step batched loop must mask and re-run attempts per lane, and any
divergence in draw order is a silent conformance failure. (b) keeps the algorithm identical to
gitma's, is parallel-safe because each scenario touches only its own RNG state and its own output
rows, and numba compiles the uint32/uint64 arithmetic and the double maths natively.

**Decision**: (b). The kernel signature is
`generate_into(dataset_seed: uint64, index: int64, ranges: RangesStruct, out_rows…)` writing into
preallocated padded arrays; a `prange` wrapper fills a batch. The file writer calls the same
kernel per scenario (sequentially or in batches) and serialises. Throughput target is met with
margin: the JS version does ~550/s single-threaded on phase-4 ranges; the compiled kernel is
expected 3–10 × faster per core (measured in a perf test, SC-003). Numba's first-call compile
(~5–10 s) is cached on disk (`cache=True`) and warmed in CI.

**Parallel safety**: no shared mutable state; the manoeuvre-count stream and the scenario stream
are local; outputs are written to disjoint row ranges; `prange` with `parallel=True` and
`NUMBA_NUM_THREADS` defaulting to the core count. The batch function also accepts
`workers=1` for debugging; the result must be identical (SC-002).

## R3 Floating-point and the one-ulp tolerance

gitma computes in float64 and rounds stored values to float32 (`f32`, `f32Angle`). V8's
transcendental functions (fdlibm-derived) and glibc's libm can differ in the last double bit.
After float32 rounding such a difference survives only when the double lies within ~1e-16
relative of a float32 rounding boundary: about 2^-29 per value, so a few per million stored
floats. Two risks are larger than a stored-value flip:

1. **Decisions on doubles**: redraw tests (`min < min_range_m`, fit tests, `turnRows` loops
   comparing `k · dt < turnS`) and `uniformInt` floors. A last-bit difference there changes a
   whole scenario. These are rare (a comparison must land within 1e-16 of its threshold) but not
   impossible; the conformance test reports them as a scenario-level mismatch, which fails.
2. **Angle wrap at 2π**: `f32Angle` returns 0 when the float32 value reaches 2π; copied exactly.

**Decision**: compute in float64 with the same operation order as gitma; use `math`/`numpy`
scalar functions inside numba (which lower to the platform libm or LLVM intrinsics); accept the
constitution's 1-ulp float32 residual and report it; treat any scenario-level divergence as a
failure to investigate, not to tolerate. If a decision-boundary case appears in a fixture, the
fixture seed is kept and the discrepancy documented, never hidden by changing the seed.

## R4 Canonical JSON and JavaScript number formatting

gitma writes `JSON.stringify` with sorted keys and no whitespace. Number formatting follows
ECMAScript `Number::toString`: shortest round-trip digits (same as Python's `repr`), but integral
values below 1e21 print without a fractional part (`1930` not `1930.0`), exponent notation only
for |x| ≥ 1e21 or |x| < 1e-6 (Python switches at 1e16 and 1e-4), and the exponent is written
`e+21` / `e-7`. Booleans and nulls match; strings are UTF-8 with the same escapes for the
characters that occur here (none beyond ASCII).

**Decision**: `canonical.py` serialises with `json.dumps(sort_keys=True, separators=(",", ":"),
ensure_ascii=False)` and a float formatter that takes `repr(x)`'s digits and exponent and
re-renders them with JavaScript's thresholds. Unit tests cover integers, small and large
magnitudes, 2π-adjacent values, and every float in the gitma fixtures (round-trip equality of the
whole file is the real test).

## R5 Float32-pack layout

Little-endian. `"TMAPACK\0"` (8) · u32 format version 1 · u32 header length H · header JSON
(canonical, space-padded to a multiple of 4) · u32 N · u64 × (N + 1) block offsets (absolute
file positions; offset N = file size) · blocks. Block: u32 M · metadata JSON (M bytes, padded to 4)
· u32 S · f32 ownship [S × 5: t, x, y, course, speed] · f32 target [S × 5] · f32 observations
[S × 3: t, bearing, valid 0/1]. Writer writes a zeroed offset table first and patches it on close;
abort removes the temporary file.

**Decision**: implement writer and reader in NumPy (`np.frombuffer`), with the same validation
messages as gitma (bad magic, version, truncated, count mismatch, block length mismatch).
Round-trip test: NDJSON → pack → NDJSON byte-equal.

## R6 Schema generation and the data dictionary

gitma generates TS/zod from LinkML's JSON Schema. In Python: `gen-pydantic schema/tma.yaml`
(linkml 1.12) gives Pydantic v2 models with enums; `gen-json-schema` gives the JSON Schema
(committed for other consumers); `gen-markdown-datadict --anchor-style mkdocs` gives the data
dictionary, post-processed as gitma's `prebuild.mjs` does (drop H1 and empty Mermaid blocks,
qualify slot anchors) plus a units table. Optional slots must be omitted when absent to match
gitma's output: dump with `exclude_none=True` and validate that generated models forbid extra
keys (`extra="forbid"` via a generation option or a post-processing wrapper).

**Decision**: `scripts/gen_types.py` runs both generators into `src/tma2/types/generated/` and
has a `--check` mode that regenerates to a temporary directory and diffs; CI runs the check.
`scripts/data_dictionary.py` writes `site/docs/data-dictionary.md` and is called by the site's
prebuild. The schema file is byte-identical to gitma's; its `version` is bumped only if a slot is
added (none planned in 001).

## R7 Toolchain versions

- **Python 3.12**: numba 0.61 supports 3.10–3.13; 3.12 is the conservative choice and matches
  gitma's `requires-python`. Pinned in `.python-version`; CI uses `astral-sh/setup-uv`.
- **numba** ≥ 0.61, **numpy** ≥ 2.0 (numba 0.61 supports NumPy 2.x), **pydantic** ≥ 2.7,
  **linkml** 1.12 (dev group), **pytest**, **ruff**, **mypy** (numba-decorated functions are typed
  with their Python signatures; `numba` ships no stubs, so a small `typings/numba.pyi` or
  `ignore_missing_imports` for that one module).
- **Node 22** for the site only (Docusaurus 3), as gitma.

**Decision**: as listed; `uv lock` committed; dependency groups `dev` (linkml, ruff, mypy,
pytest) so runtime stays numpy + numba + pydantic.

## R8 Conformance fixtures

gitma's committed golden `packages/data/test/golden/seed1-count10-test.ndjson` was produced with
the in-code `DEFAULT_RANGES`/`HELDOUT_RANGES` (iteration 1: 600–2,400 s windows, instantaneous
zig, σ ∈ {0.5°, 1°, 2°}, dropouts 0–10%, held-out ranges 20–30 km) and the fixed test provenance
(`generator_git_commit` 0123…4567, dirty false). Its `created_by` is `tma-generate --seed 1
--count 10` without ranges digests. The two other fixtures are generated now from the local
gitma checkout at `d0aec60` with `pnpm -s tma-generate --seed 777 --count 100 --format both
--allow-dirty` (the checkout is clean, so the header records dirty false) with
`configs/phase4-ranges.json` + `configs/phase4-heldout-ranges.json`, and with
`configs/iter4-ranges.json` + `configs/iter4-heldout-ranges.json`. Committed per fixture: the
four `.f32pack` splits (~15 KB per scenario), `test.ndjson` (10 scenarios), `digests.json`, the
two ranges files, and a `COMMIT` file; about 1.7 MB per fixture.

**Comparison rule**: scenarios compared field by field after parsing; header compared except
`created_by`, `generator_git_commit`, `generator_git_dirty` (reported, not asserted, because
the generating command and commit differ by construction); `redraw_count` asserted. NDJSON text
of the test split additionally compared byte for byte after re-serialising gitma's records with
gitma2's canonical JSON (proves R4) and, as a stricter optional check, gitma2's own output text
against gitma's file.

**Decision**: three fixtures as above, produced by `scripts/make_fixtures.sh`, which records the
exact commands and the gitma commit; `DEFAULT_RANGES` is materialised as
`tests/fixtures/gitma/iter1/ranges.json` (identical to gitma's `configs/iter1-ranges.json` except
σ list and dropout, which the in-code constants set to three σ values and 0–10%; the fixture
carries the in-code values).

## R9 Batch interface for training

Rows per window: `rows_for(ranges) = floor(window_s.max / dt_s)` (360 for phase 4, 240 for
iteration 4), as gitma's `rowsFor`. The batch is index-defined: batch `b` of size `B` over
`[start, end)` holds indices `start + b·B … min(start + (b+1)·B, end)`. Arrays (float32 unless
stated): `own[B, R, 4]` (x, y, course, speed), `tgt[B, R, 4]`, `bearing[B, R]`, `valid[B, R]`
(bool), `mask[B, R]` (bool), `t[B, R]`, and labels `manoeuvring[B, R]` (bool),
`last_kind[B, R]` (int8: −1 none, 0 course, 1 speed), `since_zig_s[B, R]`,
`since_manoeuvre_end_s[B, R]` (−1 before any), plus per-scenario `index[B]` (int64),
`zig_index[B]`, `samples[B]`, `sigma[B]`, `redraws[B]`, and the manoeuvre spans as a ragged
`(B, 4, 3)` int32 array padded with −1 (at most 3 course + 1 speed). Scenario parameters are not
in the batch (they are metadata); a `metadata=True` option returns the Pydantic objects for the
file path.

**Decision**: as above, in `features/batch.py`, produced by the same kernel as the file path so
the two cannot drift; a test asserts that a batch's rows equal the rows decoded from a file for
the same indices.

## R10 CLI, provenance, atomic writes

Mirror gitma's `tma-generate`: `--seed` (decimal uint64 string, exact), `--count`, `--out`,
`--ranges`, `--heldout-ranges`, `--noise-free`, `--allow-dirty`, `--format ndjson|f32pack|both`;
a ranges file with target manoeuvres requires `--heldout-ranges`; provenance read once before any
output from the package's own checkout (`git rev-parse HEAD`, `git status --porcelain`), refusing
a dirty tree or a non-git checkout without `--allow-dirty`; `created_by` records the command with
`sha256:` digests of the ranges files; writes go to `path.tmp-<pid>` then rename; splits
80/10/10 by index and held-out `count/10` indices after them with the held-out ranges;
`digests.json` with SHA-256 of every file written. Exit codes: 2 usage or refusal, 1 unexpected.

**Decision**: as above; argparse; the JSON summary printed on success matches gitma's shape
(`out`, `splits[]`, `seconds`, `scenarios_per_s`).
