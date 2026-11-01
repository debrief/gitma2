# P0 agent review panel

Gate P0 (SRD §5, spec 002). Records: round 0 `experiments/20261031-p0/` (commit 5adb8bf, machine
pass 18/18, superseded), run r2 `experiments/20261101-p0-r2/` (commit 8e5dfe1, after the round-1
fixes). The panel follows the constitution: ≥ 5 independent read-only reviewers, blockers and
majors fixed or answered with evidence, re-invited until none rejects.

## Round 1 (2026-10-31): record `experiments/20261031-p0/` at commit 5adb8bf

Five read-only reviewers in parallel; the machine verdict was pass on 18 of 18 checks.

| Reviewer | Verdict |
| --- | --- |
| TMA geometry | approve-with-findings |
| Estimation and numerics | **reject** (1 blocker) |
| Evaluation statistics | approve-with-findings |
| Reproducibility | approve-with-findings (bit-for-bit re-run of every check) |
| Red team | **reject** (1 blocker) |

### Blockers

1. **NaN gradients on masked rows** (numerics). `sqrt(valid·exp(ℓ)·mask)` has an infinite
   derivative at 0, so invalid and beyond-k rows had NaN log-weight gradients and one backward
   pass made every encoder parameter's gradient NaN. *Fixed* (f24877e): `safe_sqrt` wherever a
   square root's argument can be 0 (bearing, ridge and speed weights, speed norms). New tests
   assert finite gradients on every input entry and every toy-model parameter, at the old and the
   production configuration; they fail on the old code and pass on the new.
2. **"Physics equals least squares" passed only on the rows it sampled** (red team). The check
   used every 20th row of one 10-scenario split and dropped undetermined rows (59 left); over all
   rows 2.4% of determined validation rows differed by more than 1e-4, the layer's cost above the
   solver's. *Root cause*: one trial step per iteration, so each rejected step cost a whole
   iteration (gitma's solver retries the damping inside one), and from the grid start 40
   iterations stopped short in flat valleys; also, the per-timestep rows compared against are
   warm-started and some sit in another minimum. *Fixed*:
   - the layer can try T damping values per iteration side by side; measured on all 22,531 scored
     fixture rows against the solver from the same grid start:

     | Iterations × trials | Rows where the layer stops short | Time |
     | --- | --- | --- |
     | 40 × 1 (round-0 layer) | 159 | 99 s |
     | 40 × 4 | 8 | 341 s |
     | 60 × 2 | 0 | 261 s |
     | 100 × 1 (adopted) | 0 | 202 s |

   - the check now covers every scored row of all four splits of both fixtures against
     `solve_batch` at that row: plausibility flags must agree (0 mismatches; 726 rows are runaway
     solutions both flag implausible), the layer's cost must never exceed the solver's by 1e-9
     (0 rows; worst +1.7e-10), and on the 21,438 plausible rows at equal cost the state must agree
     to 1e-4 relative on rows whose range is determined and to 1e-2 standard deviations on all.
     The run of this rule (r2, below) failed on speed.
   - spec 002 FR-007 / SC-002 are amended to say this (the SRD criterion is unchanged): the old
     wording, float32 on every row against warm-started rows, cannot hold for any two correct
     solvers on undetermined rows, and the machine check had tested 1e-4 on 59 rows. **Owner may
     overrule.**

### Majors

3. **Efficiency definition contradicted itself; SC-005 unchecked** (statistics). *Fixed*
   (fc3e71e): efficiency is median(|eᵢ|/σᵢ)/0.6745, 1 at the bound, and P0 gates least squares'
   speed efficiency on held-course σ = 1° rows in [0.8, 1.3].
4. **median|e|/median σ is biased when bounds vary in a slice** (statistics, simulated 0.674 →
   0.575 as the bounds spread). *Fixed* by the per-row normalisation in 3; caveats (unbiasedness,
   delta method on weak geometry, wrap, model on manoeuvring rows) are in the CRB note.
5. **Per-leg CRB mislabelled as the oracle's bound; mostly singular after a manoeuvre** (numerics,
   geometry). *Fixed*: a `known_manoeuvres` model, the generator's own kinematics with each
   manoeuvre's start, duration and kind known and its size unknown, all bearings to k. It
   reproduces the stored truth to 2 mm, is singular on 3 of 1,103 validation rows where per-leg
   is on 254, and matches a Monte-Carlo fit of the same model within the test's band. A
   free-interval variant was tried first and rejected: freeing the in-turn positions decouples
   the legs, which is no better than per-leg. Per-leg stays as a labelled diagnostic. The
   singularity test is now on the Jacobi-scaled matrix. CRB files became LinkML records
   (`CrbHeader`, `CrbRecord`, `CrbModel`): they had been hand-written JSON.
