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
014 (time-late classical follow-on, `specs/014-time-late-classical/`; done; a registered study,
not a gate; nothing trained): `timelate/run2.py` (runner; plan key `runner: run2`), prior version 2
and kinds `flat` and `mix` (`prior.py`), `controls.py` (C″'s transitions refitted with arc model and
prior), `study.py` (paired ratios, gain share, classes of wrong-history periods, composite
headroom, held-course false-manoeuvre rate), `counts.py`, `thin.py`, `smooth.py` (RTS over the
frozen EKF); `timelate.yml` takes `thinning`, `systems` and a split `condition`/`whole`; schema
0.36.0. Tuning seed 333 (`experiments/20261112-tl2-tuning/`), thinning study
(`20261112-tl2-thin/`, `scripts/research/tl2_thin.py`), decision `20261112-tl2-decision/` (plan
`configs/timelate/tl-c.json` `351538c2…`, code `0704cdbc…`, never edited), validation seed 334
(`20261112-tl2-val/`, soundness passed), **test record `experiments/20261112-tl2/` (seed 335):
D1 refit's share of the search's gain 0.43 [0.28, 0.58]; D2 wrong histories ambiguous / search
failure / evidence failure 0.53 / 0.08 / 0.39; D3 headroom 1.04 (perfect search) and 1.10
[1.04, 1.18] (perfect evidence as well: inconclusive); D4 false manoeuvres on held course: search
0.76, C″ 0.02, flat prior 0.01, mixed prior 0.03; D5 by the registered rule: no GPU budget.
Decided by the panel, round 1** (`review.md`, five approve with findings). C″ ÷ search 2.13
[1.88, 2.43] paired on Annex B, 1.53 under the shift, 4.09 on whole engagements. **Two defects in
the registered code, recorded and not repaired**: `prior_precision` keeps a 600 s stand-in volume
for a manoeuvre's duration against a sharp density (2 to 3 nats of unearned Occam factor per
small manoeuvre; re-ranked, the held-course false rate is 0.47 to 0.57), and `study.classify` /
`gate.history_right` count manoeuvres cut by the period's edge (edge-aware D2 0.57 / 0.11 / 0.33;
first candidate right about 0.60). Also: the true-history fit drifts over 120 s in 13% of periods
(the composites are noisy oracles). Narrowed: D1 is "about half" (0.39 to 0.58 by estimand; 0.47
over three seeds; four refit runaways carry the point); the flat-prior search obtains 0.78 of the
gain (Annex B's statistics are worth a fifth); the headroom is 1.05 to 1.20 by convention;
"ambiguous" is a property of the Laplace evidence, not the bearings; D5 follows from the rule, not
the evidence, and the study is silent on a hedging model; the gaps under the shifted prior,
correlated errors and outliers are 1.5 to 1.6 with no remedy tried; the mixed prior moves errors
to missed single manoeuvres (6% to 20%). Thinning: fixed normal points cost 1 to 9% (not separated
from 0 or 20%) at half the run time; the adaptive rule broke bins on noise, so the owner's idea is
untested; wild-bearing editing restored clean quality under outliers (not separated from
binning); nothing adopted. Not built: prior-mismatch diagnostic, broadened prior, IMM smoother.
Write-up `site/blog/2026-11-13-time-late-classical.md`, slides
`2026-11-13-time-late-classical-slides.md` (figures `scripts/research/tl2_charts.py`). Panel's
order for what follows (owner's choice): repair evidence, classing and reference and re-register;
robust likelihood, correlated-error model, a prior that can be wrong; a hedged track; then a
learned model. Seeds 333–335 used; 324, 325 unused; the next fresh seed is 336.
**Owner 2026-11-13: repair and re-register (spec 015)**: fix the duration volume, the edge rule
and the drifting reference; decide the same quantities on fresh seeds (336 validation, 337 test);
seeds 333–335 become development data. Nothing trained, no GPU.
015 (time-late repair and re-registration, `specs/015-time-late-repair/`; done; a registered study,
not a gate; nothing trained): prior version 3 (`prior.open_precision`: volume = 1/density for
every factor without a Gaussian residual), `timelate/match.py` (`same_history`, `cut_flags`: one
edge-aware rule), `run3.py` (plan key `runner: run3`; reference held to the true times and flagged
when it drifts; refit fall-back), `study3.py`, `scripts/research/tl3_tables.py` (every record's
`tables.md` generated from `summary.json`). Development on spent seed 335
(`experiments/20261113-tl3-dev/`), decision `20261113-tl3-decision/` (plan
`configs/timelate/tl-d.json` `a6556059…`, code `3b67d026…`, never edited), validation seed 336
(`20261113-tl3-val/`, soundness passed), **test record `experiments/20261113-tl3/` (seed 337, 364
scored periods): D1 0.33 [0.20, 0.45]; D2 first candidate right 0.64, wrong histories 0.44 / 0.13 /
0.43; D3 headroom 1.06 (perfect search) and 1.17 [1.10, 1.25], lower limit 1.099 (perfect evidence
as well): inconclusive; D4 held-course false manoeuvres: search 0.53 (0.80 for spec 014's search on
the same periods; 0.09 under 30 min, 1.00 over 90), C″ 0.02, flat 0.01, mixed 0.00; D5 by the
rule: no GPU budget. Decided by the panel, round 1** (`review.md`, five approve with findings; no
bug changes a decided number). Narrowed: the headroom depends most on how the reference is fitted
(1.11 to 1.19; the 19 held references carry a third of it, ten periods over half; 1.08 to 1.30
across registered sensitivities): an oracle figure, not a limit; the rule's "no" stands and an
override would be a departure from it (the first record's "a judgement, the owner's" is corrected);
D1 is "between a third and a half" and mostly restates how often C″ has the history right; D2's
ambiguous share is the threshold's (0.11 / 0.44 / 0.66 at 1 / 3 / 5); the 0.09 on short held-course
periods is not what a correct evidence gives (integrated over where a manoeuvre might be, Annex B's
prior favours "some manoeuvre" almost everywhere); **the evidence repair is not finished**: version
3's pairing fails at the edges of the prior's support and the 10 s floor (1 to 3.5 nats; recorded,
not repaired, with smaller ones in `review.md`: `_leg_tail` zero beyond 5,868 s, combined
manoeuvres' acceleration unconstrained, speed after a change unpaired). The repair trades false
manoeuvres for missed single ones (one-manoeuvre targets called quiet 0.13 against 0.04; mixed
prior 0.20; re-ranked at a quiet probability of 0.01: 0.09 false, 0.14 missed). Not delivered: each
repair's effect separated per decided quantity; unit tests for `run3`/`study3`; the fall-back
caught one of seven runaway refits. Gaps where the simulator's assumptions fail (search ÷ oracle:
shifted prior 1.7, correlated errors 1.4, outliers 1.5) have no classical remedy yet. Write-up
`site/blog/2026-11-13-time-late-repair.md`, slides `2026-11-13-time-late-repair-slides.md` (figures
`scripts/research/tl3_charts.py`). Panel's order (owner's choice): a hedged track from the stored
candidates and a declaration margin; robust and correlated-error likelihoods and a prior that can
be wrong, scored on the mismatch splits; then a learned model registered against those; no fourth
Annex B identification study. Seeds 336, 337 used; 324, 325 unused; the next fresh seed is 338.
**Owner 2026-11-13: option B (spec 016)**: classical controls on CPU and, in parallel, a learned
whole-period model on GPU under a plan registered before any result, scored only once the controls
exist; within the $50 total.
016 (time-late controls and a learned whole-period model, study L, `specs/016-time-late-learned/`;
done; SRD §5 row proposed, owner merges). **Controls** (nothing trained; `timelate/hedge.py`,
`corr.py`, `run4.py` with plan key `runner: run4`, `study4.py`): wild bearings edited out; an
effective bearing sd from the error correlation estimated from the bearings' second differences
(used above a share of 0.2); the search under Annex B's prior and a broadened one
(`configs/timelate/tl-broad.json`), pooled; a declared history (evidence margin 1, quiet probability
0.01: `ctl-d1-q0.01`) and a hedged track (temperature 1: `ctl-h1`); the combined control `ctl` is
not told the conditions. Tuning seed 338 (`experiments/20261113-tl4-tuning/`). **Model**
(`regress/period_data.py`, `period_predict.py`, `model.py` with `causal=False` and a manoeuvre
head, `timelate/learned.py`, `tma2-tlpredict`; mix `configs/regress/tlm-mix.json`, plans
`tlm-s1..s3.json`): a bidirectional transformer over 240 tokens of six 5-second rows, three seeds of
12.5 million simulated periods on a T4 each (pilot `experiments/20261113-tlm-pilot/`, runs
`experiments/20261114-tlm-runs/`, $14; November's Modal total $41 of the owner's $50); reported track
`learned-sK-arc` (the arc model fitted at the model's manoeuvre spans, probability over 0.5), own
track beside. Decision `experiments/20261113-tl4-decision/` (plan `configs/timelate/tl-e.json`
`82cd70ee…`, code `e5040f5e…`, never edited; two addenda); controls' validation seed 340
(`20261113-tl4-val/`, L-a passed; `tma2-tlscore --controls-record` refuses a learned track without
it); **test record `experiments/20261114-tl4/` (seed 341, 2,860 periods, scored once): learning
shown on no split (declared control ÷ learned 0.80 to 0.82 shifted, 0.87 to 0.94 shifted 2, 0.83
correlated, 0.77 to 0.81 outliers, 0.97 to 1.00 bias), harm on Annex B (0.81 to 0.82), the learned
track ahead on held course (1.06): by the rule the classical controls stand and the learned track
stops. Decided by the panel, round 1** (`review.md`, five approve with findings; all 42 ratios
reproduce). Controls against the standing search: 1.68 with 2% outliers, 2.44 with 5%, 1.33
correlated, 1.70 held course (false manoeuvres 0.08 against 0.49), 1.03 shifted, 1.00 bias, 1.09
Annex B (0.96 on validation); replicated on three seeds. Narrowed: the 20% is a tail (median
per-period ratio 1.00 everywhere; level where the model declares as many manoeuvres as the control,
about twice as bad where it declares fewer): **the registered comparison measured the model's
untuned detector against the evidence search**, so "this model with this read-out stops"; the own
track is 0.71 of the control on Annex B and level under the shifted prior in range only (course
0.79, speed 0.77; a win where the bound is loose cancels a loss by three where it is tight); the
mismatch conditions lie inside the model's training ranges (it lost in-distribution); a search
started from the model equals the control at a third of the time (tuning data, not a result); the
control is not free (one-manoeuvre targets called quiet 0.29 against 0.05 with correlated errors),
does nothing under bias, and knows the generator's error family; the shifted-prior gap (control ÷
true-history reference 1.7 to 2.1 by convention) is open for both and may be identifiability. Not
delivered: a working prior-mismatch diagnostic (`log_bayes_broad` is not a Bayes factor), a Huber
cost, a whitened fit, prior version 4, the export check on trained models, IMM/EKF tracks beside,
the weights' digests in the test record, unit tests for `run4`/`study4`. Not tested: a learned
proposer inside the search, training through the arc layer, a larger budget. Write-up
`site/blog/2026-11-14-time-late-learned.md`, slides `2026-11-14-time-late-learned-slides.md`
(figures `scripts/research/tl4_charts.py`; tables `tl4_tables.py`, `tl4_learned_tables.py`,
`tl4_supplement.py`). Panel's order (owner's choice): adopt `ctl` as the standing time-late system
and study whether the shifted-prior gap is identifiability (classical, CPU); only if it is not, the
trained models as proposers inside the search. Seeds 338 to 341 used; 324, 325 unused; the next
fresh seed is 342.
**Owner 2026-11-14: option A (spec 017)**: the classical control `ctl` (declared at margin 1, quiet
probability 0.01) is the standing time-late system; one classical study of whether the
shifted-prior gap is identifiability, CPU only, nothing trained; what study L's record owes is made
good. 017 (`specs/017-shifted-gap/`; done; a registered study, not a gate; nothing trained):
`timelate/detect.py` (a true manoeuvre's detectability: the χ² its omission adds, times held;
references told only the detectable ones), `run5.py` (plan key `runner: run5`: `run4`'s control
unchanged, `ref-full`, `ref-dT`, the search under the split's own prior `true`, IMM and EKF as
tracks, references on edited bearings), `study5.py`, `scripts/research/tl5_{tables,supplement,
tracks,charts}.py`, workflow `headers/**`. Tuning seed 342 (`experiments/20261114-tl5-tuning/`),
decision `20261114-tl5-decision/` (plan `configs/timelate/tl-f.json` `0b29a95d…`, code
`b32247f8…`, never edited; no decision rule, five estimands and the recommendation's logic fixed),
validation seed 343 (`20261114-tl5-val/`, soundness passed), **test record
`experiments/20261114-tl5/` (seed 344, shifted split 451 scored periods): 0.37 of true manoeuvres
are under a detectability of 20 (Annex B 0.16); control ÷ full reference 2.27 [2.04, 2.55]; not
being told those under 20 costs 1.58; control ÷ that reference 1.43 [1.28, 1.61]; attainable share
0.65 / 0.44 / 0.14 at thresholds 10 / 20 / 40; control ÷ true-prior search 1.17 [1.06, 1.29]; by
the fixed logic a proposer study is not recommended (the control misses 0.18, not over a third, of
manoeuvres above 40). Decided by the panel, round 1** (`review.md`, five approve with findings).
Narrowed: the pooled split is two kinds of period (some manoeuvre under 20, 336 periods: control ÷
`ref-d20` 1.16; none, 115: 2.65; the 134 periods where the control misses a manoeuvre above 20
carry 83% of the attainable gap, 2.73 against 1.09 elsewhere; share 0.70 where the bound is tight,
0.20 where loose); the logic's second condition counted manoeuvres, not cost, and turns on the
match tolerance (0.30 / 0.18 / 0.11 at 60 / 120 / 240 s): the "no" is the rule's, not the
evidence's; the attainable part is at least half a prior problem (of 138 missed manoeuvres above
40 the true-prior search finds 66; E5 2.58 where it finds more, 1.07 elsewhere); detectability is
not additive and the references are flattered by true times and handicapped by hard omission, so
E3 and E4 are not bounds; the IMM/EKF ratios in the first record were on 40% of periods (on common
rows 3.8 to 10.5). Not delivered: the split under each way of fitting the reference, course and
speed in the estimands, a joint detectability, unit tests for `detect.py`/`run5.py`. Write-up
`site/blog/2026-11-14-shifted-gap.md`, slides `2026-11-14-shifted-gap-slides.md`. Panel's order
(owner's choice): a manoeuvre prior that adapts to the period (classical, CPU; registered against
`ctl`, true-prior search as ceiling, false manoeuvres on held course reported), a hedged track
beside; no GPU proposer now. Seeds 342 to 344 used; 324, 325 unused; the next fresh seed is 345.
**Owner 2026-11-14: option B (spec 018)**: a classical control whose manoeuvre prior adapts to
the period, and a hedged track beside; CPU only, nothing trained.
018 (`specs/018-adaptive-prior/`; done; a registered study; nothing trained): `timelate/adapt.py`
(`family` of priors on the broadened prior, `rescore` of one shared candidate set, `rate_posterior`,
`pooled_choice`, `range_sd` and `hedged_spread`: a mixture's Laplace sd of range), `run6.py` (plan
key `runner: run6`; `run4`'s control unchanged; `fam-<member>`, `ada-d1-q0.01`, `ada-hT` with
`hrange_`/`spread_` arrays, `ada-aP`, `true`, `ref-full`, `logz`), `study6.py` (paired ratios in
range, course and speed with period counts, kinds of period, groups of periods, coverage,
`criteria6`), `scripts/research/tl6_{tables,supplement,spread_scale,tracks,charts}.py`. First
design (three rates, a search each) gained nothing on tuning seed 345
(`experiments/20261114-tl6-tuning/`); second design (30 priors: leg mean, leg sd ratio, largest
turn) on the same seed (`20261115-tl6-tuning2/`: shifted 1.10 [0.96, 1.27] declared, 1.16 hedged;
Annex B 0.90). Decision `20261115-tl6-decision/` (plan `configs/timelate/tl-g.json` `541aa8b4…`,
code `710c74e0…`, never edited; gain = control ÷ system in range wholly above 1 on a shifted split;
harm = wholly below 1 in range, course or speed on any split; spread = two stated sds cover 0.90
to 0.99), validation seed 346 (`20261115-tl6-val/`, soundness passed; 0.95 and 1.04 on shifted,
reported), **test record `experiments/20261115-tl6/` (seed 347, 1,250 periods, scored once): no
gain (shifted 1.00 [0.92, 1.08] declared, 1.00 [0.93, 1.08] hedged; shifted 2 1.01, 0.99); Annex B
0.93 [0.85, 1.01]; the hedge reads as harm in course on shifted and outliers; spread 0.944 Annex
B, 0.897 shifted: by the rule the standing control stays for both outputs; the forecast (a trade)
was wrong. Decided by the panel, round 1** (`review.md`, five approve with findings). Narrowed:
the period's evidence does not rank the priors by accuracy (posterior over 30 members nearly flat,
largest 0.12 to 0.15; uncorrelated with a member's error on shifted; the chosen member is 1.9 × the
best in hindsight and 3 to 5% better than a central fixed one); the null excludes gains above about
8% (pooled over three seeds 1.01 [0.95, 1.08]); the Annex B cost is real pooled (0.91 [0.84, 0.98])
and is the design's (the family lacks Annex B's own prior; a member with it was not run); the grid
was set knowing the splits' statistics; choosing a member by groups of periods adds nothing; the
true-prior search is 1.15 [1.07, 1.23] over three seeds and a tail (ten of 355 periods carry 87%),
a reference and not a ceiling; the hedge costs about 10% in course everywhere as a tail and is not
worth having; one spread factor does not transfer (1.95 on tuning, 2.68 on test; coverage 0.897
[0.870, 0.923] by period bootstrap), the spread being honest where candidates disagree and too
narrow where the mixture is confident. Recorded, not repaired: the member is chosen on plain
evidences while the declaration uses the quiet probability; `hedged_spread` zeroes non-finite sds;
no unit tests of `run6`/`range_sd`. Not delivered: a search under each member, IMM/EKF on these
periods, a spread for course and speed. Write-up `site/blog/2026-11-15-adaptive-prior.md`, slides
`2026-11-15-adaptive-prior-slides.md`. Panel's order (owner's choice): stop identifying the prior
and write up specs 013 to 018 as a whole with `ctl` standing; or one development diagnostic on
spent seeds; or change the information (ownship advice, longer periods); no learned proposer or
GPU run. Seeds 345 to 347 used; 324, 325 unused; the next fresh seed is 348.
**Owner 2026-11-15: option B (spec 019)**: write up the time-late track as a whole after one
diagnostic on used seeds. 019 (`specs/019-time-late-synthesis/`; done; no gate, no registered
result, nothing trained, no new seed): `timelate/run7.py` (plan key `runner: run7`: a search of
its own under a ladder of priors from the broadened one to a split's own statistics, parts
`legs`, `angle`, `rate`, `speed`, `kinds`; each part alone; a family member with its own search),
`study7.py`, `scripts/research/tl7_{tables,refit}.py`, `scripts/research/tl_synthesis.py` (the
track's figures of record from the test records of specs 016 to 018:
`experiments/20261115-tl-synthesis/tables.md`, with the reviewers' `review.md`). Diagnostic
(`experiments/20261115-tl7-dev/`, 130 scored shifted periods of used seed 347; development work):
a member's own search equals its refit of shared candidates (1.03 [0.91, 1.19] both), so spec
018's family was not starved; along the ladder control ÷ system is 0.98, 1.05, 1.06, 1.12, 1.10,
1.11 [0.94, 1.32] (legs first; legs, turn sizes and turn rates reach the whole prior's figure;
the other parts alone do nothing); nothing separated; manoeuvres missed fall from 0.52 to 0.36.
**The account** is `site/blog/2026-11-15-time-late-synthesis.md` (slides
`2026-11-15-time-late-synthesis-slides.md`): the standing control and its known faults; C″ ÷
control 2.1 to 2.4 Annex B, 1.6 to 1.7 busier, about 5 with wild bearings, level on held course;
what remains by convention (undeclared control ÷ free reference 1.3 / 1.2 / 1.8 to 2.1; declared ÷
times held 1.6 / 1.5 / 2.3 to 2.7); the challengers; what was withdrawn; what was never tested.
Corrected by its reviewers: "ten best periods carry the gain" (spec 018's panel and this spec's
first draft) is a one-sided statistic that reads spread as a tail (the true-prior search wins in
53% of periods, twice as good in 20%, twice as bad in 13%; trimmed at both ends 1.10 unchanged).
The time-late track stops here unless the owner reopens it; what would justify a learned
approach again: real data, several periods of one target or ownship advice, or a proposer the
evidence still judges. Seeds: none new; the next fresh seed is 348.

020 (browser viewer on the exported artefact, `specs/020-browser-viewer/`; SRD §1 and §7 step 5,
the last item of the default plan; the owner said "continue" after PR 37; not a gate, nothing
trained, no fresh seed): the page `site/src/pages/viewer.js` (`/viewer`, navbar "Viewer")
runs Gate 2's carried E-w graph (`gate2.export`, carried weights) in ONNX Runtime Web 1.31.1
(WASM, one thread, worker `site/static/viewer-data/worker.js`; the runtime is copied from
`site/node_modules` by the site's prebuild into gitignored `static/ort/`). It runs on six
engagements of used seed 319 chosen by `tma2.viewer.choose`: quiet, one manoeuvre and busy,
counted over the shown span from zig + 5 min, plus the first where E's G5 median range error
is worse than C″'s. `tma2-viewer-data` (`viewer/build.py`) builds the data: E's segmentation
and hand-over in Gate 2's chunks of 16, the graph's inputs every 60 s, Python onnxruntime
outputs, and one leg, IMM, C and C″ from Python. It takes about 26 min. The data, gzipped with
a manifest of digests, are 1.2 MB in `site/static/viewer-data/`. Checks:
- `conformance/onnx/viewer_python.py` (fresh Python run on the shipped inputs);
- `viewer_leg.mjs` (the built page in Chromium, every row);
- `cmp` of the page's graph with a fresh export, all in `ci.yml`'s `onnx-conformance`.

Record `experiments/20261115-viewer/`: 181 rows; browser state within 2.7e-6, covariance
within 3.2e-6 on its own scale; one off-diagonal element of one row is 3.2e-5 element-wise
(research R6; cause not established); flags identical. At 0.27 s a row, the first estimate
appears in 1.7 s. On the 24 G5 rows the demo's E equals Gate 2's committed predictions to
2e-7. Slides `site/blog/2026-11-15-browser-viewer-slides.md`. The SRD's default plan is
complete; what follows is the owner's choice. Seeds: none new; the next fresh seed is 348.

021 (the carried model end to end in the browser, `specs/021-browser-segmenter/`; owner
2026-11-15 option A; not a gate, nothing trained, no fresh seed): C's host code is ported to
JavaScript (`site/static/viewer-data/js/`: `lsq`, `glr`, `codes` with NumPy's pairwise and
float32 sums, `ownship`, `features`, `search`, `confirm`, `handover`, `pipeline`). The physics
layer at confirmation's settings is its own graph (`viewer/layer_export.py`, `layer.onnx`; three
legs in CI), and so is E-s (`es.onnx`). The page's live mode runs the whole model from bearings
in a module worker. The dump (`tma2-viewer-dump`; `--install` writes the scenario files and
graphs into the viewer data) and the 30 check scenarios are in `experiments/20261116-port/dump/`.
Checks:
- `conformance/onnx/port_node.mjs` and `port_summary.py` (CI job `browser-port`);
- `viewer_leg.mjs --live all`.

Record `experiments/20261116-port/`: segmentation identical on 1,770 of 1,770 rows; every
nomination and decision identical; cost drops within 1.3e-4, against a smallest margin of 0.152; GLR crosses its threshold at one row
(ordinal 1) without changing a nomination; cost tables differ by up to 22%;
live mode 25 to 93 s an engagement, 181 of 181 rows identical. Slides
`site/blog/2026-11-16-browser-segmenter-slides.md`. Not built: pasting a scenario (story 3).

022 (publish the site, a time-late page, persistent PR previews, `specs/022-site-publishing/`;
owner 2026-11-16 "A + B + PR previews"): `.github/workflows/pages.yml` publishes to the
`gh-pages` branch:
- the root on every push to `main`;
- `pr/<n>/` for each same-repository PR at its head (`SITE_BASE_URL`), never deleted;
- `pr/index.json` (`scripts/site/preview_index.py`), updated on close;
- one comment on each PR linking its preview and changed posts, edited in place on every push
  (marker `<!-- site-preview -->`, as argonautical's `site-publish.mjs`; issue 44);
- a `workflow_dispatch` (pr, ref) to backfill earlier PRs.

The workflow has three jobs. `build` runs the PR's code without write access, and previews
leave out `ort/` and load the root's runtime. `publish` holds the write token. It re-applies its
change on the latest `gh-pages` until its push succeeds, and skips a stale head. Closed-PR state
updates run under `pull_request_target`, using main's code. The site's `/previews` page reads
the root index. `/timelate` shows spec 016's test-record tracks (20 periods each of man2, man2-out
and shift), with true and declared manoeuvres and per-period errors. Its data are built by
`scripts/research/timelate_viewer_data.py` into `site/static/timelate-data/` and checked by
`tests/unit/test_timelate_viewer_data.py`. Published site: `https://debrief.github.io/gitma2/`.

023 (longer engagements, issue #42, `specs/023-long-engagements/`; an investigation, not a gate;
nothing trained; fresh seed 348 used, the next is 349): a separate simulator
(`src/tma2/long/sim.py`, `configs/long/long.json`; generator 0.6.0 untouched) of one engagement
each of 6, 12, 24 and 48 hours (Annex B targets; an ownship turning at each 20–40 min leg and
keeping the target at 3–25 km, steering on the true target). Systems on windows
(`long/windows.py`: time from 0, positions from the ownship's at the window start; C″'s veto at
every ownship turn): real-time E (the exported graph), C″ on the last 2 h and one leg on 30 min
every 10 min, the IMM over everything (`long/realtime.py`); time-late `ctl` on 2-h windows
overlapping 30 min, stitched mid-overlap on each window's own rows (`long/timelate.py`).
`tma2-long {realtime,timelate,scaling}`, workflow `long.yml` (runs on changes to
`configs/long/run.json`; results `results/long-<run id>`), record `experiments/20261117-long/`
(`scripts/research/long_report.py`; page data `long_viewer_data.py` → `site/static/long-data/`;
figures `long_charts.py`; bound cost `long_bound_cost.py`). Findings (four engagements,
anecdotes): stitched `ctl` 1.6–2.7% median range error at every length, no seam penalty;
real-time E and C″ 13–21%; the IMM degrades over 48 h (answers 81%); `ctl` on one period takes
1 min (0.5 h) to 114 min (6 h) and caps at ten manoeuvres; real-time estimates cost 27–37 s
each; the IMM over 48 h 426 s (cause not established); the whole-engagement bound 4.5 GB at
48 h. Note `docs/research/12-long-engagements.md`; sections on `/viewer#long` and
`/timelate#long`. Recommended next (owner's choice): carry state between windows, an
incremental C, then scenario realism before a registered study.

024 (long engagements, part 2, `specs/024-long-carry-incremental-realism/`; owner on PR 46:
"implement 3 recommendations"; an investigation, not a gate; nothing trained; no new seed: 348
with a realism stream, the next fresh seed is still 349). `long/carry.py` (`ctl-carry`: `ctl`
with its start from nothing replaced by the previous window's declared track and manoeuvres;
both solved per window; this `ctl` equals spec 023's runner within 1 mm on one machine,
`experiments/20261117-long2/ctl-check.json`), `long/incremental.py` (one confirmation per
2-hour block, cropped to each estimate's 720 rows; equals the per-window run for blocks of
one), realism in `long/sim.py` `_World` (`configs/long/realistic.json`: steering on measured
bearing and a ±30% range belief, closing on the last belief when lost; gaps; detection 50% at
40 km; a second contact, `Engagement.other`, swapped within 1°). `tma2-long realtime-inc|carry
--config --contact`; record `experiments/20261117-long2/` (CI run 44153682342;
`scripts/research/long2_{report,viewer_data,charts,block_position,ctl_check}.py`). Findings:
carry is level in accuracy (median window ratio 1.00; wins and losses mixed) and its start costs
about 55% of the search it replaces; the incremental C is 1.7× cheaper and worse (E 29.8 / 35.6%
against 14.3 / 20.9% at 24 / 48 h), the loss growing with an estimate's position in its block
(cause not established; not adopted); realistic contact 1 keeps `ctl` at 1.5–2.2%, the untended
contact 2 is held 10–22% beyond 6 h and at 6–8% where held. Note
`docs/research/13-long-engagements-2.md` proposes a registered study (6- and 12-hour realistic
engagements, seeds 349–351): the owner's choice.


025 (several periods of one target, joined through the gaps, `specs/025-joined-periods/`; owner
2026-11-17 option C, motion continuity only; numbered 025 because 023/024 are another
session's; a registered study, not a gate; nothing trained): `timelate/layout.py` (two or
three periods of 15–30 min, gaps of 5–30 min, from an own stream), `run8.py` (plan key
`runner: run8`: `ctl-d1-q0.01` unchanged alone per period, joint over the span with the gaps'
bearings masked, full span; references `ref-span(-fixed)`, `ref-alone(-fixed)`), `study8.py`
(paired per-period ratios, engagement bootstrap, by kind, gap events, soundness),
`tma2-tlscore` `_joined`, `scripts/research/tl8_{tables,charts}.py`. Tuning seed 349
(`experiments/20261117-tl8-tuning/`); first registration `20261118-tl8-decision/` stopped at
validation seed 350 (`20261118-tl8-val/`: pooled-row soundness 0.75, a statistic with no power);
owner 2026-11-18 option A: re-registered `20261118-tl8-decision2/` (plan
`configs/timelate/tl-k.json` `bbba4603…`, code `ec046dc0…`, soundness = geometric mean over
engagements), validation seed 352 passed (`20261118-tl8-val2/`, 1.13 [0.80, 1.62]), **test record
`experiments/20261118-tl8/` (seed 353, scored once): alone ÷ joint gain on all four splits, no
harm (Annex B 3.10 [2.22, 4.58], busier 1.97 [1.63, 2.39], wild bearings 2.72, held course
12.8). Decided by the panel, round 1** (`review.md`, five approve with findings): within these
conditions (≤ 2 h, gaps 5–30 min, association certain, Annex B gap manoeuvres) the joint solve
is the standing time-late system for several periods of one target. Narrowed: mostly periods
without their own ownship turn becoming answerable (alone's error there 0.46); where a period
stands alone about 1.6 on Annex B and not shown on busier targets (1.06 own turn, 1.28 own
rows); held course 12.8 is "one leg"; wild bearings is Annex B's engagements; one period in
eight twice as bad joined, unflagged; gap manoeuvres 36% missed on busier targets, invented
in about a fifth of quiet gaps; soundness is a gross-fault screen (an efficient reference
reads 0.79 under its own model; runaway fits to 773). Not compared with spec 024's carried
state. Write-up `site/blog/2026-11-18-joined-periods.md`, slides
`2026-11-18-joined-periods-slides.md`. Panel's order (owner's choice): spec 024's `ctl-carry`
on these engagements; a consistency flag and gap-manoeuvre markers; an uncertainty; a stress
split with longer gaps. Seeds 349, 350, 352, 353 used (351 counted only); the next fresh seed
is 354.

026 (long engagements, the registered study, `specs/026-long-study/`; numbered 026 because
spec 025 (joined periods) was merged first; owner on PR 47:
"registered study"; not a gate; nothing trained; seeds 349 tuning, 350 validation, 351 test,
all used; spec 025 ran in parallel on 349, 350, 352 and 353 of its own simulator (a different
stream, so different engagements, but the seeds were claimed twice; 351 it counted only); the
next fresh seed is 354). `long/study.py` (E1 ctl ÷ ctl-carry per window on the
tended contact, non-inferior if the lower limit ≥ 0.95; E2 untended ÷ tended by range band;
E3 IMM hours 6–12 ÷ 0–6; soundness S1–S3; bootstrap over engagements), `imm_states`,
`tma2-long imm|study`, `configs/long/study-*.json`, run files `configs/long/runs/ls-*.json`;
decision `experiments/20261118-ls-decision/` (digests by `scripts/research/long_study_digests.py`,
code `938ef9a2…`). Tuning `20261118-ls-tuning/`, validation `20261118-ls-val/` (soundness
passed), **test record `experiments/20261118-ls/` (60 engagements, scored once): E1 non-inferior
1.017 [0.958, 1.082]; E2 1.47 [1.12, 2.05]; E3 drift not shown 1.06 [0.82, 1.31]. Panel round 1:
three approve with findings** (`review.md`, `supplement.json` from
`scripts/research/long_study_supplement.py`). Narrowed: E1 rests on level windows (each chain's
first is ctl by construction): without them 1.021 [0.9502, 1.100], where the two differ 1.034
[0.923, 1.168], 12 h 1.005, untended contact 0.942; adopted only as a cost measure (31% of the
search where it runs) for tended contacts up to 12 h; E2 is this simulator's second contact
(no range keeping, scored where detected; 2-km sub-bands 1.34 [1.01, 1.87]); E3 reads answered
rows only (counting failures 1.26 [0.88, 1.80]; the share answered falls 0.91 to 0.74–0.79).
Write-up `site/blog/2026-11-18-long-study.md`, slides `2026-11-18-long-study-slides.md`
(figures `scripts/research/long_study_charts.py`). Panel's recommendation (owner's choice): stop
the long-engagement track here as a simulation study; reopen only with measured realism, an
ownship steered by its own track, or association.

027 (carrying state across gaps against joining through them, `specs/027-carry-across-gaps/`;
owner 2026-11-18 option B; registered as spec 026, renumbered 027 because the long-engagement study merged first as 026; a registered study; nothing trained): `timelate/carry.py`
(`solve_ctl`: `ctl` line for line, its start from nothing optionally replaced by a carried
state; equals `ctl` without one, `scripts/research/tl9_ctl_equivalence.py`), `run9.py` (plan
key `runner: run9`: `run8` per engagement, then the carry chain), `study9.py` (carry ÷ joint,
alone ÷ carry over later periods); tables in `tl8_tables.py`, figures `tl9_charts.py`. Tuning
on spent seed 353 (`experiments/20261118-tl9-tuning/`), decision `20261118-tl9-decision/`
(plan `configs/timelate/tl-m.json` `0f1a8cae…`, code `cee4a319…`), validation seed 360
passed (`20261118-tl9-val/`), **test record `experiments/20261119-tl9/` (seed 361): joining
better on Annex B (carry ÷ joint 2.33 [1.66, 3.43]), wild bearings and held course; busier not
separated (1.351 [0.993, 1.820]); carrying not shown on Annex B (1.07), helps on busier (1.29);
no harm. Decided by the panel, round 1** (`review.md`, five approve with findings): the joint
solve stays standing; the first record's carry recommendation is withdrawn (not the rule's
output); this is a carried start, not carried information (about half of periods tie with
`ctl` alone; the busier gain is a quarter of periods without their own turn), so nothing is
said about a carried prior. Write-up `site/blog/2026-11-19-carry-across-gaps.md`, slides
`2026-11-19-carry-across-gaps-slides.md`. Panel's order (owner's choice): a carried prior
(state and covariance through the gap, a prior in the evidence) on spent seeds first; a
consistency flag; an uncertainty; longer gaps. Seeds 360, 361 used; 354 to 359 skipped to stay clear of PR 47
(spec 028 then used 354–356; 357–359 unused); the next fresh seed is 362.


