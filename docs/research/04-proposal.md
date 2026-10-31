# Proposal: gitma2, a "segment, weight, solve" tracker

Status: draft for the owner, 31 October 2026. Based on the
[retrospective](01-gitma-retrospective.md), the [literature sweep](02-literature.md), the
[infrastructure notes](03-infrastructure.md) and the
[oracle-segmentation experiment](05-oracle-segmentation.md).

## 1. The one-paragraph version

gitma showed that a network can learn TMA judgement (priors, robustness, fast reaction to a
manoeuvre) but not TMA numerics (it stayed about 3 × the Cramér–Rao bound on straight legs).
Batch least squares has the numerics and no judgement: it is at the bound on a straight leg and
wrong as soon as the target turns. gitma2 should therefore stop asking the network to produce the
estimate. It asks the network for the three things least squares cannot know, **when the target
manoeuvred, how much to trust each bearing, and where to start**, and lets a differentiable
piecewise-constant-velocity batch solve produce the estimate and its covariance. Trained end to
end on GPU with data generated on the fly, exported to ONNX. The oracle experiment on gitma's
own phase-4 data gives the ceiling: with perfect segmentation and nothing else learned, a
piecewise batch solve beats the frozen IMM by about 30% on median range over all G5 rows and
halves its error on settled rows. The project's question becomes whether a learned segmenter can
get close to that oracle, which is a detection task networks are good at, instead of whether a
regressor can reach a precision floor it has never reached.

## 2. Design

### 2.1 Model

One model, three parts, trained jointly:

1. **Encoder.** A causal transformer (or GRU, as a control) over per-timestep tokens: bearing
   sin/cos, ownship position, course and speed, time, validity, plus the derived channels gitma
   found useful (bearing rate, bearing-line intercept). Causal masking gives the instantaneous
   variant; the same weights with full attention give the time-late variant. Standard ops only,
   so it exports everywhere.
2. **Heads**, per timestep k, each a small MLP on the encoder state:
   - **segmentation**: a soft changepoint weight c_j ∈ [0, 1] for each earlier timestep j ≤ k
     (how much the velocity may change at j), produced as a per-timestep logit; in practice
     the knot set is the timesteps whose weight exceeds a threshold at export time, and during
     training it enters the solve as a continuous prior strength;
   - **speed-continuity**: a per-changepoint probability that speed carried through (a course
     change) rather than changing (a speed change), which the oracle experiment shows is worth
     a factor of two on post-manoeuvre speed;
   - **measurement weighting**: a per-bearing log-weight (robustification; learns to downweight
     outliers or near-degenerate rows);
   - **initialisation**: a coarse state (log range, velocity) at the current time, replacing the
     grid search, which gitma showed a network can do (iteration 5, R2);
   - **uncertainty**: the solve's covariance σ²(JᵀJ)⁻¹ is free; a small scalar head calibrates it.
3. **Solver layer.** A fixed-K unrolled Gauss-Newton / Levenberg–Marquardt solve of the
   piecewise-constant-velocity bearings-only problem over bearings 0..k, with the heads' outputs
   as weights and priors. Residuals are wrapped bearing differences divided by σ; parameters are
   position at window start and one velocity per segment; a ridge prior ties consecutive segment
   velocities with strength from the segmentation head, and a soft speed-continuity prior with
   strength from that head. K = 5–8 iterations from the initialisation head; everything is batched
   dense linear algebra on at most 2 + 2 S parameters, so it is cheap and exports as plain ops.
   The output is the solve's state at k: range, course, speed, position, covariance.

Why this answers gitma's failure modes directly:

| gitma failure | mechanism here |
| --- | --- |
| 3 × CRB on straight legs | the estimate is a least-squares solve, which is at the CRB there by construction |
| hedging after a turn (3a) | there is no average: the solve either has a knot or it does not, and the segmentation head is trained through the final error, not on a label |
| false alarms on held course (3b) | a false knot costs little on a long leg (the ridge prior holds the velocity) and the head is penalised through the estimate, not through a turned/held cross-entropy |
| gross errors near unobservability | initialisation and weighting heads carry gitma's demonstrated robustness; the 50% hybrid switch becomes a learned weight |
| no usable uncertainty | the solve's covariance, calibrated, comes out at every step |