6. **IMM diverges from gitma at scale** (red team: 19 of 10,000 scenarios beyond 1e-4, flags
   identical). *Answered with evidence and a new check*: the 7 scenarios beyond 1e-4 in range
   are knife-edge: a 1e-15–1e-12 relative bearing jitter moves our own IMM as far (e.g. 82525:
   any jitter, even 1e-15, flips our run to gitma's branch, 9.9e-3 apart; 89977: 0.29 against
   0.42 from gitma; 83988: 7.3e-4 at 1e-12 against 7.6e-4). 82525's batch initialisation is
   degenerate (start position ≈ (0, 0)). New check `reference-imm-at-scale` (with
   `--gitma-imm`): flags identical, at most 0.1% of rows beyond 1e-4, G5 median range ratio 1 to
   1e-4.
7. **Cached predictions reused without checks; record claims a clean tree** (red team,
   reproducibility). *Fixed*: caches live under the code commit, are reused only from a clean
   tree after `check_bound` and the estimator name, and every file used is recorded with its
   SHA-256 (`ExperimentManifest.artefacts`, schema 0.17.0).
8. **Dataset digests from a dirty tree** (reproducibility). *Fixed*: the round-2 data were
   regenerated at 9cb2b49 without `--allow-dirty`.
9. **Export results untracked, CI's P0 would skip them** (reproducibility). *Fixed*: `tma2-p0`
   exports afresh (byte-deterministic), runs the Python leg itself and accepts the browser and Java
   legs only if `results.json` names that export's SHA-256; a missing file or browser leg fails.
   The CI `p0` job now takes the conformance job's results, fails on exit 3, drops
   `--allow-dirty` and widens its cache key.
10. **The oracle is not a ceiling** (geometry: noise-free, most post-turn error is the chord;
    masking in-turn bearings drops the median from 2.0% to 0.2%). *Answered*: the P0 check
    reproduces note 05 and stays valid (independent SciPy code); the docs now call it a
    reference, not a strict ceiling, and P0 reports a masked-turn variant as a diagnostic. With
    noise (r2, seed 301) masking does *not* help: masked-turn 0.539 [0.519, 0.561] against chord
    0.531 [0.510, 0.554] on all G5 rows, 0.504 against 0.500 settled. **Proposal for Gate 2's
    pre-registration**: measure "half the gap to the oracle" against the better of the two on
    the gate's own validation rows; recommended default, the chord oracle with the speed prior
    (better or equal on noisy data).
11. **SRD wording: noise-free recovery tested least squares, not the layer** (geometry). *Fixed*:
    the check runs the layer with trivial inputs (2.4e-6 over 160 scenarios) and reports least
    squares beside it.

### Minors (all done unless stated)

- Reference tolerance: p99 reported; worst rows traced to a stopping knife-edge (6 against 5
  iterations). The at-scale check covers regressions the fixtures cannot.
- Masking and gradient claims in the note corrected; gradient test now at the spec's 1e-4.
- Covariance: an independent σ²(JᵀJ)⁻¹ test added; reference docstring σ² wording fixed.
- Float32 conclusion: stated as conditioning (JᵀJ squares the condition number); f32 numbers
  now recorded in `metrics.json` (`export`).
- Export at the production knots (8) and damping trials with the speed-skip path, but 8 unrolled
  iterations, not the production 100: unrolled, 100 gave a 45 MB graph onnxruntime could not
  load in 12 minutes; the row-by-row Gauss–Jordan was replaced by a whole-matrix form (37k → 11k
  nodes). A deployable model needs an ONNX `Loop` (spec 003). The oracle's exact inputs are not
  exported (the toy encoder supplies them). *(Corrected in round 2: the round-1 text said 100.)*
- Pre-zig rows are "plausible" with sd ≫ range: recorded in AGENTS.md for spec 003 (training
  must exclude or down-weight undetermined rows). Implicit-function backward: proposed for spec
  003.
- Pass rule for reproducing the note: kept (pre-registered); limits recorded (≈5% false-fail per
  check if identical, the tolerance set by the 2,400-scenario sample). Future reproductions
  should run both implementations on the same rows with an equivalence margin.
- Estimand differences from note 05 (drops vs +∞, interpolated vs nearest-rank, settled-row
  clustering) documented; the gap on seed 301 is below 0.002.
- Bootstrap equal to gitma's: committed fixture from gitma's `bootstrap.js` (ties, ∞, NaN,
  uneven clusters), all equal; a zero median now gives ∞ as in JavaScript instead of raising.
