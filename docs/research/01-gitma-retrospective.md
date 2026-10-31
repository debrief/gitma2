# What gitma established, and why it stalled where it did

A critical reading of [debrief/Gitma](https://github.com/debrief/Gitma) (October 2026), written to
decide what gitma2 should keep, drop and change. Figures are taken from gitma's committed
experiment records, blog posts and training manifests as of 31 October 2026.

## 1. The record in one table

| Step | Problem | Best network result | Classical reference on the same rows | Outcome |
| --- | --- | --- | --- | --- |
| G1 (iteration 1) | 2 legs, σ 0.5°, no dropouts | range error well under half the naive baseline's | — | pass |
| G2 (iterations 2, 2b, 2c) | 2 legs, σ 1–2°, dropouts | range 12–14%, course 6–7°, **speed 1.47–2.38 kt** | speed 0.60–0.62 kt (at the Cramér–Rao bound) | fail ×3 on speed |
| G2 (iterations 3, 4) | 3 legs, velocity outputs, derived features | range 7.3%, course 4.7°, **speed 0.94 kt** [0.93, 0.95] | range 3.4%, course 1.4°, speed 0.32 kt | pass (on a 100k re-score) |
| G3 (iteration 5) | same data, no training | hybrid = classical, overruled by the network where they disagree > 50% | — | pass **for the hybrid**; network alone 3 × classical |
| G4 (phase 3, 3b) | one target turn in 80% of scenarios; tuned IMM reference | after a turn: range 0.76 ×, course 0.60 × the IMM; held course: speed 1.15–1.60 kt (limit 1 kt) | IMM held-course speed 0.71 kt, batch LS 0.31 kt | stopped at validation, twice |
| G5 (phase 4, running) | 0–3 turns + speed change; learned-gain filter (T1) and Gaussian LSTM (T2) | T1 diverged once, retrained to best epoch 67; T2 at epoch 17 after 5.5 h, incomplete | IMM 9.24% median range over G5 rows; batch LS 6.7% on settled rows | not yet scored |

Three findings are robust across every iteration:

1. **A plain recurrent regressor extracts the TMA signal** (G1, G2). It gives usable range and
   course quickly, and is more robust than least squares in near-unobservable geometry (gross
   errors 1.19% → 0.57% at zig + 5 min, 4.6% → 1.8% at σ = 2°).
2. **It never approaches the information bound.** Six iterations left speed at about 3 × classical,
   and the gap is **flat across range and bearing-rate bands** where classical's error falls to
   0.1–0.4 kt (Annex A §B.1). Capacity, training budget and loss weighting each moved it by
   ~0.3 kt as a uniform shift.
3. **After a target manoeuvre the network wins, before one it loses.** Two output designs beat a
   tuned IMM by 25–40% five minutes after a turn, and both gave back accuracy on straight legs,
   because an MSE regressor hedges between "turned" and "not turned".

## 2. Diagnosis: the error floor is approximation error, not information

The most informative number in the whole record is the shape of the speed error, not its size.
Classical's speed error tracks the Fisher information: it is small where geometry is kind and
large where it is not. The networks' error is roughly constant across those same bands. That is
the signature of a function approximator that has reached a precision floor, not of an estimator
that lacks information. Several things in the gitma design made that floor high:

- **The network was asked to be the numerics.** For a constant-velocity target the sufficient
  statistics of the bearing history are the Gauss-Newton normal-equation accumulators: sums of
  products of bearing-line geometry and time. A 128-unit LSTM has to carry an approximation of
  those through 240–360 steps in its hidden state and then invert them. Reaching 0.3 kt on a
  3–20 kt target is a ~2% relative precision task for a quantity that enters the bearings only at
  second order (the bearing *rate* change across the zig). Recurrent networks are poor at this
  kind of precise accumulation; the iteration-4 gain from feeding bearing rate as a feature is
  consistent with that.
- **Compute and data were an order of magnitude or two short.** Every model trained on 80,000
  scenarios on 4 CPU cores under tfjs-node, at 0.5–1 h per epoch. The largest run was 35 h for a
  540k-parameter BiLSTM. The whole project used roughly 300 CPU-hours, which is a few GPU-hours of
  modern training. The SRD anticipated 10^6 scenarios for G3; no run exceeded 10^5. Amortised
  inference of a precise posterior from 10^5 examples with Adam and early stopping at patience 6
  is simply undertrained, and the project's own capacity scan could not separate "capacity is
  flat" from "nothing here is trained to convergence".
- **MSE on a point estimate.** Under genuine ambiguity (range along the near-unobservable valley,
  turned vs not turned) the conditional mean is the wrong summary. Phase 3b's two-hypothesis head
  helped course but not speed, and its false-alarm rate (30% on held rows) shows that a hard switch
  trained on a binary label is not a posterior either.
- **Causal, per-timestep output from a single hidden state.** The instantaneous model recomputes
  nothing: whatever it did not store at step 100 is gone at step 200. Batch least squares, by
  contrast, re-solves over all bearings each step. That is the reason classical leads "given ten
  minutes" everywhere (B.1) and why T2's advantage shows only right after a manoeuvre.

The positive side of the diagnosis is equally clear. The things the network *did* learn (a
geometry-aware prior, robustness near unobservability, fast reaction to a manoeuvre) are exactly
the things least squares and the IMM lack. The hybrid result (G3) and the post-turn result (G4)
are both cases of the network supplying judgement that the classical estimator's numerics then
cannot exploit, because the two were bolted together after the fact rather than trained together.

## 3. Methodology: what to keep

gitma's process is its strongest asset and should carry over almost unchanged:

- **Pre-registration.** Decision records with forecasts committed before training; fresh test
  seeds per look; one re-score rule; the validation rule that stops a phase before the test split
  is touched. This is why none of gitma's results is in statistical doubt.
- **Baselines on the same rows.** Naive, batch LS, and from phase 3 a tuned IMM/EKF. Medians and
  P90s, sliced; gross-error rates. The IMM re-tuning on validation with declared grids is good
  practice and should be repeated for any new problem variant.
- **Provenance and determinism.** Seeded generation, digests on data and weights, byte-identical
  re-scoring, schema-versioned files, G0 as a gate on the pipeline itself.
- **The agent review panel** with speciality reviewers and severity-tagged findings. Round 0 of
  the phase-4 G0 panel caught two mis-scoped tracker checks; that is the mechanism working.
- **The public write-up discipline:** every result has a blog post that reads itself critically.

## 4. Methodology: what to change

- **One lever per iteration was too slow for the question being asked.** Fourteen iterations,
  each a day or two of process plus 10–35 h of training, were spent moving one hyperparameter at
  a time on an undertrained model family. Pre-registration should bind what is *scored on test*,
  not forbid cheap, broad exploration on validation. gitma's Annex A already relaxed this; gitma2
  should start from the relaxed position: explore widely on validation with many seeds, then
  pre-register one configuration per gate.
- **Single training seed per model.** Seed-to-seed variance was never measured, so no lever's
  0.3 kt effect is distinguishable from initialisation noise. Three seeds minimum, reported as a
  spread.
- **The TypeScript / tfjs-node constraint cost more than it bought.** It fixed training to CPU,
  cost roughly 10 × throughput, forced a hand-built causal padding (tfjs's `causal` is `valid`),
  had no gradients for dilated convolutions, hit a 2 GiB `readFileSync` limit on feature files,
  and still needed chained 345-minute jobs with checkpoint branches. The cross-language goal it
  served (one codebase for generator, training and browser inference) is better met by a
  portable *model artefact* than by a portable *training stack* (see
  [03-infrastructure.md](03-infrastructure.md)).
- **Precomputed feature files.** 2.3 GB per split, digest-checked, regenerated per generator
  version. A vectorised generator that produces batches on the fly from a seed gives unlimited
  fresh data, removes the storage path, and keeps determinism (seed → batch). Only evaluation
  splits need to exist as files.
- **The error metric hides the diagnosis.** Reporting error / CRB (statistical efficiency) per
  slice would have shown in iteration 2 that the models were at a flat approximation floor rather
  than short of information, and would have redirected effort from loss weights to architecture
  and compute.
- **Gates asked "better than X" without a mechanism.** G4 and G5 ask a network to dominate a tuned
  tracker on both manoeuvre and settled rows. No gitma architecture had a component capable of
  settled-row precision, so those gates tested a hope rather than a design. gitma2 should pick an
  architecture whose settled-row accuracy is least squares' by construction (next section), so
  that the gate tests only the part that is genuinely in question.

## 5. The question gitma2 should ask

gitma answered its original question: a network trained on simulated bearings extracts usable
range, course and speed (G2) but not with classical precision, and it is better than a tracker
after a manoeuvre but worse before one. The open question is sharper:

> Can a learned component, trained end to end with explicit bearing geometry, be *at least* as
> accurate as batch least squares wherever the constant-velocity model holds, and better than a
> tuned IMM wherever it does not, with calibrated uncertainty, from a single model?

The design that follows from the diagnosis is to stop asking the network to do the numerics.
Let it do segmentation, initialisation, weighting and priors; let a differentiable physics layer
do the estimate. [04-proposal.md](04-proposal.md) sets that out.