### 2.2 Loss

- Primary: squared errors of log range, vx and vy at every scored timestep after the zig,
  **normalised by the per-scenario Cramér–Rao bound** computed from the true trajectory
  (literature §4). This makes a well-observed scenario count at full weight and a hopeless one at
  the weight its information deserves, and it reports *efficiency* (error / CRB) as the training
  curve, so an approximation floor is visible immediately.
- Auxiliary, down-weighted: a changepoint loss from the truth manoeuvre spans (a soft target with
  tolerance), and a Gaussian NLL on the calibrated covariance using β-NLL (β ≈ 0.5) so the mean is
  not degraded. These accelerate early training; the primary loss decides.
- Several noise draws per truth trajectory per batch (bias-reduced training), which on-the-fly
  generation makes free.

### 2.3 Data

- A vectorised generator in Python (JAX or NumPy + numba) reproducing gitma's generator 0.5.0
  semantics (0–3 course changes, one speed change in 30%, rate-limited turns, ownship zig rule
  `across_los`), batched on the fly from a 64-bit seed. gitma's committed scenario files and
  golden tests are the conformance oracle for the frame conventions; the LinkML schema is reused
  for every file that is exchanged (evaluation splits, predictions, manifests).
- Train on effectively unlimited data (10^7 scenarios per training run is a few GPU-hours);
  validation and test splits are fixed files with digests, as before.
