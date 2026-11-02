# Gate D validation stop: agent review panel

The panel had five independent, read-only reviewers: TMA geometry, estimation and numerics,
evaluation statistics, reproducibility and red team. Each was briefed on the committed record
(`README.md`, `validation.*`, `gd/`, the models and the decision record) and on the code. Each
returned a verdict and findings tagged [blocker], [major] or [minor], with evidence. Their
scratch scripts are not part of the record. The findings below are condensed from their reports;
the numbers are theirs.

# Round 1

All five reviewers returned **approve-with-findings**. None rejected, and none raised a blocker.

## Statistics: approve-with-findings
- [major] The Gate 2 segmenter's operating point is unstated. The 0%-matched CUSUM/GLR thresholds are silent comparison artefacts (CUSUM h 1.44e6, 1 detection; GLR h 2.27e5, 0 detections). Name the Gate 2 setting or defer it; the 5% figures from the docstrings are available.
- [minor] FR-035 (2) was wrong: a detector that never alarms did not fail D-miss, because the controls tuned to its 0% rate went silent too. At a 0% matched rate D-delay and D-miss are degenerate. Lesson: set a floor on the matched rate.
- [minor] gd-cls scores 1.267, inside the causal range 1.193–1.273, so the downstream loss shows no benefit; the README should say so.
- [minor] "0.95× least squares" is a point estimate only; give an interval or word it as a point.
- [minor] The no-skill evidence is weak: the in-span maximum is bounded by the scenario maximum, so that comparison proves little. Use an AUC, or recall at a matched 0.28% beside the IMM's 7.5%.
- [minor] Recall ranges: causal 0–7% (s3 is 0), time-late 1–11%. `verdict.json` "fail" omits the split. The controls are in-sample on validation.
- Rules applied as registered; the carried seeds are causal s1 and time-late s2; D-miss "inconclusive" is correct; D-gap and the ratio arithmetic check; held-leg rows equal settled rows (7,620).

## Reproducibility: approve-with-findings
- Provenance checks out: decision 785bfef is an ancestor of the training commit 38b1215 and the validation commit 501907b; the plan digest is 305d3216…; all 7 weight files match their digests; the validation file digest matches; the amendment digest matches the manifest.
- Re-running gd-causal-s1 on the full validation split gives byte-identical detector outputs (2f29d0d5…, gz e2f2aad8…) and byte-identical detection records (909677ab…). The highest p_change over all 10,000 scenarios is 0.219.
- [major] gd/manifest.json says git_dirty true. Likely cause: gd_validation writes work/, amendment.json and validation.json into the parent folder, and Experiment excludes only the gd/ subfolder. Explain it in the README and fix it for the next gate.
- [minor] The baseline and downstream predictions are kept only as digests; add a quickstart to regenerate them.
- [minor] Weights were trained on mixed CPU families (Xeon 6973P, EPYC 7763), so they are not byte-reproducible; reproduce by re-scoring.
- [minor] verdict.json contains bare Infinity, which is not strict JSON.
- [minor] The claim "never reached 0.5 on any row of all seven detectors" is confirmed only for causal-s1; narrow it or cite each detector's maximum.

## TMA geometry: approve-with-findings
- [major] The detector learned a prior over time in the window and reads no bearing evidence.
  - AUC of now against held rows: 0.867 at σ 1°, 0.873 at σ 2°.
  - Median p by row type: held rows before the first manoeuvre 0.0006, held rows after a manoeuvre 0.048, now rows 0.049.
  - AUC against held rows after a manoeuvre: 0.528. A time-since-zig baseline alone reaches AUC 0.83.
  - The per-span maximum is flat across quartiles of Δḃ = |Δv⊥|/R (0.0506 → 0.0511).
- [major] Not "intrinsically undetectable".
  - The time-late variant fails the same way (maximum 0.072; AUC 0.27 against held rows after a manoeuvre).
  - The SNR proxy Δḃ·(duration + 60 s)/σ has median 1.37, and 24% of spans exceed 3, so a calibrated 60 s posterior ≥ 0.5 is structurally rare.
  - The top quartile should still register, and does not: this is a learning/representation failure on top of a near-unreachable threshold.