028 (the previous window as a prior, `specs/028-carry-prior/`; registered and run as 027,
renumbered because the carry-across-gaps study merged first as 027; owner 2026-11-18 after PR 47; a
registered study, not a gate; nothing trained). Code:
- `long/carried.py`: `CarriedPrior`; `joint_fit_c`, `log_evidence_c` and the copied search,
  equal to the originals with no prior; `hand_on` (the state at the next window's first row,
  refitted on the bearings before it, with a Laplace covariance); `widen`; `guard`, a χ²(4)
  test.
- `long/carry2.py`: `ctl-prior` beside `ctl` and `ctl-carry` in one job, run by
  `tma2-long carry2`.
- `long/study27.py` (`tma2-long study27`) and `tma2-long jointpair`.

Seeds and settings: 354 tuning (`experiments/20261118-cp-tuning/`). Decision record
`20261119-cp-decision/`: scale 4, tail 1,200 s, α 0.001, code `09a7edae…`. Validation 355
(`20261119-cp-val/`): soundness passed.

**Test record `experiments/20261119-cp/` (seed 356, 60 engagements, scored once): not shown, at
this size; no harm.** Weak geometry is 1.105 [0.963, 1.273]: clustered by engagement
[0.951, 1.279], without the 13 constructed ties 1.112. Other 1.14 [1.035, 1.27]; contact 1 1.11
[1.006, 1.22]; ctl-carry ÷ ctl-prior 1.14–1.22.

