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
band, zig angle, σ, time since zig and time since last manoeuvre) plus **efficiency**: the ratio
of each error to its Cramér–Rao bound, per slice.

**Statistics.** Paired, scenario-clustered bootstrap; pass needs the whole interval and the point
within the limit, fail needs the interval wholly beyond it, otherwise inconclusive with one
re-score on a larger fresh seed, then final (gitma FR-015). Three training seeds per carried
configuration; the carried weights chosen by a rule named in the decision record.

| Gate | Criterion | Decision if failed |
| --- | --- | --- |
| **P0 pipeline** | Generator reproduces gitma's files; Python batch LS, EKF and IMM reproduce gitma's prediction files on the same data to float32; the physics layer with trivial inputs equals batch LS and recovers noise-free truth; the oracle ceiling on a 10^5 MAN validation split is within the interval measured in `docs/research/05` | Fix before any training |
| **Gate 1 CV** | On a fresh CV test seed, σ = 1°, at zig + 5 min (range, course) and zig + 10 min (speed): model median within 1.1 × batch least squares on every metric with intervals wholly below, gross-error rate at or below batch LS's, and efficiency ≥ 0.8 on the settled slices | One pre-registered iteration, then stop and publish: the physics layer is not learnable end to end as built |
| **Gate D detector** | [Annex A](SRD-annex-A.md) §A.5 | Annex A §A.6 |
| **Gate 2 MAN** | On a fresh MAN test seed, σ = 1°, G5 rows (zig + 5/10/15/20 min): median range and course over all rows wholly below the re-tuned IMM's; on settled rows range, course and speed within 1.1 × batch least squares; and at least half of the gap in median range between plain batch LS and the oracle ceiling recovered (interval wholly above 0.5) | The write-up proposes the follow-on with a recommended default; adopted if the owner has not objected by the next spec (`AGENTS.md`, Autonomy) |

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
4. **Gate 2** on MAN: the detector and physics layer fine-tuned end to end against the re-tuned
   IMM, batch LS and the oracle ceiling; the Gate D detector as the carried-forward control.
5. Afterwards, pre-registered, in this default order unless the owner reorders: uncertainty
   calibration, realistic bearing error, the browser viewer on the exported artefact.

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

## Annexes

- [Annex A: Steady-leg detector and Gate D](SRD-annex-A.md) (draft 2026-10-31).