- [minor] The IMM's 7.5% at μ>0.5 is a lower bound. With the threshold swept (500 scenarios): ≈0.3% false alarms detects 18%, 1% detects 29%, 5% detects 48% (cf. the GLR's 57% at 5%).
- [minor] FR-035 (1) is wrong for the time-late variant: with no knots it fits one leg across later manoeuvres, which is worse than least squares by construction. Its knots look spurious (28 of 160 within 60 s of a boundary; weights rise with row). Causal last-row knots: 96 of 209 within 60 s of a boundary.
- [minor] Labels and rows are sound (one-row offsets sit inside the tolerance). Say explicitly that the A.6 branch is read as a fail, as gitma did.

## Red team: approve-with-findings
- Not a pipeline error.
  - The training stream (generate_indices) and validation pack (batch_from_pack) are bit-identical on 200 scenarios: samples, zig, sigma, spans, n_tm, tm, t, mask, own, bearing, valid.
  - gd-causal-s3 exports no knots and reproduces least squares: 0.1212 against 0.1210.
- Detection skill, 400 validation scenarios:
  - gd-causal-s1: p_change maximum 0.165; AUC after the zig 0.54, now vs held 0.59; mean p 0.047 on now rows against 0.043 on held rows after the zig. Its pooled AUC of 0.80 is all timing: mean p before the zig is 0.0012.
  - [major] The downstream loss (about 26) swamps the classification terms (about 0.6). gd-cls ranks better: AUC 0.68 after the zig, 0.74 now vs held; w_change AUC near boundaries 0.89 against 0.75 for s1. Even gd-cls never exceeds p 0.19.
- [major] The time-late now head is at or below chance (AUC 0.45 / 0.48, maximum 0.072) despite seeing the future: an optimisation failure, not an information limit.
- [major] The 0.5 thresholds are close to unreachable by construction:
  - the now label is positive only in the span plus 60 s (base rate 10% after the zig);
  - rows from the span end to end + 300 s are labelled 0 with weight 1, though matching credits detections there;
  - the held-leg weight 3 cuts the odds about 3×, so p 0.5 corresponds to a true probability of about 0.75;
  - the triangular w_change targets keep peaks below 0.5 (gd-cls near boundaries: 99th percentile 0.40, maximum 0.47).
- [minor] The pooled ECE includes pre-zig rows; report ECE after the zig, or drop "calibrated".
- [minor] s1 and s2 hit the 20-epoch cap with best epoch 17 and the loss still falling: under-trained.
- [minor] The detection comparisons are degenerate (silent against silent).
- [minor, not run] Soft against hard segmentation downstream: worth running on a quiet machine. Script: /tmp/claude-0/panel-red/soft.py <model> <N>.

## Estimation/numerics: approve-with-findings
- No training bug. gd-cls reproduces val 0.6113. Labels are aligned (389 of 389 spans). Padded rows are masked. The downstream term is correct (CRB-normalised, keeps 96–98% of rows, implicit gradient reaches c and s).
- [major] "Calibrated" is wrong. The now-label rate is 0.0456; mean p is 0.027 (gd-cls) and 0.022 (s1). Observed frequency is 1.6–2.0× p in every bin, and ECE 0.02 is half the base rate. The held ×3 weighting deflates p, so p ≥ 0.5 needs a true probability of about 0.75.
- [major] The downstream term takes over the shared encoder.
  - Encoder gradient norm by term: downstream 15.2, now 0.016, boundary 0.31, kind 0.08. Clipping at 1 scales steps by about 1/15.
  - s1's classification is worse than a constant predictor (boundary 0.261 against 0.200; kind 0.432 against 0.430). Its now AUC after zig + 120 s is 0.506.
  - Soft w_change at scored rows: median maximum 0.014, 90th percentile 0.19, 4.7% of rows reach 0.5.
  - Downstream loss on 128 rows: 35.7 untrained (≈ least squares), 27.7 with soft knots, 32.0 with knots exported at 0.5. About half the soft gain is discarded by the hard export (registered FR-014/FR-027, not a bug).
