# Gate 1 (spec 003): agent review panel

Gate: SRD §5 Gate 1 on constant-velocity data, as pre-registered in
`experiments/20261101-g1-decision/decision.json` (committed 7fc39d5 before training) and amended by
`amendment-1.md` (owner, 2026-11-01). Evidence: plan `configs/gate1/plan.json`; models
`experiments/20261101-g1-a-models/` (run 41319578497); validation report
`experiments/20261101-g1-a-val/` (run 41356702873); test record `experiments/20261101-g1-a-g1/`
(run 41357789247, seed 303, generated once); report `experiments/20261101-g1-a-g1/report/`
(re-uses the gate run's test predictions; the test split is not scored again).

Machine verdict: **pass** on all seven checks (ratios 0.999 / 0.997 / 1.000 to batch least
squares with intervals wholly below 1.1; gross 1.19% against 1.27%, difference interval
[−0.16, −0.02] points; efficiency 0.99 / 0.96 / 0.96, upper bounds ≤ 1.03).

## Round 1 (2026-11-01)

Five independent reviewers, read-only, each given the evidence and not the author's reading of it.

| Reviewer | Verdict | Blockers | Majors | Minors |
| --- | --- | --- | --- | --- |
| TMA geometry | approve-with-findings | 0 | 1 | 5 |
| Estimation and numerics | approve-with-findings | 0 | 2 | 6 |
| Evaluation statistics | approve-with-findings | 0 | 3 | 3 |
| Reproducibility | approve-with-findings | 0 | 0 | 5 |
| Red team | approve-with-findings | 0 | 3 | 3 |

### What every reviewer found (major, all five or four of five)

**The carried model is the untrained physics layer.** Its heads collapsed to constants: 0 of 64
hidden ReLU units active in each head of `g1-physics-s2` on validation (s1, s3 and time-late
almost the same; an untrained seed has 51–61 of 64 alive); the per-bearing log-weight is −0.0089
everywhere (sd 5e-18); the start correction and covariance scale equal the final biases. Against
the same model with zeroed heads the estimate differs by a median 3.5e-11 relative (p99 7e-8).
On test, the model's gate-row medians and gross rate equal the trivial-input physics layer's
("oracle" row: on constant-velocity data there are no manoeuvres, so it is the untrained layer)
to every digit. An untrained model would pass Gate 1 with the same numbers. Validation losses are
flat from epoch 1 (3.27180 → 3.27128). — numerics, red team, statistics, geometry.

**The gross check's margin is the solver's, not learning's.** 58 model rows against 62 least
squares rows (4 discordant rows, 0 the other way; exact one-sided sign test p = 0.0625); the
untrained layer has the same 58. The difference comes from the layer's cold-start, multi-damping
solve against `tma2-solve --per-timestep`'s warm-started rows, and from the definitions (the
model's "converged" is plausibility only; least squares' also needs LM convergence). The forecast's
mechanism ("the learned start avoids wrong minima") is not supported. — all four of numerics, red
team, statistics, geometry; numerics asked for a breakdown by cause.

**Amendment 1 turned a validation stop into a proceed.** Under the registered rule (shuffled ≥
0.8 × naive = 32.5%) the shuffled control (3.71%) fails; the losses seen when the amendment was
made already implied it. Legitimate (owner-authorised, before the validation report, the
registered check invalid by construction for a physics-layer model, decision.json untouched), but
it must be disclosed plainly, and the replacement check is weak (almost any model routed through
the layer passes it). — red team (major), statistics (minor).

**Missing constitution IV reporting** (statistics, major): 90th percentiles, slices (range band, zig
angle, σ, time since zig), curves at every post-zig timestep, efficiency per slice.

### Minor findings

