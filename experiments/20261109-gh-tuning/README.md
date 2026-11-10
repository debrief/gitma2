# Gate H tuning: every condition on seed 320 (spec 010 T013)

**Tuning data only. Nothing here is a gate result**, and nothing on validation seed 321 or test
seed 322 has been generated or scored. Gate H is not yet registered.

- Run 42713888364 (`headroom/tune-all`, plan `configs/headroom/tune-all.json`), commit 1f9cde4,
  clean tree. Results branches `results/headroom-tune-all-<condition>-plan-42713888364`; each
  condition's `headroom.json`, `run.json` and data digests are copied here.
- Seed 320, `train` split of 1,300, the first 500 σ = 1° scenarios, 1,919 G5 rows per condition.
- Robust control at the draft plan's settings (`configs/gateh/gh-draft.json`), not yet tuned.
- IMM and EKF are the white-noise tunings (not re-tuned for mismatch; T016).

## Median relative range error, both sides on the true segmentation

| Condition | Plain solve | Robust control | Attainable ceiling | Ceiling efficiency | R: control over ceiling | Plain over ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| off | 0.0639 | 0.0656 | 0.0639 | 1.57 | +2.7% [−3.2, +7.3] | 0 |
| corr-mild | 0.0921 | 0.0905 | 0.0912 | 1.30 | −0.7% [−5.3, +5.7] | +1.0% [−3.9, +8.7] |
| corr-central | 0.1113 | 0.1050 | 0.1058 | 1.26 | −0.8% [−5.8, +3.9] | +5.2% [−3.1, +13.5] |
| corr-harsh | 0.1257 | 0.1234 | 0.1175 | 1.19 | +5.0% [−2.9, +10.9] | +6.9% [−2.4, +14.9] |
| bias-mild | 0.0682 | 0.0695 | 0.0682 | 1.50 | +1.8% [−2.2, +7.2] | −0.0% [−3.9, +3.3] |
| bias-central | 0.0774 | 0.0801 | 0.0776 | 1.40 | +3.2% [−2.0, +9.3] | −0.3% [−4.7, +5.6] |
| bias-harsh | 0.1124 | 0.1133 | 0.1073 | 1.32 | +5.6% [−0.7, +12.1] | +4.8% [−2.6, +11.4] |
| sigma-mild | 0.0633 | 0.0653 | 0.0633 | 1.54 | +3.1% [−1.4, +7.7] | +0.1% [−2.7, +3.1] |
| sigma-central | 0.0629 | 0.0653 | 0.0634 | 1.52 | +3.0% [−1.5, +8.1] | −0.8% [−3.8, +3.8] |
| sigma-harsh | 0.0644 | 0.0667 | 0.0635 | 1.53 | +5.0% [−0.2, +9.5] | +1.4% [−4.3, +6.6] |
| out-mild | 0.0682 | 0.0669 | 0.0649 | 1.58 | +3.0% [−1.0, +8.9] | +5.1% [−0.5, +11.9] |
| out-central | 0.0865 | 0.0667 | 0.0634 | 1.58 | +5.2% [+0.2, +10.3] | +36.4% [+24.9, +47.6] |
| out-harsh | 0.1174 | 0.0675 | 0.0629 | 1.52 | +7.2% [+1.4, +12.1] | +86.5% [+66.4, +108.0] |
| all-mild | 0.1029 | 0.0930 | 0.0921 | 1.33 | +1.0% [−2.7, +5.0] | +11.7% [+2.8, +18.8] |
| **all-central (primary)** | 0.1378 | 0.1169 | 0.1152 | 1.24 | **+1.5% [−3.4, +6.4]** | +19.6% [+10.6, +31.4] |
| all-harsh | 0.1789 | 0.1502 | 0.1487 | 1.16 | +1.0% [−6.6, +8.6] | +20.3% [+9.2, +30.8] |

Intervals are 95%, paired and scenario-clustered, 2,000 resamples. Efficiency is the attainable
ceiling's range error over the Cramér–Rao bound under the true covariance, settled rows.

## Reading (tuning data)

- **On the primary condition the untuned robust control is already within 1.5% of the ceiling**,
  and the interval lies wholly below the 10% threshold. If validation and test agree, the
  verdict is "not material". The mild and harsh combinations say the same (+1.0% each).
- **Outliers are the only kind that hurts the plain solve badly** (+36% at 2%, +87% at 5%), and
  Huber weighting alone removes nearly all of it. That is a textbook fix, not learning headroom.
- **Correlated error and bias hurt every estimator, the ceiling included.** The plain solve's
  error rises from 0.064 to 0.111 (correlated, central) and 0.077 (bias, central), but the
  ceiling's rises with it. The loss is information the bearings no longer carry, not knowledge
  of the error model that an estimator could learn. Knowing the model is worth about 5% at most.
- **An untold σ costs nothing.** The solve's point estimate does not depend on a common scale.
- **The control costs about 3% where nothing is wrong** (off: +2.7%), all of it from the Huber
  weights (whitening alone and σ alone cost nothing). The settings grid (T015) should reduce it.

## Two things to settle before the decision record

1. **H-b as drafted cannot be decided at these sample sizes.** It asks for the control's cost on
   clean data to be at most 2% with the interval wholly below. The interval's half-width is
   about 5 points on 500 scenarios and would be about 3.5 on validation's 1,000.
2. **The ceiling is not at the bound** (efficiency 1.2–1.6, and the plain oracle is 1.57 on clean
   data). This is the oracle's known chord approximation of manoeuvres, not the mismatch
   handling: the efficiency improves as mismatch is added. H-a's band must be set from the
   clean-data value, and the write-up must say the ceiling is the ceiling *of this solve*.
