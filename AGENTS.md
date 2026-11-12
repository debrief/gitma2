# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

**gitma2: TMA via ML, second attempt.** Can a learned component, trained end to end with explicit
bearing geometry, match batch least squares wherever the constant-velocity model holds and beat a
tuned IMM wherever it does not? It starts from [debrief/Gitma](https://github.com/debrief/Gitma).

- Principles: `.specify/memory/constitution.md` (v1.3.0). Plans MUST pass its checks.
- Research and the owner's decisions: `docs/research/` (notes 01–10; decisions in 04 §6 and 10 §6).
- Requirements: `docs/SRD.md` (draft), `docs/SRD-annex-A.md` (steady-leg detector, Gate D; §A.9 Gate S) and `docs/SRD-annex-B.md` (the owner's requirements for ownship and target manoeuvres and steady-leg segmentation, 2026-11-04). Read them before planning any feature; where this file and the SRD disagree, the SRD wins.

## Spec-driven workflow (GitHub Spec Kit)

Spec Kit is installed (`.specify/`, skills in `.claude/skills/speckit-*`). Feature work follows
`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-analyze` → `/speckit-implement` → `/speckit-report-slides` → PR.
`/speckit-specify` ends with `/speckit-report-kickoff` (hooks in `.specify/extensions.yml`; see
Reporting below). Specs live under `specs/<NNN-feature>/` and cite the SRD section(s) they implement. Done: 001 (types and
generator), 002 (references, physics layer, ONNX harness, P0; **P0 passed**, panel round 3,
`experiments/20261101-p0-r4/`). 003 (Gate 1, constant velocity): **Gate 1 passed** (panel round 2,
`experiments/20261101-g1-a-g1/`), but only because the model reduces to batch least squares: the
heads died in training, so learning is untested until Gate 2 (prerequisites in
`specs/003-gate1-cv/tasks.md`). Workflows: `train/<plan>`, `validate/<run>`, `gate/<plan>`,
`report/<gate run>`. 004 (steady-leg detector, Annex A): **Gate D stopped at validation**
(panel round 2, `experiments/20261102-gd-a-val/`). The detector raised no alarm: its p_change
reads only time since the zig. Downstream it scored 0.95× batch least squares but 1.21× the IMM,
and the time-late variant failed. Test seed 305 is unscored and reserved. Annex A §A.6 applies:
publish, and Gate 2 uses the CUSUM/GLR segmenter at an operating point its spec declares
(recommended: GLR at a 5% held-leg false-alarm rate). Write-up: `site/blog/2026-11-02-gate-d.md`.
Detector workflows: `train/gd-a`, `validate-gd/<run>`. Research note 08 (leg-detection spike,
validation only) recommends GLR + physics-layer confirmation as the interim Gate 2 segmenter.
005 (steady-leg segmentation, Gate S; Annex A §A.9, owner merges): implemented and scored. Components O
(ownship), C (classical target segmenter, the reference) and L (learned, starts equal to C); fresh
test seed from 312. Planned (`specs/005-steady-leg-segmentation/plan.md`): measured on validation,
an additive leg search is far weaker than GLR + confirm (F1 0.65 vs 0.79), so C confirms
nominations from both by the coupled physics-layer cost on each nomination's own prefix. Owner
decision 2026-11-04 (Annex B, SRD §9): the simulation changes to the owner's manoeuvre model
rather than the thresholds to the simulation. Generator 0.6.0 (MAN2: target legs 10–40 min, bell
shaped; 40–120 min windows, 720 rows; wander; slower turns; scoping in `docs/research/09`) is
spec 006 (`specs/006-generator-man2/`) and precedes Gate S: implemented (PR 13); **G0-MAN2
passed** (panel round 2, `experiments/20261104-g0-man2-r2/`, CLI `tma2-g0-man2`; two owner
amendments after results: check-4 coverage and the throughput method). Seeds: 314 validation
(`data/man2-val`, digests in `experiments/20261104-g0-man2/dataset-digests/`), 315 test (Gate S;
generated at a38f61b after the decision record; now used), 316 noise-free, 317 L's training
stream; 312/313 unused; the next fresh seed is 318. IMM/EKF re-tune on 314: `tune/**` branches
run `.github/workflows/tune.yml` (results to `results/man2-tune-<run id>`); frozen
`imm-cv0.03-ct1-w0.01-s0.0003-p4-r2`, EKF `ekf-sa0.00003-p4-r0.03125`
(`experiments/20261104-man2-refs/`). Gate S: decision `experiments/20261104-gs-decision/` (plan
`configs/segment/gs-plan.json`; carried L = seed 3, `carried.json`), L training on CI
(`segtrain/**` → `.github/workflows/segtrain.yml`, validation `experiments/20261105-segL-val/`),
test segmentations on CI (`segment.yml` plans `configs/segment/gs-test-*.json`;
`glr-confirm/**` for the reference), scoring `tma2-gs ... --decision --plan --split test`.
**Gate S scored** (record r2 `experiments/20261105-gs-r2/`, after panel round 1 rejected r1 for a
causality bug in C's open-transition start, fixed in 7fe8874; decided by panel round 2): S1–S3 pass,
S4 inconclusive (L − C gap recovered +0.0012 [−0.0031, +0.0049]); C recovers 0.898 of the
one-leg-to-oracle gap (0.838 on the rows every estimator answers: one leg and the IMM fail on a
quarter), GLR + confirm 0.143. Follow-on (FR-072; inconclusive counts as not
passed): C is Gate 2's segmenter and control; learning recorded as not shown. Scoring runs on CI
(`score/**` → `.github/workflows/score.yml`, plans `configs/score/`). Before Gate 2 (C fixes done on the branch after PR 15: monotone cost tables, no overlap
through open transitions, `open_handover` parameter, `code_sha256` in headers; schema 0.24.0;
the open-transition convention is chosen on validation): fix the
search's cost-table fit failures (`segment/search.py` warm starts; check monotonicity on the
validation tables), bind the segmenter's code commit in segmentation headers (the digest binds
parameters only), fix one open-transition hand-over convention (the main lever: C recovers 0.66 of the gap on
rows open at k against 0.91 elsewhere, and S4's whole L − C difference sits on those rows), stop
transitions overlapping through open ones (`_free` treats an open transition as [s, s + 1]), and
take a fresh test seed. Owner decision 2026-11-05: a learned nominator, or evidence trained
through confirmation, is tested within Gate 2, not as a separate gate. Write-up:
`site/blog/2026-11-05-gate-s.md`.
007 (Gate 2 on MAN2, `specs/007-gate2-man2/`; SRD amendment G2-d in PR 16, merged by the owner):
E = E-s (spec 005's evidence shifting C's confirmation threshold, trained on decision tables,
`tma2-dtables`) then E-w (per-bearing weights and a start correction on C's hand-over, physics
layer with 12 knots); `tma2-g2train {tables,train,es}`, `tma2-g2predict`, `tma2-g2` (tma2-gs
scoring with `--predictions`, `--knots 12`). Workflows: `segment/**`, `dtables/**`, `g2train/**`,
`g2predict/**`, `score/**` (kind `g2`). C frozen at code `4d2c084f…` (parameters `60e6ee63…`,
hand-over `knot_at_k`); decision `experiments/20261107-g2-decision/` (plan `configs/gate2/g2-a.json`
`6092c364…`, never edited). Training run 42352638177; validation `experiments/20261107-g2-val/`
(carried e-s3, `carried.json`); **test record `experiments/20261107-g2/`: G2-a to G2-d pass, E − C
+0.025 [+0.018, +0.031]** (seed 319, 4,983 scenarios). Panel round 1: two majors (E-s ≈ a zig veto,
E-w ≈ a fading memory), answered by pre-registered classical controls C′, fade and C″
(`experiments/20261107-g2-veto/`, model kind `veto` in `tma2-g2predict`, plans
`configs/gate2/g2-a-{veto,fade}.json`). **Decided by the panel, round 2: G2-a to G2-d pass**;
on test the classical C″ (zig veto + fixed fade, nothing learned) − C is +0.018 and E − C″ +0.007
[+0.001, +0.012] (learning beyond the rules, small; E-s adds nothing shown beyond the veto).
Write-up `site/blog/2026-11-08-gate-2.md`; recommended follow-on: carry E, keep C″ as a standing
control, spec 008 uncertainty calibration with the panel's follow-ons (`specs/007-gate2-man2/tasks.md`).
`scripts/research/g2_paired_gaps.py` gives paired gap differences between any two scored
estimators. Seeds: 318 training stream, 319 test (used); the next fresh seed is 320.
008 (uncertainty calibration, Gate 3, `specs/008-uncertainty-calibration/`; done; time-late E-w:
no gain over causal, `experiments/20261108-g3-timelate/`): every
prediction row states its covariance (`cov_xyvv`, `cov_ok`, sds of log range, course and speed;
schema 0.27.0), the scorer measures coverage, NEES, interval score and sharpness
(`calibration.json`, `cal_<name>` in `errors.npz`), and `--reuse <errors.npz>` skips re-solving.
A calibration head (`src/tma2/calib/`, `tma2-g3train`, `tma2-g3predict`) scales E's covariance by
e^(2s) on cached features (`tma2-g2predict --features`); control: a per-slice temperature. Gate 3
criteria in `tma2-g3` (proposed in an SRD amendment; plan `configs/gate3/g3-a.json`, draft until
the decision binds it). Time-late E-w: `configs/gate2/g3-timelate.json`. **Gate 3 stopped at
validation** (decision `experiments/20261108-g3-decision/`, plan `fdf7987e…`; record and panel
round 2 `experiments/20261108-g3-val/`): G3-a inconclusive (course coverage largely vacuous: the
95% course interval is the whole circle on half the rows), G3-b 0.835 against 0.92 (kept
near-singular correlations; linearised training errors), G3-c head worse than the temperature,
no per-row learning shown; seed 320 not generated (still unused). E's raw covariance is
overconfident (95% coverage 0.60) and must not be shown as an uncertainty. Follow-on (write-up
`site/blog/2026-11-08-gate-3.md`, spec 009): circular or undetermined course, observability gating
by a causal proxy, correlation shrinkage, training on exact errors. The next fresh seed is 320.
009 (usable uncertainty, Gate 4, `specs/009-usable-uncertainty/`; owner chose the probabilistic
course): E's rows state course as an arc ±X (≤ 45°) with probability P (von Mises + uniform
mixture, P through an isotonic map) and range/speed 95% half-widths (schema 0.30.0 fields
`course_arc_rad`, `course_arc_prob`, `course_conc`, `course_mix_p`, `range_ratio_q95`,
`speed_q95_mps`). Code: `calib/statement.py`, `calib/statement_fit.py` (head and the sd^β
temperature, β per quantity from a grid), `tma2-g3train statement|statement-temperature` (CI
`g4train/**`), `tma2-g4predict`, scorer statement columns 9–14 in `eval/calibration.py` (9-wide
arrays widened on `--reuse`), criteria `calib/gate4.py` and `tma2-g4`. Baseline
`experiments/20261108-g4-base-val/`; decision `experiments/20261108-g4-decision/` (plan
`configs/gate4/g4-a.json` `e357f8a7…`). **Gate 4 stopped at validation**
(`experiments/20261109-g4-val/`, panel round 2): carried st-s3 missed G4-b's top bin (+0.054
against 0.05; the isotonic map caps P at 0.677); G4-c, G4-d (head − temperature −0.235) and G4-e
pass, G4-a speed inconclusive. P is honest on average but not on unsettled rows (stated 0.62, hit
0.30), and 72% of the head's margin is reproducible by a quadratic rule in E's three log sds.
Write-up `site/blog/2026-11-09-gate-4.md`; follow-on spec 010 (one self-consistent course
probability, slice-gated reliability with a causal unsettled proxy, interval-based bin checks,
cross-sd and encoder-only controls registered first). Seed 320 still unused.
010 (headroom under bearing-error mismatch, Gate H, `specs/010-headroom-mismatch/`; owner decision
2026-11-09, `docs/research/10-reflection-headroom.md`; planned and tasked, not implemented; owner
fixed the 10% materiality threshold and accepted the severity grid, `research.md` R2; headroom is
gated with both sides on the true segmentation, R6): no learned model.
Generator gains correlated, biased, unknown-σ and outlier bearing errors (mismatch off must
reproduce 0.6.0 byte for byte); C″, a classical robust control and the references are scored
against an attainable ceiling (true segmentation and error model, not its realisation). Material
headroom after the robust control: train under mismatch; none: stop the learning track and
publish. The Gate 4 follow-on is set aside. Seeds: 320 tuning, 321 validation, 322 test; seed 314
is retired from tuning. After Gate H: the scaled end-to-end regressor control (note 04 option B)
on Modal's free credit, once the owner has set up the account and secret.
Implemented so far (PR 25, steps 1–3): `sim/mismatch.py` (overlay from its own stream;
`run_kernel(..., mismatch)`; `tma2-generate --mismatch configs/gateh/conditions.json#<id>`; truth
side file `<split>.mismatch.npz`), `src/tma2/headroom/` (`cov`, `gls` the whitened layer, `estimators`
the ceilings and the robust control, `crb`, `gate`), `tma2-hpredict`, `tma2-gh`, workflow
`headroom/**` → `.github/workflows/headroom.yml` with plans `configs/headroom/`. Draft plan
`configs/gateh/gh-draft.json` (tuning only). Schema 0.31.0. Gate H is not yet registered.
Steps 1–3 done on tuning seed 320 (never a gate result): all 16 conditions
(`experiments/20261109-gh-tuning/`: on the primary condition the robust control is within about
1.5% of the attainable ceiling; outliers are the only kind that hurts the plain solve badly and
Huber removes it; correlated error and bias hurt the ceiling as much as everyone), the control's
grid (`experiments/20261110-gh-grid/`: Huber constant 2.0, no shrinkage), references re-tuned
(`experiments/20261110-gh-refs/`, workflow `tune-h/**`: IMM unchanged, EKF
`ekf-sa0.00003-p4-r0.5`). Next: register Gate H (SRD §5 row, owner merges; H-b needs a form the
sample size can decide; H-a's band from the clean-data oracle's efficiency, about 1.57), then the
decision record, validation seed 321 and test seed 322.
Gate H registered (2026-11-10): SRD §5 row and §9 line in PR 25 (owner merges; H-b's form is
the owner's: point at most 5%, interval not wholly above 2%); plan `configs/gateh/gh-a.json`
(`26d8e898…`, never edited); decision `experiments/20261110-gh-decision/`. Seeds 321 and 322 are
generated in their runs only. Validation (`experiments/20261110-gh-val/`, seed 321, 16 conditions):
H-a and H-b pass. **Test record `experiments/20261110-gh/` (seed 322, 5,203 scenarios): H-c
R = −0.4% [−2.4, +1.4], headroom not material; decided by the panel, round 1** (`review.md`,
five approve-with-findings). What it supports is narrower than the SRD row: on the true
segmentation, under this stationary Gaussian-plus-outlier error family at these severities,
learning the bearing-error model for this solve is not pursued. The pooled zero is +4.9% under
10.7 km and −5.2% over 25.3 km (`range-bands.json`); the "ceiling" is an error-model-informed
fit, not a ceiling; both fits are about 1.25 × the known-manoeuvre bound and why is not
established (the chord explanation was tested and rejected). The robust control is kept: 12%
better than the plain solve under these errors, under 2% cost on clean data. Write-up
`site/blog/2026-11-10-gate-h.md`, slides `site/blog/2026-11-10-gate-h-slides.md`. Registered
comparison on C's segmentation (`configs/headroom/gh-val-c2.json`) run late, validation seed,
reported only (`experiments/20261110-gh-c2/`): **the mismatch's cost is in the segmentation**. C″
is 0.102 clean and 0.280 under the primary condition (0.230 with the robust control in its final
solve) against 0.114 for the robust control on the true segmentation; C recovers 0.92 of the
one-leg-to-oracle gap clean and 0.66 under mismatch. Not evidence for learning: C ran unchanged.
Recommended follow-on (owner may object): a robust classical segmenter (estimated σ and Huber
costs in C's own tests) as the control for that factor of two, then the scaled regressor.
Seeds: 320 tuning, 321 validation, 322 test (all used); 323 unused; the next fresh seed is 323.
011 (robust classical segmenter, Gate R, `specs/011-robust-segmenter/`; owner go-ahead
2026-11-10; specified, not planned): nothing trained. Diagnose which mismatch kind breaks C and
how (false transitions, misses, delay) on tuning seed 323; build C-r (C's own tests made robust
by classical means; C stays frozen); measure the share of the gap between C's segmentation and
the true manoeuvre times that C-r closes, each with the robust final solve (validation 324, test
325). What remains is the headroom for a better segmenter of any kind; C-r becomes the standing
control. The scaled regressor follows.
Diagnosis done (`experiments/20261110-gr-diagnosis/`): outliers, then correlated error, make C
declare false transitions (248 clean, 1,126 under all four); misses do not rise; bias and an
untold σ do nothing; true nominations do not help, so confirmation over-accepts. C-r is
`segment/robust.py` (Huber-cost confirmation over C's unchanged generator; C's digests asserted
in `tests/unit/test_segment_robust.py`), run by `tma2-hpredict --segmentation c2r
--robust-confirm`; `--segments-from` applies a clean split's segmentation (FR-003). Schema
0.32.0. Owner fixed R-b's 10% threshold. Pilot and yield plans: `configs/headroom/gr-*.json`.
**011 closed at tuning (owner, 2026-11-11): no Gate R.** On 150 engagements of seed 323
(`experiments/20261111-gr-choice/`; pilot `20261110-gr-pilot/`) the Huber test removed 28% of
false transitions and so did doubling C's threshold; no variant was separated, and by the rule
declared beforehand the robust test is not carried. A clean-data-quality segmenter would close
0.63 of the gap and still sit 43% above the true-manoeuvre reference (C″ is twice it on clean
data): misses, about 30% of true changes, are the larger part. C stays frozen, C″ standing;
seeds 324, 325 unused. Write-up `site/blog/2026-11-11-robust-segmenter.md`.
012 (scaled end-to-end regressor control, `specs/012-scaled-regressor/`; owner 2026-11-10: start
now beside 011, cap one month of Modal free credit, about 50 T4-hours; specified, not planned):
a direct sequence-to-state model, about 10^7 scenarios on the fly (seed 326 stream, 327
validation, 328 test; next fresh 329), read against the bound on held course (reaches < 1.25,
floor > 2.0) and against C″ after manoeuvres. A control, never carried. No GPU run before the
owner's account, spending limit and secrets `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` exist.
Owner 2026-11-10 (later): the budget is $50 in total (free credit plus up to $20), in dollars
not hours. Secrets exist and authenticate (`modal-check/**` workflow). CPU build done
(`src/tma2/regress/`, `tma2-rtrain`, `tma2-rpredict`, `scripts/modal_train.py`,
`gputrain/**` → `.github/workflows/gputrain.yml` with the ledger `regress/ledger.py`).
Throughput 635 scenarios/s on a T4 at about $0.66 an hour (`experiments/20261110-r-pilot/`);
decision record `experiments/20261111-r-decision/` (plans `configs/regress/r-a-*.json` bound by
digest; ledger cap 68 h). MAN2 has no held-course rows at the scored prefixes, so a fifth of the
stream and the held-course reading use `configs/regress/held-course-ranges.json` (research R8).
Readings: `tma2-rread`. In 012's scoring, also report C with a raised confirmation threshold.
Three seeds trained (38 T4-hours, about $26; `experiments/20261111-r-runs/`). Validation seed
327 (`experiments/20261111-r-val/`): held course 1.15–1.19 × the bound in range, 1.8 course, 1.4
speed (partial; least squares 1.01); after manoeuvres the regressor beats C″ (0.065 against
0.105, −0.042 [−0.051, −0.034]) and matches the true-manoeuvre solve in range; C at three times
its threshold is worse than C″ on that fresh seed. Test seed 328 and a held-out-ranges split
are scored by `rscore.yml` (`configs/rscore/r-a-test*.json`). Owner 2026-11-11: spending within
$50 is pre-approved; then GPU training paused (addendum 1 not run).
**Test record `experiments/20261111-r-test/`** (seed 328; relaunched after two runs stalled without
ever creating a job): held course partial on all seeds (range 1.13–1.16, course 1.75, speed 1.42;
worst in the best geometry); after manoeuvres the regressor beats C″ on all seeds (0.066 against
0.105, −0.039 [−0.045, −0.033]; forecast wrong) and on held-out ranges (0.114 against 0.151); a
tenth of the data loses little. **Panel round 1 (`review.md`): three approve with findings.**
Readings stand; narrowed to "a prior-informed, error-minimising estimator beats a prior-free fit in
median range": in course efficiency after manoeuvres it is worse than C″ (3.40 against 3.19), the
held-out split varies initial range only and the margin vanishes in its far quartile, and the
hedging explanation is withdrawn (a range prior is the leading candidate, untested). Control run
(`experiments/20261112-r-control/`, registered on validation first): C″ precision-weighted with a
range prior does **not** explain the margin (0.102–0.104 against the regressor's 0.066 on test), so
it is not simple shrinkage; the hedged-C″ control is not built and the margin's source is open.
Write-up `site/blog/2026-11-12-scaled-regressor.md`, slides `2026-11-12-scaled-regressor-slides.md`
(figures by `scripts/research/r_charts.py`). Spec 012 is done; about $24 of the budget is unspent.
013 (time-late, Gate T, `specs/013-time-late/`; owner 2026-11-11; specified, not planned): the
whole track over a period (position, course, speed at every moment, manoeuvre times), 5-second
bearings, periods cut at random from longer engagements; nothing trained: C″ read as a track, a
classical full-period re-test, the true-manoeuvre solve and a bound at every moment; the owner's
bearing-rate thinning idea tested (dropping, normal points, adaptive bins); headroom at 10%
decides whether a learned full-period proposer follows. Seeds 329 tuning, 330 validation, 331
test (324, 325 unused).
Build so far (`src/tma2/timelate/`: periods cut in memory, normal points, track read-out, whole-period
bound, `arc.py`). First checkpoint (`experiments/20261111-tl-diagnosis/`): the chord reference is
at 1.9 × the bound on cut periods (4.5 on whole engagements) because the layer gives a manoeuvre
four free unknowns. Owner 2026-11-11: add the arc-model solve (turn at a constant rate, speed
change at a constant rate; classical). On 60 tuning periods (`experiments/20261111-tl-arc/`) it
is at 1.2 (kind told) to 1.4 (kind judged) × the bound on true times, but worse than the chord
on C″'s own transitions: the segmentation is the larger factor (about 3 in median range error).
Full-period re-test on the arc cost (`timelate/retest.py`, `experiments/20261111-tl-retest/`):
no better than C″ read as a track. It reaches the cost of the true-times fit (median difference 0)
with a third of manoeuvres missed and 3 to 4 times the range error: the bearings do not separate
the structures, so a test of fit cannot reach the reference; prior knowledge of manoeuvres
(Annex B's statistics) is what remains. Owner 2026-11-11: classical prior first (`timelate/prior.py`, `retest.log_evidence`,
`experiments/20261112-tl-prior/`). Told only the basin (times free) the arc fit is at the bound.
**First reading withdrawn** (the evidence was evaluated at a bearings-only fit: thousands of
units of artefact). Corrected (fit to the posterior, `joint_fit(prior=...)`): where the re-test is
wrong the true history is ahead by over 3 in 0.5–0.6 of periods and behind in under 0.1; the
re-test's own history refitted with the prior is at 0.057 against C″'s 0.113 as a track
(1.99 [1.01, 3.11], 57 tuning periods); true history with the prior 0.027. About a third of the
wrong periods are genuinely ambiguous. Owner 2026-11-12 chose "write up and re-scope to candidate
tracks with probabilities" and lifted the GPU pause for time-late learning, on the first
(withdrawn) reading: the decision is back with the owner. Owner 2026-11-12 (on the corrected
evidence): continue classically; GPU held until the control exists. `timelate/search.py`
(`evidence_search`, `candidate_set`: histories scored by evidence, the best few with probabilities
as candidate tracks) measured on 99 fresh tuning periods (ordinals 60 onward;
`experiments/20261112-tl-search/`): 0.042 against C″'s 0.088 read as a track (2.12 [1.62, 2.96]),
as good started from nothing as from C″; true history with the prior 0.018; best of the top three
candidates in hindsight 0.028. The search is not the limit (its best history has evidence at or
above the truth's in 97 of 99); the evidence and real ambiguity are. Candidate probabilities are
not calibrated. Gate T tooling (PR 32): `tma2-tlsolve`, `tma2-tlscore`, `timelate/**` →
`.github/workflows/timelate.yml` with runs in `configs/timelate/runs/`, `timelate/run.py`,
`timelate/gate.py`, a shifted-prior split (`tl-shift-ranges.json`), one leg, IMM and EKF as tracks;
schema 0.34.0. **Gate T registered** (2026-11-12): plan `configs/timelate/tl-a.json` (`6f15a246…`,
never edited), decision `experiments/20261112-gt-decision/` (T-a soundness, T-b C″ ÷ search above
1.10, T-c the same above 1.00 under the shifted prior, T-d candidates, T-e headroom; temperature 3);
SRD §5 row proposed (owner merges). **Gate T stopped at validation** (seed 330,
`experiments/20261112-gt-val/`): T-a failed, range efficiency of the true-history reference 0.67
(0.28 on the shift split) against [0.8, 1.3]. Cause, tested on tuning data: the reference fit starts
at the truth and stays there on weakly determined rows (efficiency 1.05 where the bound is under
0.05, 0.27 from 0.05 to 0.2). Seed 331 not generated. Not gate results: C″ ÷ search 2.56
[1.78, 3.51], 1.70 [1.24, 2.27] under the shifted prior; candidates calibrated on Annex B data
(first right 0.61, stated 0.54) and badly overconfident under the shift (0.22 against 0.52). T-e's
headroom is overstated by the same fault. **Owner 2026-11-12: re-register and run again.** Second
registration `experiments/20261112-gt2-decision/`, plan `configs/timelate/tl-b.json` (`08793d8b…`):
the reference is the true history's structure fitted from neutral starts (`run.history_reference`;
`history-fixed` times held, `history-fit`, `history-map`); T-a reads `history-fixed` on rows bounded
below 0.05 (1.10 on tuning; with times free 1.43, because the bound assumes them known); T-d-shift
added (expected to fail); T-e against `history-map`; validation seed 332, test 331; schema 0.35.0.
Validation seed 332 (`experiments/20261112-gt2-val/`): **T-a passes (1.26)**; reported only: C″ ÷
search 2.41 [1.65, 3.02]; under the shifted prior 1.26 [0.89, 1.84] (would fail; 1.70 on seed 330);
candidates 0.62 in the first three, gap +0.06; shift gap +0.32; search ÷ reference 1.41
[1.19, 1.97]. The tuning seed's sub-bound middle band did not repeat (0.96). **Test record
`experiments/20261112-gt2/` (seed 331, 300 periods a split): T-a 1.05 pass; T-b 2.27 [1.76, 2.67]
pass (C″ 0.088, search 0.039); T-c 1.69 [1.39, 2.14] pass; T-d 0.71 in the first three, gap −0.03,
pass; T-d-shift +0.32 fail (forecast); T-e 1.46 [1.24, 1.91] material. Decided by the panel, round
1** (`review.md`, five approve with findings). Narrowed: the ratios are ratios of medians (paired
per period 1.68 and 1.53; the search is worse than C″ in about 30% of periods); T-b is mostly
smoothing with the arc model and prior, not finding histories (it wins where its history is wrong
too); T-c is seed-fragile (1.70, 1.26, 1.69) and does not isolate the wrong prior from busier
targets; the search under-counts manoeuvres (23% missed, 41% under the shift; invents one in 7 of
12 quiet periods); T-d passes on average only and at a 120 s match and temperature 3 only; under
the shift the candidates carry a rank and no probability; T-e is an upper limit (paired 1.17;
1.01 where the history is right); T-a would have passed the faulty reference. **Owed from spec
013, not run**: the owner's bearing-rate thinning study (FR-030/031), manoeuvre counts and timing
as outputs (FR-011), splits (FR-013), correlated errors (FR-003), whole engagements, a smoothed
IMM, quiet-target periods with a false-manoeuvre rate; and the controls (C″'s transitions refitted
with arc model and prior; flat-prior search). `prior.py` has three small recorded errors (leg
curvature counted twice, uniform-direction volume, leg normal not renormalised at its minimum),
not fixed: the code is registered. Panel's order: owed classical work, a prior-robust search with
a mismatch diagnostic, then a learned whole-period model registered against the search; the
follow-on is the owner's choice and no GPU run starts before it. Write-up
`site/blog/2026-11-12-gate-t.md`, slides `2026-11-12-gate-t-slides.md` (figures by
`scripts/research/gt_charts.py` and `tl_charts.py`). Seeds 329–332 used; 324, 325 unused; the next
fresh seed is 333.
**Owner 2026-11-12: follow-on is classical work first (spec 014), nothing trained, no GPU**: the
owed studies and controls above and the ambiguity share; a learned whole-period model is decided
after it.

## Stack (owner decisions, 2026-10-31)

Python 3.12 throughout: PyTorch models (from spec 003), NumPy/numba generator and reference
estimators, LinkML → Pydantic types, `uv`, `pytest`, `ruff`, `mypy --strict`. Training on free
4-core GitHub runners. Models export to ONNX (standard ops, fixed window, dynamic batch) with a
cross-runtime conformance test. Site and process as gitma: Docusaurus site, pre-registered
decision records, fresh test seeds, agent review panel for every gate.

## Repository layout

```
schema/tma.yaml            LinkML source of truth (carried from gitma, 0.16.0); README explains regeneration
src/tma2/
  types/                   generated Pydantic models + JSON Schema (scripts/gen_types.py), parse_record
  sim/                     prng (SplitMix64, xoshiro128**), geometry, ranges, scenario (numba kernel), generate
  data/                    canonical JSON (JavaScript number formatting), ndjson, f32pack, dataset, provenance, versions
  features/                batch: in-memory padded batches with per-timestep labels (prange over scenarios)
  references/              lsq, classical, naive, ekf, imm (ports of gitma's), crb (Fisher information)
  physics/                 reference.py (NumPy, documentation of record), layer.py (torch, exportable), segmentation
  eval/                    errors, slices, stats, metrics (+ efficiency), bootstrap, rows (settled, G5), predictions, experiment
  export/                  toy model and ONNX export (f64 conformance artefact, f32 reported)
  models/                  Gate 1: rows, model (encoder, heads, physics layer), loss, train, predict, export
  detect/                  Gate D: CUSUM/GLR controls, confirmation, matching, downstream (spec 004)
  segment/                 Gate S: O, C (nominate + confirm), L (evidence, crf, train, export), score, gate
  report/                  progress figures: track plots and error curves with provenance sidecars (tma2-plot)
  cli/                     tma2-generate, -solve, -track, -naive, -crb, -eval, -oracle, -p0, -train, -predict, -tune, -plan,
                           -gd, -g0-man2, -segment, -segtrain, -gs, -plot
conformance/onnx/          browser (WASM, Playwright) and Java legs of the export check
scripts/                   gen_types.py, data_dictionary.py, make_fixtures.sh, research/
tests/                     unit, golden, conformance (gitma fixtures), perf; fixtures/gitma/<name>/
specs/                     Spec Kit features
docs/                      SRD, Annex A, research notes
site/                      Docusaurus (welcome, glossary, generated data dictionary, process page, blog;
                           blog/_templates: kickoff and slides posts; static/slides/<post>/: reveal.js decks;
                           static/img/<post>/: committed figures with .json sidecars)
```

## Commands

```
uv sync                                   # Python 3.12 env with dev tools
uv run pytest -q                          # unit, golden, conformance, perf (~15 s after numba warm-up)
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run python scripts/gen_types.py        # after editing schema/tma.yaml; --check is what CI runs
uv run python scripts/data_dictionary.py  # site/docs/data-dictionary.md
uv run tma2-generate --seed <uint64> --count <n> --out <dir> [--ranges f --heldout-ranges f] [--noise-free] [--allow-dirty] [--format both|ndjson|f32pack]
uv run tma2-solve --in <split> --out <pred.ndjson> [--per-timestep]
uv run tma2-track --in <split> --out <pred.ndjson> --filter imm --sigma-cv 0.01 --sigma-ct 0.03 --sigma-omega 0.01 --switch 0.001 --p0-scale 4 --r-scale 8
uv run tma2-crb --in <split> --out <crb.ndjson> [--model full_window|known_manoeuvres|per_leg]
uv run tma2-eval --truth <split> --predictions <pred>... [--crb <crb.ndjson>] [--points 300,600] --out <dir>
uv run tma2-oracle --truth <split> --out <pred.ndjson> [--speed-prior] [--trivial] [--mask-turns]
uv run tma2-plot track --truth <split> --predictions <pred>... --labels a,b --scenario <i> --at 3600,5400 --out fig.svg   # also: errors
uv run tma2-p0 --experiment experiments/<id> [--oracle-data <dir with validation.f32pack>] [--gitma-imm <gitma tma-track output>]   # exit 3: gate not passed
uv run python -m tma2.export.onnx_export --out conformance/onnx/export
(cd conformance/onnx && npm ci && node wasm_leg.mjs --dir export/f64) ; uv run python conformance/onnx/java_leg.py conformance/onnx/export/f64
(cd site && npm ci && npm run build)      # site; prebuild regenerates the data dictionary
```

## Autonomy and owner input

The owner does not want to be the blocker. Agents make progress from the documents and ask only
where the documents say the decision is the owner's.

- **Decide and record.** Where the SRD, an annex or a decision record states a default (for
  example Annex A §A.8), adopt it, record it in the decision record or spec with a one-line
  reason, and proceed. Where no default exists, choose what a careful colleague would, state the
  choice and the alternatives in the PR description, and proceed; the owner can overrule on
  review.
- **Proceed between gates.** Specify → plan → tasks → implement → PR for every step of the SRD
  plan runs without asking. Gate verdicts come from the agent review panel, never from waiting
  on a human. A follow-on the SRD leaves to the owner is proposed in the write-up with a
  recommended default; if the owner has not objected by the time the next spec is written, the
  recommendation is adopted and recorded as such.
- **Merging.** An agent may merge its own PR once CI is green, a review agent (`/code-review`,
  or the panel for a gate PR) has approved, and the PR touches no owner-only item below. A PR
  that amends the SRD, an annex or the constitution is opened by the agent and merged by the
  owner; after two working days without objection the agent merges it and says so in the next
  write-up.
- **Owner-only** (ask, and wait): anything that spends money or needs a new account or secret
  (paid runners, cloud GPUs, external services); any change to the scope in SRD §1 or to the
  classification and mock-data rules; changing a gate's criteria after any result on that gate
  exists; deleting committed experiments, weights or result branches; publishing outside this
  repository and its site; anything the owner has said is theirs.
- **Ask well.** When input is needed, ask one multiple-choice question at a time with a
  recommended option first, do everything that does not depend on the answer beforehand, and
  never stop with nothing delivered.

## Reporting (constitution 1.3.0, owner decision 2026-11-08)

Two blog posts per task, where a task is a Spec Kit feature or a gate run. The practice page is
`site/docs/process/reporting.md`; templates are `site/blog/_templates/{kickoff,slides}.md` and
`site/static/slides/_template/index.html`.

- **Kickoff post** (`/speckit-report-kickoff`, run by `/speckit-specify`'s after-hook): written
  before implementation, from the spec. Where we are (the last gate's verdict, what is carried,
  what is open), where this task moves to (the SRD section, the criteria or acceptance, the plan
  in a few steps, the risks and what would make us stop) and how progress will be shown (which
  figures the slides post will carry). Smaller changes between tasks (fixes, CI repairs) append
  a dated paragraph to the current kickoff post rather than a post of their own.
- **Slides post** (`/speckit-report-slides`, run by `/speckit-implement`'s after-hook; a gate run
  does it after the panel decides): built *before the PR is opened*, so the PR carries it. A
  reveal.js deck at `site/static/slides/<date-slug>/index.html` (copy the template; reveal.js is
  loaded from cdnjs, pinned) embedded in the post with `<Slides slug="..." />`. Contents: an
  overview of the capability or fix, illustrated (a diagram or a figure per idea); a demonstration
  of progress with charts and track plots; what was not achieved; what comes next. A gate's
  slides post is the illustrated companion of its critical write-up and links to it.
- **Figures** are SVG under `site/static/img/<date-slug>/`, each next to the `.json` sidecar that
  `tma2-plot` writes (truth and prediction digests, scenario, command, code commit). A figure made
  by a script instead names the script and its commit in the post. Track plots: ownship blue,
  target red, each estimator's trail from the zig with its marker and 1-σ ellipse at the named
  times; rows before the zig are hidden because the layer's pre-zig states are undetermined.
  Keep each figure under about 200 KB; no raster images.
- **Data for figures** is seeded and regenerable: the demo split in a post names its seed, count
  and ranges file, or the committed experiment it came from. Never hand-edit a figure.
- A PR for a task without its slides post is not ready for review.

## Hard rules

See the constitution. In short: types once in LinkML; seeded randomness only; the reported
estimate comes from a declared physics layer; no result without naive, batch least squares, the
tuned IMM/EKF and the oracle ceiling on the same rows; efficiency (error / CRB) per slice; three
seeds per carried configuration; nothing above OFFICIAL, mock data only.

## Gotchas (learned in specs 001–002)

- The generator is a line-for-line port of gitma's `scenario.ts`: every PRNG draw, in gitma's
  order, including draws that are consumed and discarded. Changing the order breaks conformance.
- JavaScript semantics matter: `Math.round` is half-up (`js_round`), `%` is `fmod`, `Math.fround`
  + 0 maps −0 to +0 (`f32`). `canonical_json` formats numbers as `Number::toString` (integral
  doubles without `.0`, exponent thresholds 1e-6 and 1e21).
- Conformance fixtures under `tests/fixtures/gitma/` are gitma's output; never regenerate them
  from gitma2. `scripts/make_fixtures.sh` documents how they were made.
- Numba compiles on first use (several seconds); tests warm it up in `conftest.py`; CI warms it
  explicitly. The compiled cache lives next to the sources (`__pycache__`) and is gitignored.
- Throughput: kernel ≈ 20k scenarios/s; f32pack ≈ 2k/s; NDJSON ≈ 400/s (Python float formatting).
  Use `--format f32pack` for large datasets; NDJSON is for inspection.
- The reference ports keep gitma's arithmetic order, including explicit 4×4/5×5 loop products
  instead of BLAS (`@` on small matrices changes the last bits and the iteration path) and the
  IMM's finite-difference Jacobians. Agreement with gitma is 1e-7 typical, 1e-5 worst, flags exact.
- Export size: the Gauss–Jordan solve is one masked whole-matrix update per pivot; a row-by-row
  form made ~3,000 nodes per solve and onnxruntime took over 10 minutes to load the graph.
  Iterations are unrolled, so the conformance export uses 8; a deployable model needs an ONNX
  `Loop` over the iteration (spec 003).
- Physics layer export rules: no `torch.diagonal`/`diag_embed`/in-place slice writes (they export
  `If` or unsupported ops); no `torch.cos` or `torch.atan` in double (onnxruntime-web has no
  float64 kernels for them: use `cos_export`/`atan2_export`); no `Solve`/`Inverse` (unrolled
  Jacobi-scaled Gauss–Jordan instead); keep onnxruntime versions aligned across Python, web and
  Java (1.20's FusedMatMul is float-only).
- The physics layer must run in double: in float32 the damped solve's accept/reject decisions flip
  between runtimes (~1e-3 disagreement). The f32 export is reported, never the conformance artefact.
- Knot predecessors for the speed-continuity prior are counted among active knots only; an inert
  candidate between a turn's start and end knots must not become the end knot's predecessor.
- Physics layer gradients: never `sqrt` a quantity that can be exactly 0 and carries a gradient
  (masked rows, inert knots); use `safe_sqrt`. A single NaN there poisons every parameter of a
  model on the first backward pass (P0 panel round 1). Tests assert finite gradients everywhere.
- The layer tries several damping values per iteration (gitma's inner retry, side by side); with
  one trial per iteration it stops short on flat-valley rows. Compare it with *cold-start* batch
  least squares (`solve_batch` at row k): per-timestep rows are warm-started and can sit in a
  different minimum.
- Before the zig the layer returns finite, "plausible" states with range sd ≫ range: training
  and scoring must exclude or down-weight rows whose covariance says they are undetermined.
- Prediction caches in `tma2-p0 --work` are keyed by commit and reused only from a clean tree;
  `results.json` from the conformance legs must name the fresh export's SHA-256.
- Cramér–Rao bounds: `full_window` for held course, `known_manoeuvres` (times and kinds known) on
  manoeuvring data; `per_leg` is a diagnostic only. Efficiency is median(|e|/σ)/0.6745 per row.
- Model export (spec 003): the physics iterations are one ONNX `Loop` because the eager layer calls
  a TorchScript-scripted `iterate` while tracing. Inside the loop body, ONNX shape inference fails
  on zero-size tensors (no knots) and on lost ranks, so the CV path has no knot tensors and shapes
  are explicit. Write attention out (PyTorch's encoder layer casts masks to double, which the
  exporter refuses); no GELU (onnxruntime has no double `Erf`). Set the default dtype to the
  model's for `torch.onnx.export`: the scripted loop's scalar constants follow it.
- Experiments from a worktree: do not symlink `data` into it (`data/` in .gitignore matches
  directories, not a symlink, so the tree records as dirty); pass absolute data paths.
- Never time anything while another CPU-heavy job runs: torch's OpenMP threads oversubscribed by
  a parallel tune ran the physics layer 50–100× slower (48 s against 0.55 s per call; spec 004).
- Within one process, a second training run can differ from the first in the last bits
  (allocator state; 1e-16 in layer-norm weights); separate processes are byte-identical, so
  determinism and resume tests run each job in a fresh interpreter (`test_detector_train.py`).
- The known-manoeuvres Cramér–Rao bound has a numba port (`crb_known_manoeuvres_fast`, 0.4 ms
  per scenario against 8 ms) for the training loss; `Batch.tm` carries the generator's table.
- Generator 0.6.0 (spec 006): `GenerateOptions.generator_version` defaults to 0.6.0; anything that
  regenerates a 0.5.0 fixture must pass the fixture's version (P0's `check_generator` did not, and
  `tma2-p0` was broken from PR 13 until the G0-MAN2 run found it). Pack headers carry no
  timestamp, so data regenerated at the generating commit (a `git worktree` at
  `generator_git_commit`) reproduce byte for byte; at any other commit only the header differs.
- The toy model's ONNX digest does not change with its golden inputs: conformance legs must also
  record `inputs_sha256` (SHA-256 over `in_*.bin` in name order), or stale results pass.
- To time a gate check while a long job runs, pause that job (`kill -STOP` its processes, then
  `kill -CONT`); stopping a `run_in_background` job's processes ends its wrapper shell (exit 147),
  but the job continues after `CONT` and writes its own outputs.
- MAN2 zig legs: ~40% of engagements have no usable zig leg (zig inside a target change, or the
  leg ends within 5 min); single-leg fits on MAN2 data must use `eval.rows.zig_leg` and mask or
  cut the rows before it, or the one-leg solve runs away (range 1e11 m).
- Docusaurus MDX: no `{...}` in prose (it is a JS expression); `scripts/data_dictionary.py`
  escapes `<` and braces outside code spans.
- Provenance is read before any output is written: a CLI that checks `git status` after writing
  into an untracked experiment folder always records `git_dirty: true` (`tma2-gs` did, fixed in
  e648f8b). Workflows must keep downloaded tables and checkpoints outside the checkout
  (`RUNNER_TEMP`), or every job records a dirty tree.
- Container restarts kill local background jobs (several per hour on 5 Nov): run anything over a
  few minutes on CI (`score.yml`, `segment.yml`, `glr-confirm.yml`), not in the session.
- A segmentation is not a function of its scenario alone: the physics-layer batch is padded to
  the longest scenario in the chunk (`r_max`, CHUNK = 16 in `cli/segment.py`), and last-bit cost
  changes can flip a near-threshold acceptance (Gate S panel round 2: ordinal 25 alone differs
  from 25–26). Reproduce a CI segmentation with the plan's ordinals and shards.
- Never edit or commit in the checkout while a gate run reads it: provenance is read once at
  launch and modules load lazily, so a mid-run change goes unrecorded. Run long scorings from a
  `git worktree` at the commit (pass absolute data paths).
- An open transition's state is decided at acceptance: anything a later close refines (C's
  start polish) must not reach prefixes before the close (FR-002; `Transition.start_at`).
- onnxruntime has no double `Conv`: the evidence network exports each convolution as a MatMul
  per tap (`segment/evidence_export.py`, `MatMulNet`), checked against torch.
- Training with torch on 4-core runners: `set_num_threads(1)` per worker is faster for L's
  per-prefix CRF loss (24 ms per prefix) than 4 threads.
- Semi-Markov truth paths: several lattice paths can agree equally with the truth codes; take the
  lexicographic maximum on (agreement, zero-evidence score), or the CRF loss starts near 2,000
  nats from an arbitrary path (`segment/crf.py`, `truth_path`).
- Gate 2 (spec 007): untrained E must equal C end to end. Write E's prediction rows in double:
  float32 rows put a 1e-7 bias into G2-d's paired E − C comparison.
- Decision tables bind a digest of the Gate 2 plan's `c` block, not the whole plan, because the
  plan names the tables' results branch (a circular digest otherwise).
- `tma2-dtables` and `tma2-g2predict` re-run C in `tma2-segment`'s chunks (16, padded to the
  longest) so they reproduce its segmentation file; `c_mismatch_rows` in the tables' header
  records any difference.
- C's GLR nominations divide by σ: noise-free (σ = 0) data needs search-only parameters.
- The full test suite takes about 10 minutes (C on fixture scenarios in the Gate 2 tests).
- Run `uv run ruff check .` (the whole repo, as CI does), not just `src tests`: `scripts/research`
  is linted too.
- E-s's learned evidence is mostly a veto at the ownship zig and E-w's weights mostly a recency
  profile (Gate 2 panel): test any learned component against the classical rule it might be
  before claiming learning, and register that control before its result exists.
- Early stopping that keeps epoch 0 makes a shuffled control equal to the untrained model, so its
  rule cannot fail: score the last-epoch shuffled weights too (Gate 2 panel).
- The scorer (`tma2-gs`/`tma2-g2`) re-solves C, one leg, the oracle and GLR + confirm, so a
  re-score on another CPU family is not byte-identical (Gate 2: C up to 6e-4 relative, 21 one-leg
  rows switch finite/runaway; G2-d moved 1.4e-5). Compare estimators within one scoring run's
  `errors.npz` (`scripts/research/g2_paired_gaps.py`), or re-score on the gate's CPU family.
- Calibration (spec 008): what gets scaled must not read the truth. The feature cache's `usable`
  rows need a finite NEES (truth) for training; `tma2-g3predict` and the export scale by
  `scalable` (plausible, `cov_ok`, finite sds) instead.
- `setup-uv` downloads uv from GitHub releases on every job; a wide matrix can hit 504s. Re-run
  the failed jobs (`rerun_failed_jobs`) once the run completes; nothing in the code is wrong.
- `.gitignore`'s `data/` also matched `src/tma2/data/` (now excepted): after adding a file, check
  `git status --ignored` before trusting a green local run.
- Calibration lessons (Gate 3 panel): choose design settings on tuning ordinals only, never on
  scoring rows; train on the errors the gate scores (a linearised course error cannot see a
  course flip); a scale-only calibration keeps the solve's near-singular correlations; a Gaussian
  sd for course above ~90° is a vacuous statement; the `settled` slice is defined from the truth.
- Gate 4 panel: a shuffled control that permutes errors but keeps the sds tests a null the
  temperature already rejects; register a richer classical rule (a function of all the sds) and an
  encoder-only shuffle before claiming learning. A per-bin reliability point band of ±0.05 on
  about 800 rows is about 2.5 sampling sd: use an interval or a slope test. A 10-knot PAV map on
  2,000 rows caps P by noise at its top knot. Recalibrating P but not the density makes the
  statement contradict itself.
- Spec 010: never add an argument to `physics.layer.residuals`/`iterate` for a reference
  estimator: C's frozen `code_sha256` covers `physics/layer.py`. Subclass (`headroom/gls.py`).
  An `.npz` carries zip timestamps, so its file digest is not reproducible: bind a digest of the
  arrays (`mismatch_truth_digest`). A numba function called from Python returns a Python int
  for a `uint64`: wrap it in `np.uint64` before passing it back in (`OverflowError` otherwise).
- Gate H panel: a reference built by a model-based fit is not a ceiling; name it for what it is
  told. Check a pooled statistic by range band before saying "nothing to win". Do not explain a
  gap you have not tested (the chord explanation of the efficiency was wrong). Before a
  headroom gate, compute the linearised OLS-over-GLS ratio for the declared grid: it shows what
  the grid can possibly yield. A registered "reported beside" comparison is a deliverable: run
  it with the gate, and test its code path first (`--segmentation c2` read the wrong block).
- `headroom.yml`: scoring waits for every prediction shard of every condition; a run's jobs
  show as checks on the PR whose head commit they run from. `ci.yml` skips the site build and
  ONNX conformance on pull requests that cannot affect them (job `changes`).
- 20 concurrent CI jobs: a 32-job prediction run blocks every other workflow's merge job until
  it drains; queue long runs one at a time when a result is waited on.
- Workflow plans: an empty object is falsy (`if r.get('x')` dropped C-r's default settings and
  30 shards failed in minutes), and double quotes inside a bash-quoted `python3 -c "..."` are
  stripped. Emulate the workflow's command builder through bash against the real plan before
  launching, and schedule a failure check 20 minutes after every launch, not only a collection.
- A model built after physics-layer code in the same process inherits a double default dtype:
  force the dtype in the module (`Regressor.float()`), and test under the changed default.
- Check that a reading has rows before registering it: MAN2 has no held-course rows at the
  scorer's prefixes (spec 012 research R8).
- Spec 011: design for what the gap is made of, not for what changed. False transitions rose
  under mismatch, but misses were the larger part of the gap with or without it.
- Arc solve (spec 013): a span starts one row before a manoeuvre's `start_index` (the first row
  already inside it); unbounded least squares winds turns round, so bound them; a cost consistent
  with the bearing error does not rule out a mirror solution (one turn's sign wrong).
- Spec 013: before building a better search, compare its cost with the cost of the fit told the
  truth. If they are equal and the errors are not, the limit is identifiability and no search on
  that cost will help.
- A Laplace evidence must pair every density with its volume: an extra manoeuvre costs about
  −7 (leg) and −10 (changes) in log prior and gains about +6 in Occam factor; forgetting either
  side makes any history win (spec 013).
- Spec 012 panel: a learned model that knows the simulator's prior must be compared with a
  classical estimator given the same prior, not with a prior-free fit; a held-out split that moves
  one scalar is not "unseen"; report efficiency per slice beside medians (the regressor's course
  efficiency was worse than C″'s while its range median was better); do not carry an explanation
  from one spec's tuning data into another's result.
- Evidence (spec 013): fit to the posterior before a Laplace approximation, never to the
  likelihood alone; and plot the per-case differences before quoting shares (the histogram showed
  thousands of units where the medians looked sane).
- Generate from a new ranges file locally before a workflow depends on it: the kernel's manoeuvre
  table holds 32 changes, and a leg minimum under 300 s with 2-hour windows is refused (spec 013's
  first shifted split failed its CI smoke run on that).
- A reference fitted from the truth is not a fit: on weakly determined rows it returns its start,
  and its efficiency falls below 1 (Gate T's T-a: 0.67). Start references from where a real system
  would, and read an efficiency below 1 as a fault, not a success. Check efficiency by how tight
  the bound is before registering a band for it.
- A workflow step that pipes a tool into `tee <dir>/file` must create `<dir>` first and set
  `pipefail`: `tee` opens its file before the tool makes the folder, and without `pipefail` the
  step's exit code is `tee`'s (`timelate.yml`'s first scoring step).
- Never put backticks in an unquoted shell heredoc: bash runs them and deletes the text.
- Gate T panel: a ratio of medians is not a typical gain; report the paired per-period ratio and
  the share of periods lost beside it. Before crediting a search, split its win by whether its
  answer was right: winning either way means the model and prior did the work, and the control is
  the old system refitted with them. Test a soundness check against the fault it exists to catch
  (T-a would have passed the truth-started fit). A calibration check that passes overall must be
  read by complexity too. List what the spec promised and the gate did not run in the record.
- Modal rate-limits app creation: of five `modal run` jobs started within ten seconds, two were
  refused ("App create rate limit exceeded") before any container started. Launch GPU plans a
  minute apart, or re-run the refused workflow run (the plan and its digest are untouched).