- Geometry: zig + 5 min falls inside the second ownship turn for 65% of rows (not comparable with
  gitma's single-zig numbers); speed is in knots, mislabelled m/s in the validation report and the
  forecast; time-late efficiency is against the causal bound; no oracle row in the validation
  report; efficiency is median-based and cannot tell estimators apart near the bound; two median
  conventions in one record.
- Numerics: the Newton step and the 50-iteration training solve are sound and prediction uses
  K = 100; the comment at layer.py:394 still says Gauss–Newton; calibration is one global scalar;
  no numerical exclusion biases the gate rows; time-late beats causal only by seeing the whole
  window; no ONNX export of the carried weights in the evidence; tasks.md misstates s2's change.
- Statistics: checks implement the registration exactly (intersection–union, no multiplicity
  adjustment needed; paired, scenario-clustered, 0.95, 2,000 resamples); carried rule applied as
  registered (s2 and s3 tie, the tie goes to the lower seed); amendment wording ("no validation
  metric existed") inaccurate; amendment not digest-bound; the direct control is under-trained, not
  evidence that direct regression is 7–12 × worse; median efficiency below 1 reflects heavy tails.
- Reproducibility: test split (8d9346fe…), ancestry, plan digest, committed folders and four of six
  prediction files (least squares, naive, EKF, IMM) reproduced byte for byte; a 384-scenario
  re-score of the carried model matches least squares on every gate row; weights not bound by
  digest; model predictions only a 90-day artefact; `git_dirty` absent from job records; amendment
  not in the manifest; checkpoint branches reported as still present.
- Red team: no truth reaches the inputs (features, rows, grid start on samples ≤ k; truth only in
  the loss and scoring); seed 303 generated once, one results branch; time-late passes by
  construction; the speed ratio interval is an identity, not a margin; add a relative minimum
  improvement to early stopping.

### Response (author, round 1)

1. **What Gate 1 shows** — accepted in full. The verdict and every write-up state: *on
   constant-velocity data the end-to-end model passes Gate 1 because it reduces to batch least
   squares through the physics layer; training left the heads input-independent. Gate 1 shows that
   end-to-end training through the declared layer is stable and does not degrade least squares at
   the bound; it does not show that the learned component adds anything, which is untested until
   Gate 2.* The forecast's mechanism is recorded as wrong; the CV "oracle" row is reported as
   "physics layer, trivial inputs (= untrained model)", not as a ceiling.
2. **Gross check** — the report (`report/diagnostics.json`) gives the discordant counts, the exact
   sign test and the gross rows split by cause for the model, least squares and the untrained layer
   (numbers below once the report lands). The check is reported as met under the registered rule
   and attributed to the solver and the convergence definitions.
3. **Amendment disclosure** — `amendment-1.md` now states that the registered rule would have
   stopped the phase at validation (3.71% against a 32.5% floor), that the per-epoch losses seen
   were validation metrics, and its commit times. Its digest is bound below. The forecast's
   "shuffled at naive level" is recorded as wrong.
4. **Reporting** — `report/eval/` holds tma2-eval on the gate run's own test predictions (medians,
   90th percentiles, gross rates, slices, curves, efficiency per slice against the full-window
   bound), for the model, least squares, naive, EKF, IMM and the trivial-input layer; the test
   split's digest is re-checked and nothing is re-scored. `report/gate-rows/` keeps every
   estimator's gate rows in the repository.
5. **Minor findings** — fixed: speed labelled in knots and a time-late efficiency caveat in the
   validation report (script; the committed report is left as generated); oracle added to the
   validation workflow for future gates (on test the oracle row is reported); the layer comment;
   tasks.md's s2 wording. Recorded as follow-ups before Gate 2 (specs/003-gate1-cv/tasks.md):
   dead heads (no warm start from these weights, an activation that cannot die, an alive-unit test,
   a learnability check), weight digests, `git_dirty`, amendments in manifests, export of the
   carried weights, one median convention, gross rows by cause, minimum improvement in early
   stopping. The checkpoint branches were deleted by the results job (`git ls-remote` shows none);
   the reviewer saw a stale local ref. The second-zig overlap and the median-efficiency caveat go
   into the write-up.

Amendment binding: `amendment-1.md` sha256 recorded with the round-2 commit.