**Panel round 1** (`review.md`): three approve with findings. Narrowings:
- The owner's case, a window with no useful ownship manoeuvre, never occurs in this simulator;
  the weak split is the untended contact plus windows near gaps.
- Beside the rule there is an average shift with many losses (median window 1.03).
- "Narrows the permutations" is not shown either way.
- The registered settings were extrapolated, not run as a chain.
- `hand_on`'s refit starts from the full-window fit, so it can keep overlap information.
  Recorded, not repaired.

Write-up `site/blog/2026-11-19-carry-prior.md`, slides `2026-11-19-carry-prior-slides.md`.
Recommended (owner's choice): adopt `ctl-prior` with its guard for tended contacts up to 12 h
and close the track. Alternatives: an ownship holding course for 1–2 h (the owner's case), or a
registered joint solve over consecutive windows. Seeds 354–356 used (357–359 unused); the
next fresh seed is 362.


029 (the carried prior where the ownship holds course, `specs/029-held-course/`; owner
2026-11-19 "test the ownship holding course option"; a registered study, not a gate; nothing
trained).
- **Design:** spec 024's realism with ownship legs of 1–2 h (`configs/long/hold-*.json`), contact
  1 only, 1-hour windows overlapping 15 min. No 2-hour window is turn-free at those legs.
  `long.yml` passes `window_s`/`overlap_s` through.
- **System:** spec 028's `ctl-prior`, unchanged.
- **Scorer:** `long/study29.py` (`tma2-long study29`). Classes by ownship turns overlapping a
  window: held, one, more (more is empty). Excludes windows with no hand-over and bootstraps over
  engagements.
- **Records:** tuning 362 (`experiments/20261119-hold-tuning/`); decision
  `20261119-hold-decision/` (code `c39cb031…`); validation 363 (`20261119-hold-val/`, soundness
  passed).

**Test record `experiments/20261119-hold/` (seed 364, 60 engagements, scored once): gain, no
harm.**
- Held windows: ctl ÷ ctl-prior 2.41 [2.06, 2.83], median 2.15, 76% of windows better. Seeds:
  2.10, 1.91, 2.41.
- One turn: 1.22 [1.06, 1.40].
- Median error on held windows: 0.227 → 0.074.

**Panel round 1** (`review.md`, three approve with findings). Narrowings:
- The comparison is against the same 1-hour window alone; 2-hour `ctl` and a joint solve were not
  tested.
- The mechanism is range observability; history counts were not measured.
- The gain grows with range: 1.66 under 15 km, 3.19 beyond 25.
- Excluded held windows are windows where contact was lost (as ties 2.34).
- Coverage 0.945 passes the band but is not a calibration (median NEES 0.74).
- Hand-overs never fall inside a target manoeuvre: windows are placed by truth.
- The carried start alone costs 11% on one-turn windows: no `ctl-carry` without the prior.

Supplement: `scripts/research/hold_supplement.py`. Write-up `site/blog/2026-11-19-held-course.md`,
slides `2026-11-19-held-course-slides.md`. Recommended (owner's choice): adopt `ctl-prior` for the
tended contact. Then register `ctl-prior` (1 h) against `ctl` (2 h) and a joint solve on
held-course engagements, with a reference told the truth over the span. Seeds 362–364 used; the
next fresh seed is 365.

030 (a carried prior across gaps, `specs/030-carried-prior/`; owner 2026-11-19 option A, then
"register k4"; a registered study; nothing trained; developed and registered as 028, renumbered because
another session's 028 and 029 (long engagements) merged first; code and bound plans keep "spec 028"): `timelate/cprior.py` (`CarriedPrior`: a
Gaussian prior on a period's starting state from the previous period's declared last state and
Laplace covariance, propagated through the gap at constant velocity with Annex B process noise;
applied by wrapping `prior.prior_residuals`/`log_prior`/`open_precision` inside
`carried_evidence()`, so `ctl`'s registered code is untouched), `run10.py` (plan key `runner:
run10`; `run9` then the carried-prior chain; settings `cprior_variants` for inflation `inflate`
and a two-part mixture `w`), `study10.py`, `scripts/research/tl10_{tables,charts,supplement}.py`.
Development on spent 361 (`experiments/20261119-tl10-dev/`: uninflated prior overconfident,
truth inside 95% in about half), refinement (`20261119-tl10-refine/`: rule chose k4, covariance
4× in sd, on 361; checked on 360), decision `20261119-tl10-decision/` (plan
`configs/timelate/tl-o.json` `74166535…`, code `90a19712…`), validation seed 362 passed
(`20261119-tl10-val/`), **test record `experiments/20261120-tl10/` (seed 363): alone ÷ k4 on
Annex B 1.59 [1.21, 2.13], helps; no harm on any split. Decided by the panel, round 1**
(`review.md`, five approve with findings; `supplement.json`): narrowed to "a carried prior helps
where a period cannot answer alone" (no own turn 1.97; own rows 1.04, level); the inflation is
not shown to matter (uninflated ÷ k4 0.99 [0.78, 1.25]); k4 covers by being about 2.6× too wide
(mis-shaped process noise, one history's covariance too narrow in the tail); k4 ÷ joint 1.40,
on the line; against spec 027's carried start 1.60 (not registered). The joint solve stays
standing; the carried prior applies, within the simulator, when only the previous state and
covariance are kept. Write-up `site/blog/2026-11-20-carried-prior.md`, slides
`2026-11-20-carried-prior-slides.md`. Panel's order (owner's choice): a consistency flag on the
carried prior's distance; a calibrated carried prior on spent seeds; a longer-gap stress split;
a real hand-over only if that case matters. Seeds 362, 363 used here in the time-late layout
simulator; spec 029 had claimed 362 to 364 earlier on another branch in the long-engagement
simulator (different streams, so different engagements, but the numbers were used twice). The next
fresh seed is 365.

031 (the carried prior against longer windows, `specs/031-held-comparators/`; registered and run as
030, renumbered because the carried-prior-across-gaps study merged first as 030; owner 2026-11-19
"run the comparison against 2-hour ctl and joint solve"; a registered study, not a gate; nothing
trained). On spec 029's held-course engagements, 1-hour `ctl-prior` (a) against (b) `ctl` and
`ctl-prior` on 2-hour windows (stitched) and (c) a joint solve (`ctl` on each turn-free hour's union
with the hour before; `tma2-long jointheld`); scorer `long/study30.py` (`tma2-long study30`; D1 2-hour
ctl, D2 joint, D3 2-hour ctl-prior, each ÷ (a) on held windows); `long.yml` passes `tag`; run files
`configs/long/runs/cmp-*.json`. Tuning on spent seed 364 (`experiments/20261119-cmp-tuning/`),
decision `20261120-cmp-decision/` (code `e7a1870b…`), validation 365 (`20261120-cmp-val/`, soundness
passed), **test record `experiments/20261120-cmp/` (seed 366, 179 decided windows): "ctl-prior worse"
on all three: D1 0.730 [0.579, 0.917], D2 0.774 [0.632, 0.954], D3 0.488 [0.386, 0.619]; forecasts for
D1/D2 wrong in direction. Panel round 1** (`review.md`, three approve with findings): D2 is the clean
comparison (same past, no later bearings); D1/D3 include an ownship turn in 98% of windows and a median
29 min of later bearings; averages with wide spread ((a) better in about 4 in 10, twice as bad in a
third); 2-hour ctl-prior over 2-hour ctl is supplement only (1.49, median 1.14); cost about 2.1× per
engagement-hour for the whole job. Spec 029's 1-hour recommendation withdrawn; spec 028's `ctl-prior`
on 2-hour windows stands. Write-up `site/blog/2026-11-20-held-comparators.md`, slides
`2026-11-20-held-comparators-slides.md` (figures `scripts/research/cmp_charts.py`). Recommended
(owner's choice): close the long-engagement track with a synthesis; or legs longer than the window;
or reopen with new information. Seeds 365, 366 used; the next fresh seed is 367.

032 (the carried prior where the ownship's legs outlast the window, `specs/032-long-legs/`; owner
2026-11-20 "test ownship legs longer than the 2-hour window"; a registered study, not a gate;
nothing trained). Spec 024's realism with ownship legs of 2–4 h (`configs/long/legs-*.json`),
contact 1, standing 2-hour windows; on blind (turn-free) windows E1 = `ctl` ÷ `ctl-prior`, E2 =
joint solve (`jointheld` at 7200/1800: 3.5 h of past bearings) ÷ `ctl-prior`, harm on one-turn
windows; scorer `long/study32.py` (`tma2-long study32`); `jointheld` always writes its npz. Tuning
on spent seed 366 (`experiments/20261120-legs-tuning/`), decision `20261120-legs-decision/` (code
`babd25bc…`; test raised to 50 + 50 on tuning's yield), validation 367 (`20261120-legs-val/`,
soundness passed), **test record `experiments/20261120-legs/` (seed 368, 85 decided blind windows):
E1 "ctl-prior better" 1.537 [1.156, 2.029]; E2 not separated 1.113 [0.840, 1.445]; no harm (one-turn
1.26). Panel round 1** (`review.md`, three approve with findings): half the blind windows lost
contact (median 72 km) and are unscored (answered: joint 0.99, `ctl-prior` 0.52); a far-range effect
(about 2.2 beyond 35 km, about 1.0 under; range and contact loss inseparable); E1 is "more data
beats no data", E2 the fair comparison is level; the prior came from a window with a turn in 83 of
85; seeds swung (E1 1.32, 0.87, 1.54; pooled 1.37); carried region not calibrated (median d² 0.94
against 3.36; one-turn coverage 0.79). Write-up `site/blog/2026-11-20-long-legs.md`, slides
`2026-11-20-long-legs-slides.md` (figures `scripts/research/legs_charts.py`). Recommended (owner's
choice): adopt 2-hour `ctl-prior` with its guard for the tended contact up to 12 h, joint solve as
the equal alternative; close the long-engagement track with a synthesis. Seeds 367, 368 used; the
next fresh seed is 369.
**Owner 2026-11-21: adopt 2-hour `ctl-prior`.** The standing chained time-late system for the
tended contact on long engagements is `ctl-prior` (spec 028's `carry2`, registered settings: scale
4, tail 1,200 s, guard α 0.001) on 2-hour windows overlapping 30 min, up to 12 h, with `ctl` as the
control and the joint solve as the equal alternative where the bearings are kept. Limits that go
with it: one simulator, contact 1; the claim on blind windows is a far-range one (about 2.2 beyond
35 km, about 1.0 under); windows are placed past true manoeuvres; the carried covariance is not
calibrated and must not be shown as an uncertainty; spec 028's hand-over defect is kept. New
long-engagement studies run `tma2-long carry2` and read `ctl-prior` as the standing system. Not
chosen yet: closing the track with a synthesis.

034 (the long-engagement track as a whole, `specs/034-long-synthesis/`; owner 2026-11-21 "yes,
please try it"; a synthesis: no gate, no registered result, nothing trained, no new seed; numbered
034 because another session's spec 033 (joined periods across long gaps) is on main).
`scripts/research/long_synthesis.py` reads every figure of record from the test records of specs
026, 028, 029, 031 and 032 (and spec 026's supplement) into
`experiments/20261121-long-synthesis/tables.md` and `summary.json`, with two charts. Write-up
`site/blog/2026-11-21-long-synthesis.md`, slides `2026-11-21-long-synthesis-slides.md`; two
reviewers (fidelity, critical) approved with findings, all taken in (`review.md`). The account:
stitched 2-hour `ctl` held up on the tended contact (registered to 12 h; 24 and 48 h one engagement
each); a carried start is not shown to help accuracy and saves about 31% of the search where it
runs; a carried prior beats the same window alone where the window cannot see range (1.7–2.4 on
1-hour windows; 1.54 on one seed, 1.37 pooled, on 2-hour windows, far range only) and is not shown
to beat a joint solve over the same past bearings. **The long-engagement track is closed unless the
owner reopens it** (with measured realism, association, an ownship steered by its own track, a need
for the untended contact or lost-contact answers, a latency requirement, or a case where only a
hand-over can travel).

033 (several periods of one target across long gaps, `specs/033-long-gaps/`; owner 2026-11-20
option 3 of spec 030's order, then "separate the factors", "diagnose the >70 min reversal" and
"write up"; developed as 031, renumbered because another session's 031 and 032 merged first;
a development study, not registered; nothing trained; spent seed 348 only). First, a look at spec
030's records (`experiments/20261120-tl11-flag-look/`, `scripts/research/tl11_flag_look.py`): a
per-period consistency flag on the carried prior is not worth registering (evidence flag AUC
0.52–0.78; even the truth's distance reaches 0.45–0.76 on k4; the twice-as-bad periods are
mostly ones where `ctl` alone landed close). Code: `tma2-tlsolve` takes a split's `long` config
(whole engagements from the long simulator via `long.timelate.period_of`);
`Period.ownship_turns()` reads the long simulator's full turn list when the meta carries one
(generator data unchanged, `tests/unit/test_periods_turns.py`); workflow `tl12ev/**` →
`.github/workflows/tl12-evidence.yml`; `scripts/research/tl12_{readings,paired,evidence,
evidence_summary,charts}.py`. Two runs on the same 40 six-hour engagements, 2–4 periods with
gaps of 30–90 min (`configs/long/gaps-dev.json`, `gaps-hold-dev.json`; plans
`configs/timelate/tl-q-dev.json`, `tl-q-hold-dev.json`): ownship legs 20–40 min
(`experiments/20261120-tl12-dev/`) and 1–2 h (`experiments/20261120-tl12-hold-dev/`, with
`evidence/` and the panel's `review.md`, three approve with findings). Readings: periods without
their own ownship turn gain from joining by about 2 below 70 min gaps (2.24 [1.13, 4.50],
2.13 [1.29, 3.55]); with their own turn not separated; of 18 gap-band intervals one is separated
(held course 50–70 min, 2.85); beyond 70 min 0.80 and 0.71, not separated (medians 0.95, 0.88);
the true gap structure would still help there (2.35, 2.48), so what falls short is choosing the
gap history: in most engagements the Laplace evidence does not prefer the true one (13 of 21
within ±10 units; 123 declared against 178 true); whether search matters is not resolved (the
diagnostic's re-run ran on another CPU family and declared other histories in 5 of 21); k4 (as
tuned in spec 030) level with alone; the joint solve costs 11–16× alone. Suggestion, not a rule:
join a period without its own ownship turn across gaps up to about an hour. **Follow-up (owner
option 3, `experiments/20261121-tl13-evidence/`, histories and errors in one job per engagement,
`scripts/research/tl13_{evidence2,summary}.py`)**: a gain from the true gap structure alone is not shown
(declared refit ÷ gap-true 0.96 [0.67, 1.40], fragile refits; the 2.35/2.48 were the whole true history, which
knows the observed periods' manoeuvres too); beyond 70 min nothing is shown either way (0.97,
median 1.03; interval contains the earlier 0.71); against the better declared fit the truth's evidence
is higher by > 3 in 1 of 21, lower in 11 (the truth's refit does not beat it; search not settled). **Owner 2026-11-21: the
gap track is closed**; the joint solve stands for gaps under about an hour. Write-up
`site/blog/2026-11-21-long-gaps.md`, slides `2026-11-21-long-gaps-slides.md` (figures
`scripts/research/tl12_charts.py`). Owner's choice next: stop; register a gap × own-turn rule on
fresh seeds (369 onward, about 140 periods per band); or first re-check the evidence on the
scored run's own histories on one CPU family. Seeds: none new.

035 (interactive TMA demonstrator, `specs/035-interactive-demonstrator/`; the owner's draft
"Spec 005" in `owner-draft.md`, interview 2026-11-21; not a gate, nothing trained, no seed):
the page `/demo` (`site/src/pages/demo.js`, navbar "Demonstrator"). Drag ownship and target
tracks (legs joined by steady-rate arcs), narrow a time-late window, solve on release in a
module worker (`site/static/demo-data/worker.js`). Code in plain ES modules shared with Node
tests: `site/static/demo-data/js/` (`track`, `scenario` (seeded xoshiro128** bearings), `solvers`
and `solver-info` (`ls-js` = spec 021's `lsq.js`; `layer-cv`/`layer-oracle` = `tl-layer.onnx`,
`PhysicsLayer()` with `k_state` and theta/knots outputs, by `tma2.viewer.demo_layer_export`;
`tlm-s1..3` = spec 016's whole-period model, by `tma2.viewer.demo_tlm_export` from the results
branches, ONNX digests equal to spec 016's export check, `tlm.js` ports its inputs and
`direct_track`; real-time E was dropped at the owner's word), `metrics` (errors across the window, the
known-manoeuvre bound, observability), `codec`, `presets`). LinkML `DemoScenario`, `TmaProblem`,
`TmaSolution`, `DemoSolverInfo` (schema 0.37.0); the page's JSON Schema
`site/static/demo-data/demo-scenario.schema.json` by `scripts/site/demo_schema.py` (`--check`).
Owner decisions: both JS and ONNX solvers; 5 s bearings at 1°; errors over the whole window
(RMS, worst, bound), no reference time; ellipses off by default, never for E; lower charts with
time down the left, each hideable; one screen at full browser width (plot | charts | dashboard).
Checks: `conformance/onnx/demo_node.mjs` (golden `demo/golden-tlm.json` for the model's port),
`demo_page.mjs` (Chromium), golden least squares `demo/golden-ls.json` from Python
(`demo_golden.py`); CI job `demo`. Figures `scripts/research/demo_charts.mjs`.

036 (leg splitters in the demonstrator, `specs/036-leg-splitters/`; owner 2026-11-21 "a demo of
the leg solvers, so we can compare them … two blocks: leg splitters and TMA solvers"; not a gate,
nothing trained, no seed): the page's toolbar picks a **leg splitter → TMA solver**. The physics
layer (`layer`, which replaces `layer-cv`/`layer-oracle`; old names map to `layer` + `none` /
`truth` through `presets.normaliseScenario`) fits legs joined across the splitter's spans.
Splitters (`site/static/demo-data/js/splitters.js`, `arctan.js`): none; truth; Debrief's 2015
arctan slicing (three-parameter arctan law per steady ownship leg, one split, 2-minute buffer,
ZigRatio 0.6, our choice); multi-leg independent slices (recursive, τ = 40 σ²); the arctan law
with **joined legs** (position continuous, velocity steps at knots, forward selection then
re-placement, τ = 25 σ², at most four knots); C (spec 021's port, no evidence, confirmation
through `viewer-data/layer.onnx`, about 3–4 min on a two-hour window). Only the truth splitter
sees the true spans (the worker strips them; tested). A legs panel (found within 120 s, missed,
false, timing) and "Run all splitters" (worker message `compare`). Schema 0.38.0
(`DemoScenario.splitter`, `DemoSpan.stat`, `DemoSplitterInfo`, solution splitter fields). Preset
`two-target-turns` is outside spec 035's golden problem set (`golden: false`). Readings
(`scripts/research/demo_splitters.mjs`, `experiments/20261121-demo-splitters/`; presets only,
anecdotes, σ 1°, five draws): two turns inside ownship legs: joined legs 9 of 10 found, 2.6% median
range RMS (truth 2.0%, Debrief 14.5%, independent slices 37.8% (it splits between the turns), C 8.2%
on three draws with false transitions at ownship's turns, one leg 27%); a turn during ownship's
turn: Debrief blind (31.9%), independent slices 1.4%, joined legs 3.1% (instant knot placed late);
held course: no false split. No splitter wins everywhere. Slides
`site/blog/2026-11-21-leg-splitters-slides.md`; next is the owner's choice.

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
- Spec 014 panel: check a prior's whole density against its Laplace volume, parameter by
  parameter (a test that integrates only one factor missed the duration's volume: the fourth
  such error). Apply one rule for manoeuvres cut by a period's edge everywhere a history is
  compared. A reference with free times can drift into another history: check it still matches
  the truth before calling it that. Never hand-copy a table row: generate tables from the
  summary. Report a decided statistic at every registered sensitivity value, not only the
  class shares. A forecast from one tuning seed of 134 periods is a guess (D1: 0.79, 0.30,
  0.43). Before running an adaptive rule, run it on noise alone. "At no cost" needs the counts
  by case, not a pooled median. A fixture pinned to 1e-9 fails on another CPU family; pin the
  well-determined outputs tightly and the rest loosely.
- Spec 015 panel: a repair to a reference changes every statistic that reads it; report the
  decided figure under each way of fitting the reference, not only the registered one. A fit told
  the true times knows more than which history is right. Do not register as a decision rule a
  line you forecast as a coin's toss at the planned sample size; and when a rule returns "no" by
  a hair, report the rule's output as the outcome and do not reword it as a judgement. Test a
  density-volume pairing at the edges of the support and at solver bounds, not only inside.
  Comparing one Laplace mode with "no manoeuvre" is not the evidence for "some manoeuvre":
  integrate over where it might be. Report a class share at every registered threshold. Commit
  the script that checks a README's numbers, or do not claim the check. A forecast written from
  a development run minutes earlier is a restatement, not a prediction.
- Spec 016 panel: a registered comparison is only as wide as its narrowest part: thresholding a
  model's manoeuvre probability at an untuned 0.5 and fitting a classical layer at those spans
  measures the detector, not the model. Tune both sides or neither, and score the learned side on
  validation as soon as the order allows. Report the median per-period ratio and the shares over
  twice as bad beside any geometric mean (the 20% was a tail; the median was 1.00), and split a
  loss by whether the two sides agree on structure. Read a "level" pooled ratio by how tight the
  bound is and on course and speed before writing "level". A held-out condition inside the
  training ranges is not a mismatch for the model. A reference fitted to unedited bearings is no
  yardstick under outliers. Keep the declared and undeclared variants of a control in separate
  rows. Record the weights' digest in the scored record, not only in shard headers. A change of
  shard size reaches every system that starts from C″. Never edit a file the decision record
  binds while its run is in progress, even to add a field; put new readings in a new script.
- Spec 017 panel: before registering a recommendation's logic, check each condition could fire
  on tuning data and that it measures cost, not counts (a pooled miss rate hid that 22% of
  periods carried 69% of the gap), and state its sensitivity to the matching tolerance. Split any
  pooled "share" by the kind of period before naming it. A single-omission detectability is not
  additive: check joint omission before calling manoeuvres hidden. A reference told true times is
  flattered even with the right structure; do not call an estimand built on it a bound. A filter
  with no state on early rows drops most periods from a paired period-median: report the period
  count beside every paired ratio. A test value inside the tuning interval is not a disagreement.
- Spec 018 panel: a second design tuned on the same seed has no forecast value: spend a small
  fresh seed on the direction before a five-hour test (validation's 60 periods already said it).
  Before building a selector, check that the selection score ranks the candidates by error
  within a case (the evidence did not rank the priors). Report a reference's gain with its
  concentration (drop the ten best periods) and its losses; do not call it a ceiling. A factor
  fitted on one seed is not a calibration: give coverage a period-bootstrap interval, and do not
  register a band whose edge the tuning value sits on. A fixed member that refits shared
  candidates is not a search under that prior. Splits that reuse the same periods under other
  errors are not independent samples. A comparison is unfair by construction where the control
  contains the split's own prior and the challenger cannot. When an interval's limit is within
  0.02 of the line, print three decimals. `timelate.yml` shards: about 45 minutes per ten
  shifted periods under `run6`, up to 130.
- Spec 019 review: never drop only the best (or only the worst) cases to ask whether a gain is
  a tail: with per-case log ratios of sd about 1, a true ratio of 1 reads 0.85 without its ten
  best of 130. Trim both ends, and give the shares better, twice as good and twice as bad. In a
  synthesis, quote each figure with its system (declared or undeclared) and its reference's
  convention; state a control's known faults beside its gains; use a panel's wording for a null
  ("not shown, at this budget"), not "no". A blog post that links a post not yet written fails
  the site build: add both in one commit. `run7` costs about 450 s a period (eleven searches).
- Modal: functions must be defined at module scope with the decorator; functions built in a loop
  with `serialized=True` cannot be imported in the container ("the 'modal_train' module is not
  available"), and Modal retries the failed start for as long as the client waits. Bound the
  workflow step with `timeout`. The ledger loses a replaced container's time.
- A script that writes a record must run under `uv run python`: a plain `python3` here has no
  torch, the script fails, and a chained `git commit` still commits whatever else was staged
  (spec 016's decision record took two commits). Check the commit holds what its message says.
- Modal rate-limits app creation: of five `modal run` jobs started within ten seconds, two were
  refused ("App create rate limit exceeded") before any container started. Launch GPU plans a
  minute apart, or re-run the refused workflow run (the plan and its digest are untouched).
- Spec 020: the browser runtime (onnxruntime-web WASM) can differ from Python's onnxruntime by
  more than the 1e-5 element-wise tolerance on an off-diagonal covariance element of an
  ill-conditioned row, while state and flags agree to 3e-6. Compare a covariance on its own
  scale (|ΔP_ij| / √|P_ii P_jj|) and report the element-wise figure. Never give a static folder
  the name of a page's path (`/viewer` and `static/viewer/`): which one a host serves is
  ambiguous, so the data live in `static/viewer-data/`. Hooks after an early
  return break a React page: compute every `useBaseUrl` first.
- Spec 021: compare a port by its decisions, not its intermediates. Least squares can land in
  another minimum at one row (relative 75), and the GLR basis's 1e-6 cutoff is discontinuous,
  yet every decision matched. A numba `np.sum`/`mean` and NumPy's pairwise sum differ in the last
  bits, and a float32 pack column is averaged in float32: port the summation order (`codes.js`).
  `onnxruntime-web`'s `ort.node.min.mjs` runs the same WASM build under Node, which is much
  faster for development than a browser.
- Spec 023: a window cut to start after a target manoeuvre is off the global row grid; stitch
  on each window's own rows, never on `arange(0, n, every)` (the 24/48-hour tracks answered 14%
  and 4% of rows until fixed). A shard that recomputes a whole-engagement quantity reports it
  once per shard: average, do not sum. GitHub artifact download URLs are signed for ten minutes:
  fetch each one right after asking for it.
- Spec 024: a CPU-family difference moves `ctl`'s search by kilometres on a window (2.5 km
  between EPYC 9V45 and the session container): compare systems within one job, never a run
  against another run's record. A block-incremental segmenter that crops a longer history is
  not the per-window segmenter: test equivalence at block length one and then check error by
  position in the block. A PR merged while its branch has new commits: open a new PR from the
  same branch rather than rebasing under a running CI job.
- Spec 025: a fit's rows share one error, so a soundness statistic pooled over rows has the
  power of the number of engagements, not of rows: register a per-engagement statistic with an
  engagement interval, check its expected value under its own model (a geometric mean of
  |z|/0.6745 is 0.79 for a perfect reference), and list runaway engagements. Never generate a
  fresh seed locally before registering, even to count it. Splits built on the same seed with
  a mismatch overlay are the same engagements. When rows are chosen by a bound the joined data
  satisfy, report the ratio on rows each side determines alone beside it.
- Spec 026 panel: a chained system's first window equals the control by construction; a
  per-window rule over all windows counts those as ties and moves the decision (E1 passed by
  0.008 with them, 0.0002 without). Exclude constructed ties in the registration, or report
  the rule without them beside. A median over answered rows cannot see a filter that stops
  answering: register the share answered as an outcome. Banding by range does not match range
  inside a band. A CPU saving is the saving where the cheaper path runs, not over all windows.
- Spec 027: a carried start can only change which minimum a period's own fit lands in; a
  comparison of it with a joint solve is decided by construction. Before registering, ask
  what information each side's likelihood actually holds. Report ties (unchanged periods)
  beside any ratio whose median is 1.00. A recommendation conditioned on the deciding split
  must not be drawn from a secondary split.
- Spec 028 panel: when a chained system falls back to the control where nothing was handed on,
  those windows are constructed ties too: exclude them in the registration. Bootstrap units are
  engagements, not (engagement, contact) chains: two contacts share an ownship. A hand-over
  refit started from the full-window fit can keep the overlap's information on a flat valley:
  start it neutrally. Register the soundness check on the population the rule decides (the
  coverage check covered contact 1 while the decided split was mostly contact 2), and run the
  registered settings as a chain on tuning rather than extrapolating a grid. "Same history"
  needs matched times and kinds, not equal counts. Check that each clause of a split can fire
  in the simulator before registering it.
- Spec 029 panel: a window shortened so that it is blind makes its control blind too. A gain
  against the same window alone is "more data beats no data". Register the comparison against
  the control's standing configuration (2-hour windows, a joint solve) beside it. A reference
  fitted on the window alone is no ceiling for a system that carries information in: in chained
  designs it reads as soundness only. A carried start without its prior can cost (0.89 on
  one-turn windows), so do not carry a start alone. `timelate.chain` moves each window start past
  a true manoeuvre, so hand-overs are never inside one: state it as a limit of every chained
  study. Coverage within a band is not calibration: report the median NEES beside it. Never write
  in a tuning record what validation or test will show.
- Spec 031 panel: a stitched longer-window track scored on a shorter window's rows also uses
  later bearings and the next ownship turn: state the latency and the data horizon, and take the
  comparator with the same past (the joint solve) as the clean one. Never compare a system from
  one run with systems from another in tuning either (the tuning flip, D1 1.30, was two CPU
  families). A part that writes no `.npz` when it has nothing to do makes S1 unable to tell
  "nothing to do" from "lost": always write the file. Give the cost per engagement-hour, not per
  window, when windows advance at different rates.
- Spec 032 panel: a design that holds the ownship's course long enough to blind a window also
  opens the range, so half the blind windows lost contact and fell outside the claim; register
  each system's answered share and read the effect by range band. Range and contact loss move
  together in this simulator. A tuning yield of decided windows is a forecast too: 120 planned,
  85 came.
- Spec 034 review: a synthesis's headline must carry each study's comparator and window length;
  "about twice as good" pooled a 1-hour window against itself with a 2-hour reading on one seed.
  Quote cost figures as the panels corrected them (on the windows where the cheaper path runs),
  label every row whose "above 1" reads the other way, and never mistake a bearings-held share for
  an error.
- `long.yml`: a results branch whose history carries workflow edits is refused to the Actions
  token, so the collect step pushes an orphan branch. Pushes to main are ignored: merging a PR
  that changes `configs/long/run.json` re-ran the last study's whole plan.
- Spec 030 panel: a variant chosen to remove a harm seen on one development seed must be
  compared with the uninflated version on the test, or the test cannot say the change mattered
  (it did not). Coverage reached by inflating is not calibration: report the median d² beside
  the coverage. Read a prior's gain on rows the period determines alone before saying it
  improves estimates. A harm rule on 32 periods sees only losses over about a third; state the
  detectable size. Isotropic velocity noise for a turn puts half the change into speed.
- Spec 033 panel: a diagnostic that re-runs a search must run on the scored run's CPU family,
  or compare stored histories: a re-run on another family declared different histories in 5 of
  21 engagements and broke the cross-tab with the errors. Fix bands before looking, or call them
  post hoc; test a trend, not three band means. Split a joining gain by whether the period has its
  own ownship turn before reading it by anything else. A narrow evidence difference (within about
  10 units) is ambiguity, not identifiability, and says nothing about search. When a local job
  keeps dying with the container, move it to a CI workflow at once.
- Spec 035: the demo's ES modules under `site/static/demo-data/js/` are imported by the page
  (bundled by webpack), loaded by the worker at run time and imported by the Node tests; keep
  them free of browser-only globals at module scope. A `package.json` with `"type": "module"`
  in `site/static/demo-data/` keeps Node from warning. `demo_page.mjs` needs
  `PW_EXECUTABLE=/opt/pw-browsers/chromium` in a session whose Playwright is newer than the
  installed browser. Inert knots tie in top-k and onnxruntime breaks ties unlike torch: compare
  a layer's theta and knots through the active knots only.
- Spec 036: a leg split scored by independent slices (each slice its own constant-velocity fit)
  is too flexible: a slice without an ownship turn absorbs a misplaced break through its free
  range, and the drop is flat over a quarter of an hour. Join the legs (position continuous) and
  refit every parameter before comparing splits. A target turn made during ownship's turn is
  invisible to a detector that only slices steady ownship legs. C's leg search takes about 40 s
  in JavaScript on 715 rows (every prefix's cost table); keep it off the default path of a page.
- Spec 022: PR previews live on `gh-pages` at `pr/<n>/`, and a main deploy must exclude `/pr/`
  from its `rsync --delete`. A preview built with another `SITE_BASE_URL` reads the preview index
  from the root (`/gitma2/pr/index.json`), not from its own base. Deleting a preview is deleting
  published material: owner-only.