- `threshold_low` recorded for interval checks; detail strings no longer hard-code counts.
- Known-answer frame tests (bearing convention, turn direction, truth displacement).
- `test_single_leg_is_singular` asserts `singular`.
- Speed-prior semantics vs note 05 (`min(end, k)`) and knot-timing conventions documented in
  `segmentation.py`.
- Manifest: package versions, uv.lock digest, CPU, thread counts; git run from the repository.
- Slice keys at band edges: a fixture from gitma's own `sliceKeys` on 176 metadata records at,
  just below and just above every range, zig, σ, dropout and manoeuvre edge (double and
  float32); all equal.


## Run r2 (2026-11-01): `experiments/20261101-p0-r2/`, commit 8e5dfe1, clean tree and clean data

Machine verdict **fail**, 21 of 22 checks pass:

| Check | Result |
| --- | --- |
| Generator, 3 fixtures | 24 of 24 files byte-identical |
| References, 6 | flags identical; worst 1.6e-5 |
| Physics equals least squares | **fail**: 22,531 rows; flags differ on 0; cost higher on 0; worst 1.3e-4 relative on range-determined rows (limit 1e-4); 3.3e-4 standard deviations on all (limit 1e-2) |
| Noise-free recovery (layer) | 2.4e-6 over 160 scenarios |
| Least-squares speed efficiency | 0.949 on 1,313 held-course rows (range 1.007, course 0.988) |
| Oracle, 4 range ratios | 0.531, 0.500, 0.638, 0.575: inside the note's intervals |
| IMM at scale | 1,214,916 rows, 0 flag mismatches, 475 rows (0.04%) beyond 1e-4, G5 median ratio 1.000000 |
| Export, Python / WASM / Java | 7.2e-12 / 1.1e-11 / 7.2e-12 in double, one export digest |

**Diagnosis of the failure.** One row exceeds the limit (row 225, 1.29e-4; row 226 is 7.2e-5,
corrected in round 2), in speed, on scenario 1 of the phase-4 train fixture. Their range is determined (sd 0.31–0.33 of range), so the
rule applies the relative test, but their speed is not: its standard deviation is 5.8–9.4 times
the speed. Polishing each with 3,000 iterations, from gitma's own solution and from the grid,
lands where the layer already is; gitma's solver had stopped short (its stop is a relative cost
decrease below 1e-12):

| Row | Speed, gitma's solver | Layer (100 iterations) | Polished from gitma's solution | Cost (all three) |
| --- | --- | --- | --- | --- |
| 225 | 6.870677 | 6.871561 | 6.871539 | 0.2732685527 |
| 226 | 11.123961 | 11.124763 | 11.124761 | 0.2733695460 |

So the rule, written before this run, measures gitma's stopping error on rows whose speed is
undetermined. It is not changed here: changing a gate's criterion after a result exists is the
owner's decision (AGENTS.md). **Open question to the owner** (asked separately, recommended
option first): apply the 1e-4 relative test to each quantity only where that quantity is
determined (its sd below half its value), keeping the standard-deviation test on all rows; or
compare against a polished optimum instead of gitma's stopping point; or keep the rule and
record P0 as failed on this check.

## Round 2 (2026-11-01): record r2 at 8e5dfe1, diff 5adb8bf..06733db

| Reviewer | Verdict |
| --- | --- |
| TMA geometry | approve-with-findings |
| Estimation and numerics | approve-with-findings (2 majors) |
| Evaluation statistics | approve-with-findings (2 majors) |
| Reproducibility | approve-with-findings (2 majors; every re-run value bit for bit) |
| Red team | approve-with-findings (2 majors) |

No reviewer rejects. Every verdict assumes the owner accepts the recommended option for the
physics-vs-least-squares rule. All five confirmed the r2 diagnosis independently (two with
their own optimisers: speed 6.871542 / 6.871534 at row 225 against the layer's 6.871561 and
gitma's 6.870677; one Gauss–Newton step from gitma's point still moves speed by 1.9e-3). The red
team showed the recommended rule is not tuned to pass: with speed counted as determined at
sd/speed below anything from 0.05 to 5, the worst speed difference is 6.4e-6 to 2.1e-5, a 5–15×
margin, and the cost test rules out a layer that stopped short. The numerics reviewer showed the
miss is predictable: relative error ≈ (sd/value)·√Δχ², with √Δχ² ≈ 2e-5.

### Majors and responses (fixed at 8116827 and 463f8f8)

