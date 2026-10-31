# Literature: learned estimators for bearings-only TMA and manoeuvring targets

A web sweep made on 31 October 2026 for gitma2, covering roughly 2019–2026. Each entry gives the
idea, what was reported, whether code is public, and an honest view of its relevance to *this*
problem, where range observability from an ownship zig is the crux. The shortlist at the end feeds
[04-proposal.md](04-proposal.md).

## 1. Deep learning for bearings-only tracking specifically

Nobody in the open literature has published a single-ownship, zig-observability, full-state
(range, course, speed) learned TMA estimator with EKF, batch least-squares and CRLB baselines.
gitma's own record is, as far as this sweep can find, the most careful open comparison. That is a
gap, not a reassurance: it suggests that the people who tried did not get publishable wins.

- **Torok, Deghat, Song, "Bearing-only tracking and circumnavigation ... utilising an LSTM"**
  ([arXiv 2504.19463](https://arxiv.org/abs/2504.19463), ECC 2025). Many-to-one LSTM regressing
  relative position and velocity; the agent circles the target, so range observability is never
  in question. Baselines are classical circumnavigation observers, not filters. No code.
  Relevance: low.
- **Shalev & Klein, BOTNet** ([Sensors 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8271718/)).
  MLP for static multi-sensor triangulation: 40% lower RMSE than iterative least squares inside
  the training grid, worse outside it. Code public. Relevance: low, but a clean demonstration of
  a net beating least squares in-distribution by exploiting the prior and losing out of it.
- **Zhou et al., "Bearings-only TMA via deep reinforcement learning"** (IEEE/CAA JAS 2025,
  3-page letter) and a GRU-PPO speed estimator (Ocean Engineering 2025, paywalled). No numbers in
  the abstracts, no code. Relevance: a pointer that others found the speed/bias problem; the
  method is a hype flag (RL on a supervised regression task).
- **Ristic & Arulampalam, "RL-trained observer control for bearings-only tracking"**
  ([arXiv 2605.02120](https://arxiv.org/abs/2605.02120), 2026). The learned part is the ownship
  manoeuvre policy; the estimator is still a cubature Kalman filter. Relevance: medium as a
  reward-design template (Mahalanobis consistency plus error), not as an estimator.
- Passive-sonar papers that put a CNN or GRU in front of or beside a Kalman filter
  ([Sensors 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12473789/), JMSE 2022, PLOS ONE 2022):
  bearing-track association or qualitative results; no range/course/speed estimation against
  classical baselines. Relevance: low.

## 2. Hybrid model-based and learned estimation

- **KalmanNet** (Revach, Shlezinger et al., [IEEE TSP 2022](https://arxiv.org/abs/2107.10043),
  code public). A GRU learns the Kalman gain inside an EKF recursion. Beats EKF/UKF/PF under
  model mismatch; with correct models it does not beat a well-tuned EKF, and gain learning does not
  create observability. This is gitma's T1.
- **Split-KalmanNet** (Choi et al., IEEE TVT 2023). Two RNNs learn the predicted-state and
  innovation covariances separately and the gain is formed analytically with the measurement
  Jacobian. Robust where KalmanNet fails under strong measurement nonlinearity (range-bearing
  SLAM). Community reimplementation in
  [filternet](https://github.com/tycryang/filternet). Relevance: medium-high for any filter-style
  model; the explicit Jacobian path is what a bearing measurement needs.
- **DANSE / pDANSE** ([2023](https://arxiv.org/pdf/2306.03897),
  [Oct 2025](https://arxiv.org/abs/2510.27503)). RNN emits a Gaussian prior per step; posterior by
  closed form (linear) or particles (nonlinear, tested on spherical measurements of Lorenz-63).
  Relevance: medium; full-rank spherical measurements say nothing about rank-deficient bearings.
- **RTSNet** (Ni, Revach et al., IEEE TSP 2023, code public). A learned smoothing gain. Relevance:
  medium. gitma's gates score a fixed-lag estimate, where a smoother (or batch solve) is the right
  comparison class; gitma's BiLSTM consistently beat its causal LSTM for the same reason.
- **Unscented KalmanNet** ([arXiv 2608.04201](https://arxiv.org/abs/2608.04201), Aug 2026). UKF
  with bounded multiplicative Q/R corrections, a bounded residual gain correction and a
  calibration-aware loss (state error + NEES + innovation consistency); 26–50% RMSE reduction over
  the UKF and the best NEES among covariance-reporting filters. No code. Relevance: high as a
  design pattern: bounded corrections around a correct filter cannot be much worse than the
  filter, and the consistency loss targets the hedging bias gitma saw after turns.
- **"AI-aided Kalman filters"** tutorial (Shlezinger et al.,
  [arXiv 2410.12289](https://arxiv.org/abs/2410.12289), IEEE SPM, code). Taxonomy of
  task-oriented (learn gain/estimate) vs model-oriented (learn noise covariances, dynamics, or a
  latent linear model) hybrids. The model-oriented branch (learn Q, keep the filter) is the one
  least likely to break observability guarantees.
- **Learned process noise / adaptive Q** (NNAKF, ICASSP 2021; DDPG-tuned Q, Sensors 2022).
  Cheap to add to a frozen IMM as a *stronger reference*, which matters because gates are relative
  to the reference.
- **Differentiable particle filters** (review [arXiv 2302.09639](https://arxiv.org/abs/2302.09639);
  mixture-density DPF, NeurIPS 2023). The only radar test with manoeuvres found is a 2025 Chalmers
  MSc thesis where a flow-DPF loses to the IMM beyond low dimension. No bearings-only DPF paper.
  Relevance: medium-low; a lot of engineering for an unproven gain.
- **Learned IMM mode probabilities.** JMFNet ([arXiv 2511.09569](https://arxiv.org/abs/2511.09569),
  Nov 2025): GRU mode predictor + mode-augmented KalmanNet trained end to end without mode labels;
  beats IMM/PF/KalmanNet on CV/CT switching, but with position measurements and only 8–12% over
  KalmanNet. IMMNet ([arXiv 2607.13573](https://arxiv.org/abs/2607.13573), 2026): transformer
  replaces the Markov mode update, 3-D radar, no numbers in the abstract. No code for either.
  Relevance: the idea is gitma's phase-3b head; the useful import is **training the mode head
  through the estimation loss rather than on a turned/held label**, which avoids rewarding early
  hedging. None of these report held-course false-alarm rates, which is what killed phase 3b.

## 3. Amortised inference, sets, and sequence models

- **Neural posterior estimation.** BayesFlow (summary network + conditional flow, trained on
  simulations; [BayesFlow 2.0](https://arxiv.org/abs/2602.07098), 2026, code public) and
  conditional diffusion for NPE ([arXiv 2410.19105](https://arxiv.org/abs/2410.19105), code
  public). A single TMA scenario is a 4–6-parameter (plus manoeuvre-time) inverse problem with a
  known simulator: the textbook setting. The range posterior before and shortly after the zig is
  skewed or bimodal, so a density head that reports a median is the right fix for mean collapse.
  A 2026 preprint ([arXiv 2602.00960](https://arxiv.org/abs/2602.00960)) argues mixture-density
  networks match diffusion on low-dimensional multimodal physics posteriors in the low-data regime,
  so try an MDN head first. Nobody has applied NPE to TMA.
- **Set-based encoders.** Set Transformer (Lee et al., ICML 2019); set-transformer ensemble
  filters beating a tuned LETKF ([arXiv 2504.17836](https://arxiv.org/abs/2504.17836)). An
  attention encoder over (time, bearing, ownship position) tokens handles dropouts natively and
  lets the model align measurements across legs, which an LSTM must carry in its state.
- **Transformers and SSMs as filters.** Constructive proof that a transformer can represent a
  Kalman filter for LTI systems ([arXiv 2312.06937](https://arxiv.org/abs/2312.06937));
  in-context filtering approaching EKF/PF ([arXiv 2410.16546](https://arxiv.org/abs/2410.16546));
  **"Model-free neural filtering" benchmark** ([arXiv 2601.21266](https://arxiv.org/abs/2601.21266),
  Jan 2026): Mamba/Mamba-2 are the strongest model-free estimators but "well-matched model-based
  filters can still outperform". MT3/MT3v2 (Chalmers, code public): transformer multi-target
  tracker competitive with PMBM on radar. Relevance: a backbone change is cheap and worthwhile, but
  every honest comparison still has the matched classical filter on top. Architecture alone will
  not close a 3 × gap that is about numerics and loss.

## 4. Why regressors collapse to the prior, and the remedies

The mechanism: under MSE the optimum is the conditional mean. Where the likelihood is flat (range
on one leg; speed with 1–2° noise over a short post-zig window) that mean is the prior mean, and
under a skewed or bimodal posterior it lies in a low-density region.

- **CRB-normalised loss** (Zhang et al., [MRM 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9050814/)):
  loss = (θ̂ − θ)² / CRB(θ), averaged over samples and parameters; an MSE-trained net was
  bias-dominated, the CRB-trained one reached std ≈ √CRB. **Bias-reduced follow-up** (Mao et al.,
  [arXiv 2312.11468](https://arxiv.org/abs/2312.11468), MRM 2024): average the loss over several
  noise draws of the same truth, so bias and variance are traded explicitly. The loss is one line.
  Relevance: very high. gitma already computes the Fisher information per scenario (classical is
  "at the CRB"); normalising the speed error by its CRB stops hopeless geometries dominating the
  gradient and lets well-observed ones be learned precisely.
- **Heteroscedastic NLL pitfalls**: β-NLL (Seitzer et al., ICLR 2022) and "Faithful
  heteroscedastic regression" (Stirn et al., AISTATS 2023) show plain Gaussian NLL degrades the
  mean because it down-weights high-variance (here unobservable) samples. gitma's T2 uses plain
  NLL and should expect this.
- **Density heads**: MDN (Bishop 1994), quantile/pinball (with Chung et al. 2021's warning on
  conditional quantiles), conditional flows or diffusion (§3). Report a median, not a mean.
- **Observable coordinates**: modified polar (Aidala & Hammel 1983) and log-polar
  ([arXiv 2406.19599](https://arxiv.org/abs/2406.19599), TAES 2025) decouple the observable
  components (bearing, bearing rate, range-rate over range) from the unobservable one (1 / range),
  with closed-form non-Gaussian priors after an ownship turn. No neural paper uses them. gitma's
  velocity parameterisation mixes the unobservable scale into every output; in log-polar
  coordinates the network's leg-2 job reduces to one scalar.
- Curriculum by observability: nothing published; the CRB loss does it implicitly.

## 5. Manoeuvre detection

Classical: CUSUM, GLR, MLR detectors compared in Ru, Jilkov, Li, Bashi (IEEE TAES 2009). Neural
CUSUM ([arXiv 2210.17312](https://arxiv.org/abs/2210.17312)); offline neural change-point
detectors (JRSS-B 2023) contain CUSUM as a special case. DeepMTT (Information Fusion 2020, code
public) learns a BiLSTM residual correction on a filter for manoeuvring aircraft. Nothing is
bearings-only and nothing reports held-course false alarms.

## Shortlist

Ranked by the likelihood of beating batch least squares plus a tuned IMM on gitma's problem:

1. **Observable-coordinate outputs with a CRB-normalised, noise-averaged loss.** Cheapest change,
   strongest mechanistic evidence; aimed squarely at the straight-leg speed gap.
2. **A density head (MDN first, flow or diffusion second), reporting the posterior median.**
   Removes mean collapse where the range posterior is skewed; gives calibrated intervals that can
   drive a hybrid switch instead of a fixed 50% rule.
3. **A bounded-correction hybrid filter with a consistency (NEES) loss** on a log-polar UKF
   (Unscented-KalmanNet / Split-KalmanNet pattern). Cannot be much worse than the filter it wraps.
4. **A learned smoother or batch head rather than a filter** (RTSNet idea). The gate is a
   fixed-lag estimate; batch least squares wins because it uses all data.
5. **A mode head trained end to end through the estimation loss, without labels** (JMFNet), on top
   of 3 or 4.

Not recommended: replacing the LSTM with Mamba or a transformer *alone*; DRL "estimators";
differentiable particle filters for this problem; headline percentages from IMMNet/TrMTT-style
papers with no bearings-only case and no code.

The sweep found no published learned method that matches batch least squares at the CRB on
straight-leg bearings-only data. Items 1–2 are about matching it efficiently; the realistic win
over the classical-plus-IMM reference is after target manoeuvres, where gitma already leads. The
approach in [04-proposal.md](04-proposal.md) takes that seriously: it uses a batch solve for the
numerics and asks the learned component only for what the solve cannot know.
