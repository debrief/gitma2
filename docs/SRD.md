# SRD: gitma2, TMA via ML, second attempt

Draft 2026-10-31 · owner Ian Mayo · status: proposed, awaiting the owner's acceptance

gitma2 inherits the problem, data conventions and measurement discipline of
[debrief/Gitma](https://github.com/debrief/Gitma) (its `docs/SRD.md` with Annexes A–C, referred to
below as *the gitma SRD*). Where this document is silent, the gitma SRD applies. Where they
differ, this document wins and the difference is stated.

## 1. Purpose and scope

gitma answered its question: a recurrent regressor trained on simulated bearings extracts usable
range, course and speed, is more robust than least squares near unobservability, and beats a
tuned IMM after a target turn, but it stays about 3 × the Cramér–Rao bound on straight legs and
gives back its post-turn gains when the target holds course (`docs/research/01`). gitma2 asks the
sharper question:

> Can a learned component, trained end to end with explicit bearing geometry, be at least as
> accurate as batch least squares wherever the constant-velocity model holds, and better than a
> tuned IMM wherever it does not, with calibrated uncertainty, from a single exportable model?

**In scope**

- A Python toolchain: vectorised generator reproducing gitma's generator 0.3.0 and 0.5.0,
  reference estimators (naive, batch least squares, EKF, IMM, Cramér–Rao bound), a **declared
  physics layer** (piecewise-constant-velocity batch solve) with learned inputs, training on
  GitHub-hosted CPU runners, scoring, gates.
- Staged gates (§5) with pre-registered decision records, fresh test seeds and the agent review
  panel.
- A steady-leg (manoeuvre) detector as its own annex ([Annex A](SRD-annex-A.md)): the first
  learned component, gated on its own and on the estimate it enables.
- Export of every carried model to a portable artefact (ONNX plus weights and manifest) with
  cross-runtime conformance; a browser viewer on that artefact.

**Out of scope** (as gitma §1): multi-target, clutter, association, sensor artefacts beyond
Gaussian noise and dropouts, real or classified data, runtime performance tuning. Realistic
bearing error (correlated, slowly biased) is deferred until Gate 2 is passed.

## 2. Problem definition

As the gitma SRD §2 and Annex C §C.2: one ownship with exactly known track, noisy bearings to a
single target, ownship zigs for observability, flat-earth Cartesian frame, x east, y north,
metres, bearings true clockwise from north in radians, speeds m/s (knots for reporting).

Two problem variants are used, in this order:

| Variant | Generator semantics | Used for |
| --- | --- | --- |
| **CV** | gitma 0.3.0: constant-velocity target, three ownship legs (`zig_rule: across_los`), σ ∈ {1°, 2°}, 0–10% dropouts, 10–40 min windows | pipeline gate, Gate 1 |
| **MAN** | gitma 0.5.0: 0–3 target course changes (P = 0.2, 0.3, 0.3, 0.2), one speed change in 30%, 20–60 min windows, phase-4 ranges | Annex A detector gate, Gate 2 |
| **MAN2** | gitma2 0.6.0 (owner, 2026-11-04; Annex B): target legs of 10–40 min with a bell-shaped length distribution (5% at 10 min), transitions of about a minute, helm wander and autopilot oscillation, target changes allowed during ownship turns, 40–120 min windows (720 rows); 0.5.0 ranges reproduce 0.5.0 byte for byte | Gate S (spec 005), Gate 2 |

Both consumers (instantaneous, causal; time-late, full window) remain, scored as gitma does: the
instantaneous model at every timestep after the zig as a curve against time since zig, gates at
fixed points.

## 3. Data requirements

As the gitma SRD §3 with these changes:

- **Generation is vectorised and on the fly.** The generator is a pure function from (seed, index
  range, ranges) to arrays; training may draw fresh scenarios every epoch. Evaluation splits
  (validation, test, held-out geometry) are files with committed digests.
- **Conformance to gitma.** For a fixed set of seeds the Python generator MUST reproduce gitma's
  committed scenario files equal after float32 rounding (integers, flags and strings byte-equal).
  This is the pipeline gate's first check.
