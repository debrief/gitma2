# Gate S decision record (spec 005 T025–T027)

`decision.json` (a `GateSDecision`) is committed before any training of L (FR-070) and before
test seed 315 is generated (T028). It binds `configs/segment/gs-plan.json` by SHA-256
(`plan_digest`). Later changes are amendments: new files here, listed by digest in the gate
manifest. None may change a criterion once any test result exists.

## Fixed here

- **Annex A §A.9** (Gate S) is on `main` (T025).
- **Segmenter parameters:** from the validation measurements. Each is listed with its source in
  `specs/005-steady-leg-segmentation/research.md`, in the addendum "R1 and R3 on MAN2".
  - search penalty 30 (T021);
  - grid step 6 rows (T010);
  - GLR threshold 4.665, tuned on tuning ordinals 0–499 to `nominator_far` 0.2 and fixed for
    every later run, test included;
  - τ 13.8 and margin 0;
  - Annex B's C = 5°, S = 0.5 kt, D = 10°, D_S = 1 kt, L_min 30 rows, T_min 6 rows.
- **Mode: gap.** It has the lower validation median range error (0.120 against the chord's 0.123).
  The paired difference in gap recovered is +0.006 [−0.002, 0.014], so the choice matters little.
- **Gap normalisation:** raw medians (R7), with efficiency reported beside.
- **References** (frozen by name):
  - IMM `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` (the gated reference, D3);
  - EKF `ekf-sa0.00003-p4-r0.03125` (reported, with the deviation recorded in
    `experiments/20261104-man2-tune-pass4/`);
  - GLR + confirm `glr-q0.2-t13.8`, with thresholds tuned on validation
    (`experiments/20261104-man2-refs/`).
- **Seeds:**
  - validation 314 (`e8150cb0…`);
  - test 315, generated after this record with `--count 100000`, giving a 10,000-scenario test
    split; its digests go to `seed315-digests.json` here;
  - L's stream 317, 10,000 training scenarios at commit `d72cb81`, train split `387013c5…`.
- **S2 on validation:** C − GLR + confirm, gap recovered (range), +0.632 [0.558, 0.734]
  (`experiments/20261104-gs-val/c-final/`). The implied S4 reference is C. S2 is decided again
  on test; if it does not pass there, the better of the two is the reference.
- **S1 limit:** 0.02 (O's contamination P90 on ownship legs; 0 on all of validation).
- **S3 limits:**
  - **Contamination:** L − reference at most +0.01, median and P90.
  - **False split:** L − reference at most +0.05. The spec's proposal was an absolute 5%. A
    difference is used because C itself is at 8.3% on validation (2 of 24 change-free prefixes);
    an absolute limit would fail the reference it protects.
- **Carried rule:** the median of the three seeds by validation gap recovered (range).
- **Shuffled rule:** the shuffled control's gap recovered minus C's must have an interval that
  includes zero or lies below it. Otherwise S4 cannot pass.
- **Criteria, forecast and follow-on:** in `decision.json`. The follow-on is copied from Annex A
  §A.9 and FR-072.

## Choices a reviewer may question

- **One noise draw for L's stream.** Cost tables are computed once per scenario, so spec 003's
  per-epoch re-noise is not used.
- **O's channel in L's features is causal.** O's label for row r comes from O run on the prefix
  [0, r]. O on the whole window would use ownship navigation after r, and labels near a prefix's
  end would change with the prefix.
- **The references were tuned on rows that include validation's scoring ordinals.** This favours
  them on validation, not on test.
- **The S3 false-split measure has few rows.** Validation has 24 change-free prefixes, and test
  will have about 120 among about 5,000 σ = 1° scenarios. Its interval will be wide; it is a guard,
  not a claim.
