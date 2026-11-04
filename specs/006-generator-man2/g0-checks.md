# Pipeline gate on generator 0.6.0 (G0-MAN2): checks fixed before the run

Spec 006 FR-051, SC-001 to SC-005. Written on 4 November 2026, before `tma2-g0-man2` was first
run. The thresholds come from the spec's success criteria (written before any MAN2 data existed)
and from P0's existing checks; a 2,000-scenario exploratory sample of seed 314's *train* indices
was measured while the generator was reviewed (PR 13), and is not the gate's data.

**Data** (generated from the clean tree at `d72cb81`, the merge of PR 13):
- seed 314, `configs/man2-ranges.json`, `--count 100000`: validation = indices 80,000–89,999
  (10,000 scenarios), the gate's MAN2 split; train deleted after its digest was recorded;
- seed 316, `configs/man2-noise-free.json`, `--count 10000`: validation (1,000 scenarios) for the
  noise-free checks;
- seed 304's committed validation split (`data/gd-val`, generator 0.5.0) for the regeneration
  check.

**Verdict**: pass when every gated check passes, decided by the agent review panel (constitution
V); fail or inconclusive otherwise. Exit 3 from the CLI when any gated check fails.

## Gated checks

| # | Check | Pass when |
| --- | --- | --- |
| 1 | `generator-conformance` | gitma's fixtures regenerate with gitma's digests (P0's check, unchanged) |
| 2 | `regen-0.5.0` | all 10,000 scenarios of seed 304's validation split regenerate identically under 0.6.0 (each encoded block equal) |
| 3a | `man2-transitions` | the median planned duration of target changes seen whole in the window is in [60, 180] s (SC-002) |
| 3b | `man2-changes` | at least 60% of engagements have two or more target changes (SC-002) |
| 3c | `man2-kinds` | course / speed / both shares each within 2 percentage points of 0.8 / 0.1 / 0.1 |
| 3d | `man2-wander-band` | on every ownship row away from a planned turn (the row and its neighbours on a straight planned course), the recorded course is within 5° of the planned leg course (SC-003) |
| 3e | `man2-wander-kinds` | none / wander / oscillation shares each within 2 percentage points of 0.4 / 0.3 / 0.3 |
| 4 | `noise-free-zig-leg` | on seed 316's noise-free validation split: for each scenario, the steady target leg that contains the ownship zig, fitted alone (its rows only), by batch least squares (final mode) and by the physics layer with trivial inputs, gives range at the leg's last row within 1e-3 relative of truth; scenarios whose leg has fewer than 12 rows before the ownship's turn or fewer than 30 after the zig are skipped and counted; pass needs the worst error below 1e-3 for both and ~~at most 20% skipped~~ at least 500 scenarios fitted (owner amendment, below). This is research R3's restatement of gitma's `beforeManoeuvre` for data whose first change can precede the zig |
| 5 | `physics-equals-ls-720` | P0's physics-equals-least-squares check on 720-row windows: 200 σ = 1° MAN2 validation scenarios, every 10th row from zig + 1 up to the row before the first target change after the zig; same tolerances as P0 |
| 6 | `export-720` | the toy export at 720 rows (golden batch from seed 316) agrees with torch within 1e-5 in the Python and browser (WASM) legs, in double; Java as P0 (may be deferred, then skipped) |
| 8 | `tracker-nis` | added 4 November 2026 after panel round 1 (FR-051 and research R6 name it; it was missing), before its first run: gitma's phase-4 `tracker-nis` restated on the zig leg. The straight-leg IMM (`imm-cv0-ct0.01-w0.001-s1e-05`, gitma's `G0_IMM_STRAIGHT`, r scale 1, p0 scale 1) through `imm_predict` on the zig leg alone of the first 200 σ = 1° seed-314 validation scenarios that have one; each scenario's mean NIS over rows from zig + 60 s to the leg's last row; pass when the median over scenarios is in [0.75, 1.3] (gitma's band) |
| 9 | `least-squares-efficiency-speed` | added with check 8, before its first run: P0's efficiency check restated on the zig leg. Batch least squares (final mode) on the zig leg alone of the first 2,000 σ = 1° seed-314 validation scenarios that have one, at the leg's last row, against the full-window Cramér–Rao bound at truth on the same rows (the leg is constant velocity); pass when the speed efficiency, median(\|e\|/σ)/0.6745, is in [0.8, 1.3] (P0's band); range and course reported |
| 7 | `throughput` | the kernel generates at least 10,000 MAN2 scenarios per second (SC-004); measured: 30,000 |

**Not restated for MAN2** (FR-051 and R6 listed P0's whole set): P0's `references` (gitma's
prediction fixtures exist only for 0.5.0 data, and the reference code is unchanged; `tma2-p0`
still runs them), `oracle` (its pass intervals come from the phase-4 research note; Gate S's spec
sets MAN2's oracle comparison) and `imm-at-scale` (a comparison with gitma's IMM on gitma's data;
gitma has no 0.6.0). These were left out when the table was first written without saying so
(panel round 1, red team).

## Amendment (owner, 4 November 2026, after the first result)

Check 4's coverage limit was set before any MAN2 data existed. The first run (commit `29e3a21`,
before the gate's record was written) skipped 417 of 1,000 noise-free scenarios: 126 (12.6%) where
the zig overlaps a target change, 212 (21.2%) where the zig leg ends within 30 rows of the zig, 77
(7.7%) with under 12 rows before the turn, 2 with both. Seed 314's validation split gives the same
shares (14.2%, 17.9%, 7.2%, 0.3%; 39.7% in all). With legs of N(25, 9.1) min and about 8 min of
the zig leg required, a skip share near 40% follows from the leg model, so the 20% limit tested the
owner's simulation, not the pipeline. Accuracy on the fitted scenarios was 9.3e-6 (least squares)
and 9.2e-6 (physics layer) against 1e-3. The owner chose to replace "at most 20% skipped" with "at
least 500 of 1,000 scenarios fitted"; the accuracy limit is unchanged and the skip share is
reported. Recorded here and in `src/tma2/cli/g0_man2.py` (`ZIG_LEG_FITTED_MIN`).

## Reported, not gated

- complete target legs inside the window: 5th / 50th / 95th percentiles and share at or under
  10 min (biased towards short legs by the window; the planned law is unit-tested in a long
  window, `tests/unit/test_man2_generator.py`);
- zig overlapping a target change: count;
- the physics layer's cost per solve at 360 and 720 rows (measured 20.8 and 25.7 ms, batch 64,
  four threads);
- the current frozen IMM (`imm-cv0.0003-ct0.03-w0.003-s0.001-p4-r16`, tuned on 0.5.0) on seed 314's
  σ = 1° G5 rows: median range error and mean NIS on settled rows, as the starting point for the
  re-tune (T032), which is a separate experiment.