1. **Covariance non-finite on "plausible" rows, silently skipped** (numerics). Where both solvers
   collapse onto ownship (range 1e-7–4e-6 m) unpivoted elimination gave NaN. *Fixed*: a relative
   ridge of 1e-12 on the covariance's information (scaled condition near 1e12), in the layer and
   the reference; a `cov_ok` output (finite, positive diagonal, range > 1 m); the check counts
   degenerate and non-finite rows and fails on any non-finite one; a gradient test with losses on
   the state, cost and log covariance with random learned inputs on pre-zig, at-zig, mid and last
   rows including the collapse rows. The reviewer's probes now give 0 non-finite covariances.
2. **Training throughput not measured** (numerics). *Fixed* (reported, not gated):
   single-threaded forward + backward at 100 iterations is 0.18 s and 72 MB per row; 256 rows
   would take about 45 s and 18 GB against the planned 1 s. **Consequence for spec 003**: the
   backward pass must not unroll 100 iterations: an implicit-function backward at the optimum
   (one solve) or a truncated backward, with threads pinned; spec 003's first decision record
   should state which and measure it.
3. **A gate could pass with checks missing** (statistics, reproducibility, red team). *Fixed*:
   `--oracle-data`, `--gitma-data` and `--gitma-imm` are required; the CI job builds gitma's
   reference itself (`scripts/gitma_reference.sh`, gitma checked out at d0aec60).
4. **SRD Gate 1's efficiency criterion points the wrong way** (statistics: "efficiency ≥ 0.8"
   with error/CRB passes every inefficient model). *Answered*: an SRD amendment, the owner's;
   proposed in the PR for spec 003's pre-registration: efficiency (error/CRB, 1 at the bound)
   ≤ 1.25 on settled slices.
5. **Dirty runs could write the clean commit's cache** (reproducibility, red team). *Fixed*: a
   dirty tree writes to a fresh `<commit>-dirty-*` directory no run reuses.
6. **gitma's IMM file not bound to the data, no provenance** (reproducibility, red team). *Fixed*:
   the check verifies gitma's file names gitma's dataset (`check_bound`) and that the dataset's
   10,000 scenarios equal ours block for block (headers differ only in the generating code);
   gitma's commit and commands are in `scripts/gitma_reference.sh` and the record; the header is
   copied into the record.
7. **Owner approval of the round-1 amendment** (red team). *Accepted*: both the round-1 spec
   amendment and the r2 rule go to the owner in one question; no P0 pass is recorded until the
   owner answers.

### Minors (done unless stated)

- `spd_solve` docstring: agreement is about eps × cond, not "≈1e-17".
- `_hypot` branch-safe; a learned log-weight must be bounded (documented).
- Unconverged solver rows: the layer's flag and cost are now reported.
- Manifest records the oracle's actual iterations and trials; artefact and dataset paths are
  relative; the conformance results are copied into the record.
- Noise-free check pinned to double (explicit dtype in the layer inputs) with a test.
- `known_manoeuvres` refuses data with manoeuvres but no plan; kinematics tested against the
  stored truth of every phase-4 fixture scenario (worst under 1 cm); the Monte-Carlo docstring
  no longer claims a test that did not exist.
- Frame tests pin ownship's course convention and use the median residual over all bearings.
- Fixtures: slice cases just beyond gitma's snap windows (230 cases); a gitma bootstrap case
  with a zero-median denominator.
- Oracle and IMM efficiency against the known-manoeuvres bound reported in P0 (geometry
  measured 1.13 range, 1.15 course, 1.16 speed for the chord oracle with the speed prior).
- Efficiency check: scenario-clustered 95% interval [0.89, 1.04] and excluded rows (275 beyond
  the window, none singular) recorded.
- IMM at scale: rows either side lacks count as mismatches; p99 and p99.9 reported; the 0.1%
  limit is labelled post hoc.
- Naive model validated against `NaiveModel`. Not done: the experiment `metrics.json` is a
  diagnostic dictionary, as in gitma; typing it is proposed for spec 003's record format.
- Gate 2 proposal revised (geometry, statistics): pre-register the chord oracle with the speed
  prior now (better on range, the gated metric; masking is mixed: course 0.461 against 0.438,
  speed 0.380 against 0.393), and report its efficiency against the known-manoeuvres bound.
- For spec 003: a knot at `start_index − 1` (geometry); a `Loop` export with 1e-5 conformance as
  an entry criterion (numerics); the jitter null for the at-scale check (statistics).

### The owner's decision (2026-11-01, after run r2)

Asked in one question, recommended option first, with the alternatives (a polished reference;
keep the r2 rule and record P0 as failed; revert to the original wording). **The owner chose the
recommended option**: the round-1 spec amendment is accepted, and the relative test applies to
range and speed separately, each only where that quantity is determined (sd below half its
value), with the standard-deviation test on every row. Run r2's fail stays in its record
unchanged; run r3 (`experiments/20261101-p0-r3/`) is judged under the amended rule.
