# G0-MAN2 agent review panel

**Decided: pass, panel round 2, on record r2** (`experiments/20261104-g0-man2-r2/`, commit
31ea6cf, 17 of 17 checks).

Pipeline gate on generator 0.6.0 (spec 006 FR-051, SC-001–SC-005), checks pre-registered in
`specs/006-generator-man2/g0-checks.md`. Records:

| Run | Folder | Commit | Machine verdict | Status |
| --- | --- | --- | --- | --- |
| first run | not written (the write failed: verdict schema has no gate `G0-MAN2`) | 29e3a21 | — | check 4 failed its ≤ 20% skip limit; generator conformance and throughput also failed (the faults below) |
| r0 | `experiments/20261104-g0-man2/` | 64a2d6f | fail (4 checks) | superseded; README gives the causes |
| r1 | `experiments/20261104-g0-man2-r1/` | 42d6a8b | pass, 15 of 15 checks | reviewed in round 1 |
| r2 | `experiments/20261104-g0-man2-r2/` | 31ea6cf | pass, 17 of 17 checks | after the round-1 fixes; reviewed in round 2 |

The r1 commit message said "20 of 20 checks"; the record holds 15 check rows (the seven
pre-registered checks expand to 15). Corrected here.

## Before the panel: owner decisions on criteria with results

1. **Check 4 coverage** (owner, after the first run): "at most 20% skipped" replaced by "at least
   500 of 1,000 fitted". The first run's output was not written to disk (the verdict write
   failed); its check-4 line, from the session log: *fail: zig leg alone, 583 of 1000 scenarios
   (417 skipped, 41.7%): least squares 9.27e-06, physics layer 9.22e-06*. Skip breakdown: zig
   inside a target change 12.6%, zig leg ends within 30 rows of the zig 21.2%, under 12 rows
   before the turn 7.7%, both 0.2%; seed 314: 14.2 / 17.9 / 7.2 / 0.3%. The owner was told, in
   the question, of that breakdown and of the accuracy result; the generator-conformance and
   throughput failures of that run were found afterwards and were not in view.
2. **Throughput method** (owner, after r0 and r1, round 1 red team): `generate_indices` on four
   threads, timed with nothing else running; the one-thread loop reported.

Both amendments are in `g0-checks.md` with dates. The owner's choices were given in this session
in answer to multiple-choice questions; verbatim, the options the owner chose were:

1. *"Amend coverage (Recommended): Replace '≤ 20% skipped' with 'at least 500 of 1,000 scenarios
   fitted'; the 1e-3 accuracy limit is unchanged. Record it in g0-checks.md as an owner amendment
   made after the result, with the skip breakdown. The panel then reviews G0-MAN2 on that basis."*
2. *"generate_indices, 4 threads (Recommended): Gate on the training path, the one that matters
   on 4-core runners, re-timed with nothing else running. The one-thread loop is reported beside
   it. Recorded as your amendment after the result, like check 4."*

**The first run's check-4 line**, verbatim from the session log (2026-11-04T13:02:32Z, an
in-process run of `check_distributions` and `check_noise_free_zig_leg` at commit 0900c43 plus the
uncommitted CLI, before 29e3a21): `fail noise-free-zig-leg zig leg alone, 583 of 1000 scenarios
(417 skipped, 41.7%): worst relative range error at the leg's last row: least squares 9.27e-06,
physics layer 9.22e-06`. The five distribution checks passed in the same run with the values r2
records.

**Dry run of checks 8 and 9.** After registering them (bf4eaeb) and before r2, both were run once
in-process at 4d0d74d (NIS 1.018, efficiency 1.010, the values r2 records). Between bf4eaeb and
31ea6cf their code did not change and their text changed only in the IMM name's spelling, so the
dry run moved nothing (statistics and red-team reviewers checked the diff).

## Round 1 (4 November 2026): record r1 at 42d6a8b

Five read-only reviewers in parallel. A tuning job held three of the four cores; reviewers were
told not to time anything.

| Reviewer | Verdict |
| --- | --- |
| TMA geometry | approve-with-findings |
| Estimation and numerics | approve-with-findings |
| Evaluation statistics | approve-with-findings |
| Reproducibility | approve-with-findings (checks 1–6 re-run, every value bit-identical) |
| Red team | **reject** |

### Majors and responses

1. **The 720-row export batch was 2 short scenarios** (geometry, numerics, red team). Only zig
   legs starting at row 0 qualified: 2 of 64 fixture scenarios, k = 239 and 163, so every row
   past 240 was padding. *Fixed* (3051f7c): bearings before the zig leg's first row are marked
   invalid, so any zig leg can be used, and only legs ending at row 480 or later are taken (from
   400 fixture scenarios). Batch of 8, k 480–549, valid rows 204–370; double: Python 3.1e-10,
   WASM 2.3e-10, Java 3.1e-10 (covariance). The golden k and valid-row counts are recorded.
2. **Browser and Java results were bound to the model digest only** (red team). The toy model's
   ONNX does not change with the golden batch (bc44c90b… before and after the fix), so a stale
   results file would have been accepted. *Fixed* (3051f7c): both legs record a SHA-256 of the
   golden inputs (`in_*.bin` in name order) and the gate requires it to match its own export.
3. **The manifest bound no datasets** (reproducibility, red team). *Fixed* (3051f7c): the three
   splits are recorded with digest and header.