- [major] gd-cls against constant baselines, BCE: now 0.0657 against 0.0894; boundary 0.1279 against 0.2003; kind 0.4177 against 0.4298; total 0.611 against 0.720. Its now AUC after zig + 120 s is 0.649, while a time-since-zig rule scores 0.664. gd-cls stopped on patience while still improving.
- [minor] A 0.5 threshold on BCE against ±60 s triangular targets is reached only when timing is certain; gd-cls recall is 0.15%.
- [minor] Recall: causal 3.2 / 6.9 / 0.0%, gd-cls 0.15%, time-late 1.1–11.1%.
- [minor] Check whether a logit ceiling caps p at 0.19. CHECKED: no ceiling. Maximum logit −1.79 / −1.52 / −2.10 (p 0.143 / 0.179 / 0.109) on 200 scenarios, against a bound of about 11; 47–69% of hidden units saturated.

## Response to round 1

All findings were accepted. None changes the verdict.

- **Attribution (TMA [major], numerics [major] ×3, red team [major] ×3, statistics [minor]).**
  The README's "why" section was rewritten with the panel's evidence:
  - the AUCs after the zig and against held rows after a manoeuvre, and the time-since-zig
    baseline;
  - the flat response across quartiles of manoeuvre signal, and at σ = 2°;
  - the time-late variant at chance;
  - the encoder gradient imbalance (15.2 against 0.016);
  - the soft-versus-hard segmentation losses (35.7 / 27.7 / 32.0);
  - gd-cls against constant predictors;
  - the threshold and label design: end + 300 s rows trained as 0, held-leg weighting, a ±60 s
    triangular BCE.
  "Calibrated" was replaced by "deflated". The result is now described as a learning failure on
  top of near-unreachable thresholds, not as an information limit.
- **Logit ceiling (numerics [minor]): checked, not a ceiling.** The maximum logit is −1.79 /
  −1.52 / −2.10 (p 0.143 / 0.179 / 0.109) for s1, gd-cls and s2 on 200 scenarios, against a bound
  of about 11.
- **Gate 2's segmenter operating point (statistics [major]).** The README now says the matched
  thresholds are Gate D comparison artefacts, and that the next spec declares the operating point.
  The 5%-rate GLR (57% of spans) and CUSUM (10%) figures from R6 are quoted. The IMM's
  7.5% is reported as a lower bound, with the TMA reviewer's sweep (18% / 29% / 48% at ≈0.3% / 1% /
  5%).
- **FR-035 (1) and (2) were wrong (TMA [minor], statistics [minor]).** Recorded in the README,
  with the lesson for the next detector gate: a floor on the matched false-alarm rate, or a
  declared operating point.
- **A.6 branch (TMA [minor]).** The README now states that the validation stop is read as a
  fail, as gitma did.
- **git_dirty (reproducibility [major]).** The cause is explained in the README and fixed:
  `scripts/gd_validation.py` now runs `tma2-gd` with the record's own folder, which `Experiment`
  excludes from the dirty check. This committed record keeps the flag. Its byte-identical re-run
  is the evidence that it is harmless.
- **Strict JSON (reproducibility [minor]).** Fixed for future records: `Check.as_record` names
  non-finite values in the detail, and `metrics.json` writes them as strings. There is a test.
- **Wording (statistics and reproducibility [minor]).**
  - Recall ranges are corrected.
  - "Never reached 0.5" is narrowed to what the record shows, plus the panel's full-split maximum
    of 0.219 for s1.
  - "0.95×" is stated as a point estimate.
  - The control results are in-sample.
  - The verdict's split is in `metrics.json` (`split: validation`) and in the README title.
- **Reproduction (reproducibility [minor]).** The README says to reproduce by re-scoring the
  committed weights, and that the baselines are pinned by digest and regenerated by
  `gd-validation.yml`. Committing those prediction files (about 100 MB gzipped) is not done.
- **Under-training (red team [minor]).** Recorded: s1 and s2 stopped at the epoch cap with the
  loss still falling.
- **Soft-versus-hard downstream on the gate's rows (red team [minor, not run]).** The numerics
  reviewer's 128-row figures answer the question at the level the record needs. A full run is
  left to the follow-on.