- Start simple on purpose: phase-4 ranges, σ ∈ {1°, 2°}, dropouts, as gitma. Add correlated
  bearing error and slow bias once the gate is passed (gitma Annex C's deferred realism item).

### 2.4 References and gates

Keep gitma's references and add the one it lacked:

- naive; batch least squares; the frozen phase-4 IMM re-tuned on the new validation split with
  declared grids; **and the oracle-segmented batch solve** as the ceiling for this design.
- **Gate A (design is sound):** on σ = 1° G5 rows, the trained model's median range and course are
  wholly below the IMM's (paired, scenario-clustered, 97.5% intervals) and within 1.1 × batch
  least squares on settled rows. This is gitma's G5 with the settled check tightened to least
  squares, which is the honest settled reference.
- **Gate B (the learned part earns its keep):** the model closes at least half the gap between
  plain batch least squares and the oracle on overall median range. This is the question that is
  actually open.
- Controls: the same encoder with a plain regression head (gitma's T2, re-trained at scale, which
  also settles whether gitma's result was a compute artefact); the solver with a CUSUM detector
  instead of the learned segmenter.
- Everything else as gitma: pre-registered decision record with forecast, fresh seeds, one
  re-score, agent review panel, baselines on the same rows, medians and P90s, sliced.

### 2.5 Portability

The export is one ONNX graph: encoder (attention, MLP), heads (MLP) and the unrolled solver
(matmul, atan2 via standard ops, small batched inverses via explicit 2 × 2 / block formulae or the
ONNX `Inverse`-free Cholesky written in ops). Fixed window length 360, dynamic batch. Conformance
across ORT Python, ORT-web WASM and ORT Java on a golden batch in CI. Weights also in safetensors
with a JSON manifest, and the solver's equations in an algorithm note, so a port can be written by
hand and tested against the golden batch, as gitma's constitution already requires for a declared
filter layer.

## 3. Alternatives considered

| Option | Verdict |
| --- | --- |
| **A. Segment, weight, solve** (this proposal) | recommended: the ceiling is measured, the open question is a detection task, settled-row accuracy is least squares' by construction |
| B. Scale gitma's T2 (regression LSTM/transformer, GPU, 10^7 scenarios, CRB loss, MDN head) | run it as the control: it is cheap on GPU and answers "was gitma undertrained?" If it reaches the CRB on straight legs, A's solver layer is unnecessary and the design simplifies |
| C. Learned-gain or bounded-correction filter (KalmanNet family, Unscented KalmanNet) | second choice. Causal, cheap at inference, literature-backed; but a filter is the wrong comparison class for a fixed-lag gate, gitma's T1 was fragile, and it inherits the IMM's structure rather than beating it |
| D. Amortised posterior (flow/diffusion over the full parameter vector incl. manoeuvre times) | attractive as a later upgrade to A's output (posterior over knots and state), not a first step: more machinery, no tracking precedent |
| E. Learned IMM mode probabilities on top of the frozen IMM | low ceiling (8–12% in the literature), still a filter |
| F. Differentiable particle filter | not recommended: the one honest radar study lost to the IMM |

## 4. Risks

- **The segmenter false-alarms like phase 3b.** Mitigation: it is trained through the estimate,
  so a false knot on a long leg is nearly free and a missed knot is expensive; the ridge prior
  caps the damage; the CUSUM control shows whether learning adds anything.
- **Young legs are unobservable whatever the segmentation.** Right after a manoeuvre no estimator
  knows the new velocity; the oracle's speed error on unsettled rows shows this. The gate is
  scored on medians over fixed times and the speed-continuity prior recovers most of it; the
  write-up should show the error-vs-time-since-manoeuvre curve.
- **Backpropagation through an unrolled solve** can be ill-conditioned near degenerate geometry.
  Mitigations: Levenberg damping with a learned floor, gradient clipping, stop-gradient through
  the Jacobian's inverse (implicit differentiation), and starting from the heads' initialisation
  rather than the grid.
- **ONNX export of the solver.** Fixed K, no data-dependent control flow, explicit small-matrix
  algebra; tested in CI from day one, before any training.
- **Scope creep in the generator port.** Port exactly 0.5.0 and prove it against gitma's golden
  files before anything else; new realism only after the gate.
- **Compute access.** Team plan plus the T4 runner, or Modal; decide before the spec.

## 5. Plan of work

1. **Foundations (one PR each):** vectorised generator with conformance to gitma's golden
   scenarios; batch LS, EKF, IMM, CRB in Python, checked against gitma's outputs on the same
   files; the oracle-segmented solver as a reference CLI; ONNX conformance harness with a toy
   model across Python, WASM and Java.
2. **G0 equivalent:** the Python solver recovers noise-free truth; the IMM reproduces gitma's
   frozen reference numbers on a gitma file; the oracle ceiling is reproduced on a 10^5 validation
   split.
3. **Control first:** gitma's T2 re-trained at scale with the CRB loss, on GPU. One day of work,
   answers the compute question.
4. **The model:** encoder + heads + solver; pre-registered decision record; three training seeds;
   validation rule; fresh test seed; panel; write-up.
5. **Then:** uncertainty calibration, correlated bearing error, in-browser viewer via ORT-web.

## 6. Decisions for the owner

Each is a choice that changes the work. Suggested answers are first.

1. **Training compute.** (a) GitHub T4 runner under a Team plan; (b) Actions job driving Modal;
   (c) stay on free 4-core CPU runners with PyTorch (3–7 × faster than tfjs-node, still slow).
2. **Language.** (a) Python throughout (PyTorch model, JAX or numba generator), ONNX artefact;
   (b) Python training with a C++ generator; (c) JAX throughout.
3. **First target.** (a) Gate A and B as above on phase-4 (0.5.0) data; (b) first reproduce
   gitma's G2 problem (constant-velocity target) to show the solver layer reaches the CRB, then
   move to manoeuvres; (c) go straight to realistic bearing error.
4. **Keep gitma's LinkML schema as the source of file types?** (a) yes, generating Pydantic
   instead of zod; (b) replace with Pydantic models and JSON Schema directly.
5. **Site and process.** (a) keep the Docusaurus site, blog, panel and pre-registration as they
   are; (b) keep pre-registration and the panel but drop the site until there is a result.
