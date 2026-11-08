# Gate 3 validation stop: agent review panel

Five independent, read-only reviewers: evaluation statistics, estimation and numerics, TMA
geometry, reproducibility and red team. Each was briefed on the committed record (`README.md`,
`validation.json`, `calibration.json`), the decision record, the baseline and the code, and
returned a verdict with findings tagged [blocker], [major] or [minor], with evidence. Their
scratch scripts are not part of the record. Findings are condensed; the numbers are theirs.

# Round 1

All five returned **approve-with-findings**: the stop at validation is correct. None rejected,
none raised a blocker. The majors concern the record's explanations and claims, not the outcome.

## Statistics: approve-with-findings
- Independent recomputation from `errors.npz` (own bootstrap, 2,000 clustered resamples) matches
  the record: coverage95 0.9863 / 0.9227 / 0.9837, G3-b 0.8345 [0.820, 0.850], G3-c +1.068
  [+0.976, +1.172]; the carried seed (median IS95: 5.76, 5.95, 6.00 → cal-s3) is right; missing
  rows (39 per estimator) are handled as registered; the verdict logic and the validation rule
  were applied as written. G3-b's upper limit is 0.07 below the band: no reasonable change to the
  bootstrap or missing-row handling reaches 0.92.
- [major] The README's G3-c mechanism ("the gross-dominated β-NLL widens log range") is not what
  the arrays show: the head is wider on 93% of rows (width ratio quartiles 1.16, 1.32, 1.59), the
  miss penalty is ≈ 0 for both, and 84% of the gap is on rows the temperature already covers. The
  better-supported account: the joint 4-state loss inflates log range globally to absorb tails
  driven by course. State it as such.
- [minor] "Raw E's misses are charged in log range only" is misleading (every estimator is);
  raw E's intervals are ~12× narrower, so its miss penalty costs less than the others' widths.