- **Types** stay in LinkML (`schema/tma.yaml`, carried over) and generate Pydantic; gitma's files
  remain readable.
- **Labels** gain, from the stored truth, per-timestep manoeuvre spans and kinds (already in
  0.5.0's `ManoeuvreSpan`), and the per-scenario Fisher information / Cramér–Rao bound for range,
  course and speed at every scored timestep, computed from the true trajectory and the valid
  bearings.

## 4. Model requirements

**The estimate comes from physics.** A gitma2 model is an encoder, a set of heads, and a declared
physics layer (constitution III):

| Part | Requirement |
| --- | --- |
| Encoder | Standard operators only (dense, attention, normalisation); causal mask for the instantaneous variant, full for time-late. A GRU encoder is allowed as a control. |
| Heads | Per timestep: soft changepoint weights over earlier timesteps and a manoeuvre-kind probability (segmentation; Annex A); per-bearing log-weights; an initial state; a covariance calibration scalar. |
| Physics layer | A piecewise-constant-velocity bearings-only batch solve (position at window start plus one velocity per segment; wrapped residuals over σ; ridge prior between consecutive segments and a speed-continuity prior across course-only manoeuvres, both with strengths from the heads), **K fixed Gauss-Newton or Levenberg–Marquardt iterations** from the initial state, no data-dependent control flow. Output: state at the current time and its covariance σ²(JᵀJ)⁻¹. Its equations are stated exactly in an algorithm note. With trivial inputs (no changepoints, uniform weights, grid start) it MUST reproduce gitma's batch least squares to float32 precision. |
| Loss | Squared errors of log range, vx, vy at scored timesteps, **normalised by the per-scenario Cramér–Rao bound**; auxiliary down-weighted changepoint loss from the truth spans with tolerance, and β-NLL (β ≈ 0.5) on the calibrated covariance. Several noise draws per truth trajectory per batch. |
| Controls | (a) the same encoder with a direct regression head and the same loss, never carried; (b) the physics layer fed by a CUSUM/GLR detector instead of the learned segmenter; (c) shuffled labels. |
| Export | One ONNX graph (fixed window length, dynamic batch, standard ops), safetensors weights, JSON manifest; conformance across ONNX Runtime Python, browser WASM and Java to 1e-5 on a golden batch. |

**Compute.** Free GitHub-hosted 4-core CPU runners (owner decision 2026-10-31): a carried
configuration MUST complete one epoch over 10^5 scenarios in under an hour on them; runs are
chained ≤ 6 h jobs with per-epoch checkpoints; every job's duration is recorded.

## 5. Baselines, metrics and gates

**References, all on the same rows:** naive (training-set mean); batch least squares
(gitma's algorithm, ported and checked); EKF and IMM re-tuned on the gitma2 validation split with
declared grids and frozen before training; the **oracle ceiling** (the physics layer with truth
segmentation and kinds, `docs/research/05`); for Annex A, CUSUM and GLR detectors.

**Metrics** as gitma §5 (median and P90 of range, course, speed; gross-error rate; sliced by range
band, zig angle, σ, time since zig and time since last manoeuvre) plus **efficiency**: the median
over a slice's rows of each error divided by that row's Cramér–Rao bound, divided by 0.6745, so
that an unbiased estimator at the bound scores 1 and higher is worse (spec 002; P0 measured batch
least squares at 0.95–1.01 on held-course rows).

**Statistics.** Paired, scenario-clustered bootstrap; pass needs the whole interval and the point
within the limit, fail needs the interval wholly beyond it, otherwise inconclusive with one
re-score on a larger fresh seed, then final (gitma FR-015). Three training seeds per carried
configuration; the carried weights chosen by a rule named in the decision record.

| Gate | Criterion | Decision if failed |
| --- | --- | --- |
| **P0 pipeline** | Generator reproduces gitma's files; Python batch LS, EKF and IMM reproduce gitma's prediction files on the same data to float32; the physics layer with trivial inputs equals batch LS and recovers noise-free truth; the oracle ceiling on a 10^5 MAN validation split is within the interval measured in `docs/research/05` | Fix before any training |
| **Gate 1 CV** | On a fresh CV test seed, σ = 1°, at zig + 5 min (range, course) and zig + 10 min (speed): model median within 1.1 × batch least squares on every metric with intervals wholly below, gross-error rate at or below batch LS's, and efficiency (error ÷ bound, 1 at the bound) ≤ 1.25 on the settled slices | One pre-registered iteration, then stop and publish: the physics layer is not learnable end to end as built |
| **Gate D detector** | [Annex A](SRD-annex-A.md) §A.5 | Annex A §A.6 |
| **Gate 2 MAN** | On a fresh MAN test seed, σ = 1°, G5 rows (zig + 5/10/15/20 min): median range and course over all rows wholly below the re-tuned IMM's; on settled rows range, course and speed within 1.1 × batch least squares; at least half of the gap in median range between plain batch LS and the oracle ceiling recovered (interval wholly above 0.5); and (owner, 2026-11-06) more of that gap recovered than Gate S's carried classical segmenter C fed to the physics layer with no learned weights (paired difference wholly above zero; void if a shuffled-label control also beats C on validation). On MAN2 C alone meets the first three, so the last is the learning claim | The write-up proposes the follow-on with a recommended default; adopted if the owner has not objected by the next spec (`AGENTS.md`, Autonomy) |
| **Gate 3 calibration** | (agent, proposed 2026-11-08; owner to merge) On a fresh MAN2 test seed, σ = 1°, G5 rows, the carried E with its calibration (a learned local form on its covariance: per-row scales e^(s_i) of the standard deviations of log range, bearing, speed and course, correlations kept, from a head on causal features; points unchanged; corrected 2026-11-08, spec 009 FR-043): **G3-a** 95% coverage of log range, course and speed (a row without a usable covariance counts as not covered), each interval wholly within [0.92, 0.98]; **G3-b** (owner, 2026-11-08, before any result) share of rows whose 4-state NEES is within the χ²₄ 95% point, missing rows outside, interval wholly within [0.92, 0.98]; **G3-c** mean 95% interval score in log range below a per-slice temperature fitted on validation (classical control; paired difference wholly below zero; void if a shuffled-label head also beats the temperature on validation), the learning claim; **G3-d** point errors identical to the uncalibrated E's on every row, so Gate 2's result carries over | As Gate 2: the write-up proposes the follow-on with a recommended default; if only G3-c fails, the temperature is carried as the calibration |
| **Gate 4 usable uncertainty** | (agent, proposed 2026-11-08; owner to merge) On a fresh MAN2 test seed, σ = 1°, G5 rows, the carried E with its uncertainty statement (points unchanged): course stated as an arc ±X (X at most 45°) with a probability P that the true course lies within it, otherwise unknown; log range ratio and speed as 95% intervals. A row without a statement states nothing (P = 0, not covered, the uniform course score). **G4-a** range and speed 95% coverage each wholly within [0.92, 0.98]; **G4-b** reliability: hit rate minus mean P wholly within ±0.03 overall, and within ±0.05 (point) in each of five equal-count bins of P; **G4-c** informativeness: the mean circular log score of the course statement wholly above the uniform's, and mean P at least 0.5; **G4-d** the learned statement's standardised summed score (course log score and the two interval scores, each divided by the temperature's mean on the same rows) below a per-slice temperature stated on sd^β per quantity, fitted on validation tuning rows (plan; paired difference wholly below zero; void if a shuffled-error head also beats the temperature on validation), the learning claim against that control (a pass does not by itself show learning beyond a richer classical rule: see §9, 2026-11-09); **G4-e** point errors identical to the uncalibrated E's on every row | As Gate 3: the write-up proposes the follow-on with a recommended default; if only G4-d fails, the temperature's statement is carried |
| **Gate H headroom** | (agent, proposed 2026-11-10; owner to merge; threshold and the form of H-b are the owner's, 2026-11-09 and 2026-11-10) Nothing is trained. On a fresh MAN2 test seed under the primary bearing-error mismatch (correlated error 60 s on half the variance, bias 0.5° with a 30 min correlation time, true σ within a factor 1.5 of the stated 1°, 2% outliers of 10 σ; spec 010 research R2), σ = 1°, G5 rows, **every estimator on the true segmentation**: **H-a** (soundness) the attainable ceiling (the declared solve whitened by the true error covariance, outlier flags not given) has range efficiency against the Cramér–Rao bound under the true covariance within [0.9, 1.6] on settled rows, and a median range error no worse than the plain solve's; **H-b** (soundness; owner, 2026-11-10) on mismatch-off data the classical robust control (Huber weights, σ and a correlation model estimated from residuals; settings from the tuning seed) costs at most 5% in median range error over the plain solve, and the interval of that cost is not wholly above 2%; **H-c** (the verdict; owner, 2026-11-09) R, the robust control's median range error over the attainable ceiling's, minus 1: headroom is **material** if the interval is wholly above 10%, **not material** if wholly below, otherwise inconclusive with one re-score on a larger fresh seed. Intervals are paired, scenario-clustered, 97.5%. H-a and H-b are applied on the validation seed and stop the gate before the test seed if they fail; H-c is decided on the test seed only | Material: a learned component is trained under mismatch with C″ and the robust control as standing controls. Not material: the learning track on this estimator stops and the null result is published. Either way the scaled end-to-end regressor control (§9, 2026-11-09) follows |

## 6. Architecture and tooling

- Python 3.12+, `uv`; PyTorch 2.x; NumPy, numba; LinkML → Pydantic; `pytest` golden tests;
  `ruff`, `mypy --strict`. Docusaurus site under `site/` as gitma.
- Layout: `schema/`, `src/tma2/{types,sim,references,features,models,physics,eval,export}`,
  `configs/`, `experiments/`, `specs/`, `site/`, `scripts/`.
- Each pipeline stage is a CLI reading and writing files; plan branches `train/<id>` and result
  branches `results/<plan>-<run>` as gitma.

## 7. Experiment plan

1. Foundations and **P0** (generator conformance, references, physics layer, ONNX harness, CPU
   throughput measured).
2. **Gate 1** on CV: encoder + weighting and initialisation heads + physics layer, no
   segmentation; pre-registered; three seeds.
3. **Annex A** detector: specified, trained and gated on MAN data; its segmentation feeds the
   physics layer without end-to-end training first (Gate D).
4. **Gate 2** on MAN2: the learned model and physics layer trained end to end against the re-tuned
   IMM, batch LS, the oracle ceiling and Gate S's carried segmenter C, which is the carried-forward
   control (Annex A §A.9 supersedes the Gate D detector here). Learned segmentation is tested
   within Gate 2 (owner, 2026-11-05); spec 007.
5. Afterwards, pre-registered, in this default order unless the owner reorders: uncertainty
   calibration (spec 008, Gate 3), realistic bearing error (spec 010, Gate H: headroom first), the browser viewer on the exported
   artefact.

Agents run this plan without waiting on the owner except for the owner-only items in
`AGENTS.md` (Autonomy and owner input). Defaults stated in this SRD and its annexes are adopted
and recorded, not asked.

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| Backpropagation through the unrolled solve is ill-conditioned near degenerate geometry | Levenberg damping with a learned floor, gradient clipping, implicit differentiation through the final normal equations, initialisation from the heads |
| The learned segmenter false-alarms like gitma phase 3b | Trained through the estimate; the ridge prior makes a false knot on a long leg cheap; CUSUM/GLR controls; Annex A gates false alarms explicitly |
| CPU budget limits data and model size | Vectorised on-the-fly data removes the storage path; models are small by design (the physics layer does the work); throughput is measured in P0 before any decision record |
| ONNX export of the solver | Fixed K, explicit small-matrix algebra, no control flow; conformance test exists before any model |
| Generator port drifts from gitma | Conformance to gitma's committed files is the first P0 check and a permanent golden test |
| The gates test a hope rather than a design | The oracle ceiling and the trivial-input layer bound every result from above and below |

## 9. Decisions taken

- **2026-10-31 (owner):** free CPU runners with PyTorch; Python throughout with a NumPy/numba
  generator; constant-velocity problem first, then manoeuvres; LinkML kept, generating Pydantic;
  site, pre-registration and panel kept (`docs/research/04-proposal.md` §6).
- **2026-10-31 (owner):** the steady-leg detector is its own SRD annex and spec inside gitma2,
  gated on detection metrics and on the downstream estimate, designed for later end-to-end
  fine-tuning (Annex A).
- **2026-10-31 (owner):** the owner is not to be a blocker. Agents proceed from the documents;
  stated defaults are adopted and recorded; only the owner-only list in `AGENTS.md` waits for the
  owner (constitution 1.1.0).
- **2026-11-04 (owner):** the steady-leg requirements are Annex B. The simulation model changes
  to match them rather than the thresholds to the simulation: target legs of 10–40 min, bell
  shaped, 5% at 10 min, in 40–120 min windows (generator 0.6.0, the MAN2 variant), before spec
  005 is gated.
- **2026-11-01 (agent, proposed; owner to merge):** Gate 1's efficiency criterion corrected. As
  written ("efficiency ≥ 0.8") it pointed the wrong way for an error-over-bound ratio, so every
  inefficient model passed (P0 panel round 2, statistics). Now ≤ 1.25 on the settled slices,
  1.25 being the reciprocal of the intended 0.8; no result on Gate 1 exists.
- **2026-11-08 (agent, proposed; owner to merge):** Gate 3 (uncertainty calibration, spec 008)
  added to §5. The bands are absolute calibration targets (95% coverage within ±3 points, NEES
  within 0.8–1.25 of its χ²₄ median), not tuned to any result; no Gate 3 result exists. The
  learning claim (G3-c) is against a classical per-slice temperature, following Gate 2's lesson
  that a rule can match a learned component.
- **2026-11-08 (owner, after the validation baseline, before any Gate 3 result):** G3-b changed
  from the median NEES ratio in [0.8, 1.25] to the share of rows within the χ²₄ 95% NEES point in
  [0.92, 0.98]. E's errors are heavy-tailed (a third of course errors exceed 30°), so a Gaussian
  covariance whose 95% statements are honest has a median NEES far below 1 (0.04–0.18 for a
  temperature on the tuning rows) and the two checks could not both pass
  (`experiments/20261108-g3-base-val/`). The median NEES is reported, not gated.
- **2026-11-08 (agent, proposed; owner to merge):** Gate 4 (usable uncertainty, spec 009) added
  to §5, the Gate 3 follow-on. Gate 3 stopped at validation: E's errors are heavy-tailed (35% of
  course errors exceed 30° on the tuning rows) and not predictable from causal features (AUC
  about 0.62), so a Gaussian course interval honest at 95% covers the whole circle on half the
  rows. Gate 4 asks instead for a statement an operator can act on: course within ±X with
  probability P (reliability gated, not coverage), range and speed 95% intervals; the 4-state χ²
  consistency check is reported, not gated. The bands are absolute targets set from the tuning
  rows' sampling error (research note in `specs/009-usable-uncertainty/research.md` R7), not
  tuned to any result; no Gate 4 result exists. The Gate 3 row's form is corrected to what was
  registered (a local form, not one scale).
- **2026-11-09 (agent, after the result):** Gate 4 stopped at validation (G4-b's top bin of P,
  +0.054 against 0.05; `experiments/20261109-g4-val/`, panel rounds 1–2). The panel found G4-d's
  pass largely reproducible by a classical function of E's three sds (72% of the margin by a
  quadratic rule fitted on tuning rows), so a G4-d pass does not by itself show learning. Criteria
  unchanged; the wording of the Gate 4 row's control corrected to what the plan registered.
- **2026-11-09 (owner):** direction after Gate 4. Every learned component so far has reduced to
  a classical rule under its control, most likely because the generator's bearing errors are
  exactly the estimator's model (`docs/research/10-reflection-headroom.md`). Next is a **headroom
  gate under bearing-error mismatch with no learned model** (spec 010, Gate H; §7 step 5's
  realistic bearing error): correlated, slowly biased, unknown-σ and outlier errors; the standing
  classical estimator C″ and a classical robust control against an oracle that knows the error
  model. Material headroom: a learned component is trained under mismatch with those controls;
  none: the learning track stops and the null result is published. The Gate 4 follow-on
  (course-probability fixes) is set aside. After Gate H, whatever its result, the scaled
  end-to-end regressor control (`docs/research/04-proposal.md` §3, option B) runs on Modal within
  its free credit; the owner sets up the account and secret. Gate H's §5 row is proposed with
  spec 010's plan, before any result.
- **2026-11-10 (agent, proposed; owner to merge):** Gate H (spec 010) added to §5. Its threshold
  (10%) is the owner's of 2026-11-09 and the form of H-b the owner's of 2026-11-10 (point at most
  5%, interval not wholly above 2%: the first draft, at most 2% with the whole interval below,
  could not be decided at the validation sample size). Three points are the agent's and open to
  the owner on this merge: both sides of the comparison are given the true segmentation, so that
  the segmentation shortfall already measured at Gates S and 2 is not counted as error-model
  headroom (spec 010 research R6); H-a's band [0.9, 1.6] is set from the plain oracle's
  efficiency on clean tuning data (1.57: the oracle approximates each manoeuvre by a chord, so it
  is not at the bound, and the ceiling is the ceiling *of this solve*); intervals are 97.5%, as
  at Gates 2 to 4. No result on validation seed 321 or test seed 322 exists: neither has been
  generated. Tuning seed 320 has been used (`experiments/20261109-gh-tuning/`,
  `experiments/20261110-gh-grid/`, `experiments/20261110-gh-refs/`).
- **2026-11-10 (owner, recorded by the agent):** the owner chose H-b's form and then said in the
  session "merged, go ahead with validation and test". PR 25, which carries the Gate H row, was
  still open at that moment; validation (seed 321) and test (seed 322) ran from its branch on
  that instruction. The row, the plan and the decision record were committed (a814ac5) before
  either seed was generated and have not been edited since.
- **2026-11-11 (owner, recorded by the agent):** spec 011 stops at tuning and is published
  (`site/blog/2026-11-11-robust-segmenter.md`); no Gate R row is added to §5. On tuning seed 323
  the robust confirmation test did no more than a raised threshold, and neither closed most of
  the gap to the true manoeuvre times. C stays frozen and C″ the standing classical system;
  seeds 324 and 325 are unused. Spec 012 (the scaled end-to-end regressor, a control) runs
  beside it on the owner's Modal account with a budget of $50 in total (2026-11-10).
- **2026-11-11 (owner, recorded by the agent):** spending on the Modal account within the $50
  budget of spec 012 needs no further approval: "I've allocated the funding to this project."
  Agents still register any run before its result and keep the ledger; anything beyond $50, a
  new account or a new secret remains owner-only.
- **2026-11-12 (owner, recorded by the agent):** spec 013 (time-late) stops at tuning and is
  written up; no Gate T row is added to §5. On tuning seed 329 the bearings and Annex B's
  manoeuvre statistics leave the manoeuvre history ambiguous in about half the difficult
  periods, so no estimator that names one history reaches the true-history reference
  (`experiments/20261111-tl-retest/`, `experiments/20261112-tl-prior/`). The time-late goal is
  re-scoped from one track to candidate tracks with probabilities (a new spec). The GPU pause
  of 2026-11-11 is lifted for time-late learning: "you now have freedom to use GPU in support
  of the time-late learning", within the same $50 total; runs are registered before their
  results and the ledger is kept. Seeds 330 and 331 are unused.

## Annexes

- [Annex A: Steady-leg detector and Gate D](SRD-annex-A.md) (draft 2026-10-31).
- [Annex B: Ownship and target manoeuvres, steady-leg segmentation](SRD-annex-B.md) (owner's
  requirements, 2026-11-04; implemented by spec 005 and Gate S, Annex A §A.9).