4. **Throughput method changed after a fail** (statistics, red team). *Answered*: owner decision
   2 above. r2 times throughput and layer cost with the tuning job paused (SIGSTOP, resumed after
   four minutes), and reports the one-thread loop beside it.
5. **FR-051's tracker NIS and P0's efficiency checks were missing** (red team). *Fixed*
   (bf4eaeb): both restated on the zig leg and pre-registered before their first run (checks 8
   and 9 of `g0-checks.md`); P0's references, oracle and IMM-at-scale recorded as not applicable
   to MAN2 with reasons. `imm_predict`'s `nis_out` now has one value per row, as `ekf_predict`'s
   (test added; estimates unchanged).

### Minors and responses

- **Check 4's tolerance has little power against a one-row convention error** (geometry): a
  shift of one row into a turn gives 1.6e-3 on 1% of scenarios; it fails only through the worst
  case. Reported; the limit is unchanged (changing it now would be a criterion change). The
  geometry reviewer's independent check that all 3,868 noise-free target legs between spans are
  exactly constant velocity (4 mm) is quoted here as evidence.
- **Check 3d cannot fail unless the clip breaks; 3e counts header kinds** (geometry, red team).
  r2 reports realised wander per kind (largest deviation per straight segment), so missing wander
  would show. The red team's probes (none 0°, wander 2.7–4.0°, oscillation 1.0–3.0°) agree.
- **Check 5 tests mostly mis-specified fits** (geometry, numerics): 98% of its rows fit one
  constant-velocity leg over a prefix that contains target changes. It is a solver-equality check,
  as P0's was, and harder than P0's (25% both implausible, no flag mismatches, no row where the
  layer stopped higher). Stated here; the knot path at 720 rows is untested and is noted for
  spec 005 (Gate S's coupled cost needs it).
- **Native onnxruntime differs from torch by 1e-8 on a well-conditioned row while WASM agrees to
  1e-15** (numerics, r1 batch). In r2's batch the three runtimes agree to 2–3e-10. Recorded.
- **SC-002's in-window clauses** (statistics): spec amended to the planned law (4d0d74d); the
  in-window share (7.0%) agrees with the window-conditioned expectation the statistics reviewer
  computed by Monte Carlo (about 6.8%).
- **±2 pp share tolerances are loose** (statistics): a multinomial χ² gives p = 0.62 (kinds) and
  0.39 (wander); reported, not gated.
- **`zig_leg` raised on a null turn start; docstring said a−1** (geometry): fixed (4d0d74d).
- **Seed 315 is reserved but tasks say it is generated** (reproducibility): tasks.md says it is
  generated when Gate S's decision record is committed.
- **The frozen 0.5.0 IMM on seed 314 G5 rows** (reproducibility, red team) was promised as a
  reported item and is not in the gate record: it comes from the re-tune (T032,
  `experiments/20261104-man2-tune/grid.csv`, which includes that setting); NIS on settled rows is
  replaced by check 8.

## Round 2 (4 November 2026): record r2 at 31ea6cf

The same five reviewers, given review.md's round-1 section and the r2 record. A tuning job ran on
three cores; nobody timed anything; r2's own timed checks ran with that job paused.

| Reviewer | Verdict |
| --- | --- |
| TMA geometry | approve |
| Estimation and numerics | approve |
| Evaluation statistics | approve |
| Reproducibility | approve (manifest digests, code, export model and inputs digests, Python and WASM legs, checks 8 and 9 re-run: all identical) |
| Red team | approve-with-findings (no blocker or major open) |

### Minors raised in round 2 and responses

- **Owner consent attested only by the agent** (statistics, red team): the chosen options are
  quoted verbatim above and in the PR.
- **The ~6.8% window-conditioned expectation came from an uncommitted script** (red team):
  committed as `scripts/research/man2_window_bias.py` (output: 6.8–6.9% with row rounding, 6.4%
  continuous; P5/P50/P95 8.9/23.5/38.2 min; 93.7% with two or more changes).
- **The first run's record and the dry run** (red team, statistics): quoted above with timestamp
  and commit.
- **`zig_leg`'s end row against check 5's wording** (statistics): `zig_leg` ends a leg at
  `start_index − 2` (one row conservative); check 5 scores every tenth row up to the same row
  (`rows_of` in `g0_man2.py` uses `a − 2`), so "the row before the first target change" in
  `g0-checks.md` means that row. No behaviour differs.
- **The Python entry in the 720-row results has no inputs digest** (reproducibility): the Python
  leg runs inside the gate on the gate's own export, so it is bound by construction.
- **The float32 export now differs from torch by about 6e-2 on the covariance** (r1's batch:
  2e-4) (reproducibility): the masked, late legs extrapolate the state to t = 0 over up to
  5,500 s, which float32 cannot hold; float32 is reported, never the conformance artefact
  (AGENTS gotcha), and Gate S's models run in double.
- **Carried to spec 005** (numerics, red team): the physics layer's knot path at 720 rows is not
  checked for conformance or equivalence; check 4 has little power against a one-row convention
  error; check 5 tests mis-specified fits.
- **Checks 3d/3e cannot fail on missing wander** (red team): mitigated by the reported realised
  wander per kind (none 0°, wander 4.0°, oscillation 3.0°), not gated.

**Decision**: no reviewer rejects and no blocker or major finding is open. G0-MAN2 **passes**;
`verdict.json`'s `decided_by` names this round. Training on MAN2 data may proceed (FR-051).