- [minor] Beating the shuffled head does not show per-row information (global level can do it).
- [minor] Disclose the missing-row charge (the estimator's own 99th percentile) beside G3-c.

## Estimation and numerics: approve-with-findings
- Checked correct: gradients, local Jacobian, the closed-form T⁻¹, the LOCAL order across head,
  temperature, loss and export, q(s) equal to the NEES under A P Aᵀ, course wrapping; the cache →
  prediction → scorer chain loses nothing (cache G3-b 0.843 × 3,895/3,934 = 0.835); no shift
  between stream and validation (global scales agree to ±0.1); the head wins on the loss (NLL
  12.74 against the temperature's 13.12) and loses on the score.
- [major] **G3-b fails mainly because the stated correlations are kept.** Raw local correlations
  are near-singular (median |ρ| 0.81 log range–speed, 0.77 speed–course; 15% of rows have some
  |ρ| > 0.99). With the same scales and correlations dropped, the share within the χ²₄ 95% point
  is 0.957 (head) and 0.937 (temperature). The R5 family (scales only) cannot reach G3-b.
- [major] Training uses the linearised local error u = T e; the score uses exact errors. A course
  flip has a small linearised course error (rows with course error > 90°: median 46.6°
  linearised against 122.6° exact): course coverage 0.962 linearised, 0.932 exact. Log range the
  other way (0.987 against 0.996), pushing it over 0.98.
- [minor] β-weighting is mis-described (it up-weights rows the head widens); its effect is
  ≤ 1.1× and immaterial.
- [minor] The head is nearly constant (log-range s 2.36–2.94, 5th–95th; corr. with log q 0.2).
- [minor] R5 and R6 are stale (scalar form, bound 2, term cap 100 still described first).

## TMA geometry: approve-with-findings
- Confirmed: E's median course error 14.6°; 0.338 > 30° (settled 0.235, unsettled 0.643); no
  mirror-course concentration (2% in 150–180°); 30+ km worst is physical (low bearing rate).
- [major] **Course coverage is largely vacuous:** for 52.8% of the head's rows (41.6% of the
  temperature's) the 95% course interval covers the whole circle; on the rest coverage is 0.857
  (head), 0.826 (temperature). Median stated course sd 101° (raw 5.5°). "Reaches 95% marginal
  coverage" overstates.
- [major] "Segmentation wrong mid-manoeuvre" misreads the unsettled slice: it is defined from the
  truth, and the oracle (true segmentation) also fails there (within-95% 0.635, median course
  error 27°). Much of it is physical manoeuvre lag; only part is E's segmentation.
- [major, follow-on] A heavy-tailed predictive would pass χ²₄ without giving the operator a usable
  statement. Better: (a) calibrate on observable rows only, with an explicit "manoeuvre suspected
  / course undetermined" flag driven by a causal proxy; (b) report course as a circular
  distribution or as undetermined, never a Gaussian sd above 90°; (c) a mixture only for the
  unsettled component, weighted by E's own change evidence.
- [minor] Say why course binds (least observable on short or low-bearing-rate legs).

## Reproducibility: approve-with-findings
- Decision (a34e1c5) before training (the training ran at a34e1c5, clean tree, plan
  `fdf7987e…`, E weights `a5485318…`); caches and baseline before the decision, as the spec
  allows (frozen-E features, no calibration fit). Digests all match. cal-s3, temp and
  cal-shuffled-last rebuilt byte for byte at d9962b7; `validation.json` reproduces byte for byte.
- [minor] Calibrated-file headers do not carry g3predict's own commit and dirty flag (only the
  hand-written `run.json` does); cal-shuffled-last's header names the model `cal-shuffled`
  (weights digest distinguishes it); `validation.json` has no producing commit or CPU.
- [minor, methodology] An in-sample temperature was fitted on tuning ordinals 0–499 before the
  decision (disclosed as forecast evidence), and the form change and the G3-b amendment followed
  it. No *fitting* touched the scoring ordinals; design choices (the form and bound) did use their
  baseline (see the README's process notes).

## Red team: approve-with-findings
- The failure is real: cal-s3 rebuilt exactly from cache and weights on all 3,934 rows; cache and
  prediction keys unique and fully matched; no fitting on scoring rows (training and the
  temperature used ordinals 0–499; design choices used their baseline); under the original G3-b
  (median NEES ratio) the head fails worse (0.15).
- [major] "Learned something per row" is not supported: with each estimator's log-range sd shifted
  by its best global factor, IS95 is 2.264 (head), 2.271 (shuffled), 2.335 (temperature); the
  shuffled head also beats the temperature on NLL (12.92). Discrimination AUC 0.60 (head), 0.56
  (shuffled), 0.53 (temperature). Little per-row learning is shown.
- [major] Course coverage largely vacuous (as TMA geometry).
- [major, process] The local form and bound 4 were chosen from evidence on the *scoring* rows
  (`g3-base-val`, ordinals 500–1499); the README says tuning rows (true of the cap only). The bias
  runs toward passing and the gate failed, so the outcome is unaffected; the write-up must say so.
- [minor] The β-weight acts on the head only (constant per cell for the temperature).
- [minor] The SRD Gate 3 row still describes "a learned scale e^(2s)".
- [minor] The cache and the prediction file come from different g2predict runs (segmentation
  digests differ; rows agree to 1e-6); say so.
- [minor] The carried-seed rule ranks seeds on the scoring ordinals (registered; harmless here).

## Response (for round 2)

Every major is a correction to the record's account; none changes the outcome. The README is
amended (§ "What the record shows" replaced; course coverage restated; the unsettled slice
re-described; the per-row learning claim withdrawn; the scoring-row provenance of the form and
bound disclosed); research R5/R6 are made current; the follow-on is re-proposed along the
numerics and TMA findings (correlation shrinkage, exact-error training, circular course,
observability gating) instead of a heavy-tailed predictive. The minors on file headers and the
SRD wording are carried as follow-ons (spec 009), listed in the write-up.

# Round 2

The four reviewers with majors were asked whether commit 1b96939 closes them. **No reviewer
rejects; no blocker or major is open. The stop at validation is decided by the panel.**

- **Statistics: approve.** All four findings closed (the README's mechanism now matches the
  arrays; the per-row learning claim is withdrawn; missing-row charge disclosed). New [minor]: the
  best-global-factor comparison is fitted in sample on the scoring rows; label it a diagnostic
  (done).
- **Numerics: approve-with-findings.** All five closed. New [minor]: the β-weight docstring in
  `calib/loss.py` still said the opposite of the code (corrected).
- **TMA geometry: approve-with-findings.** All five closed. New [minor]: the follow-on lives only
  here, while `decision.json` and the SRD §5 row still name a heavy-tailed predictive as the
  default; the write-up and spec 009 must state the replacement (done in the write-up: circular
  or undetermined course, never a Gaussian sd above 90°; a causal proxy for the settled slice).
- **Red team: approve.** All three majors closed; SRD wording carried to spec 009. New [minor]:
  "scoring ordinals were not touched" contradicted the disclosure that design choices used their
  baseline (qualified above).
- **Reproducibility** (minors only in round 1): carried to spec 009 (g3predict headers carry
  their own commit; distinct model names for best and last; producing commit in validation.json).

## Decision

Gate 3 stops at validation; seed 320 is not generated. The carried estimator stays E with its
points unchanged; its raw covariance is not to be presented as an uncertainty. The follow-on is
re-proposed (`site/blog/2026-11-08-gate-3.md`) and replaces the decision record's heavy-tailed
default: circular or undetermined course, observability gating by a causal proxy, correlation
shrinkage and training on exact errors; a heavy-tailed component only for manoeuvres.
