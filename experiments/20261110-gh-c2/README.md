# Gate H, the registered comparison on C″'s own segmentation (spec 010 research R6, FR-033)

**Reported, not gated.** Run 42839164739 (`headroom/gh-val-c2`, plan
`configs/headroom/gh-val-c2.json`), commit 8f381c1, clean tree, exit 0. Validation seed 321, the
first 1,000 σ = 1° scenarios, 3,931 G5 rows, the primary condition and mismatch off. Intervals
97.5%, paired, scenario-clustered. It was run after the test verdict, at the panel's request: the
comparison was registered and had been left out, and its code path had a bug in how C's frozen
parameters were read (fixed in 8f381c1 with a digest check; no estimator changed).

C″ is the standing classical system: C segments at the stated σ (frozen code `4d2c084f…`,
parameters `60e6ee63…`), with the zig veto and the fixed fade, and hands over to the solve.
"C″ + robust" applies the robust control in that final solve only; C's own nominations and
confirmations are untouched.

## Median relative range error

| | Mismatch off | Primary condition | Ratio |
| --- | --- | --- | --- |
| Plain solve, true segmentation (the oracle) | 0.0600 | 0.1300 | 2.2 × |
| Robust control, true segmentation | 0.0604 | 0.1143 | 1.9 × |
| Error-model-informed fit, true segmentation | 0.0600 | 0.1190 | 2.0 × |
| **C″ (C's segmentation, plain solve)** | **0.1018** | **0.2796** | **2.7 ×** |
| **C″ + robust control** | 0.1034 | **0.2303** | 2.2 × |
| One leg / IMM / EKF | 0.554 / 0.553 / 0.532 | 0.565 / 0.617 / 0.553 | |

| Comparison | Mismatch off | Primary condition |
| --- | --- | --- |
| C″ over the informed fit | +69.5% [+55.2, +88.5] | **+134.9% [+114.1, +163.1]** |
| C″ + robust over the informed fit | +72.1% [+57.1, +90.2] | **+93.5% [+75.7, +112.8]** |
| C″ + robust over C″ | +1.6% [−1.2, +3.8] | **−17.6% [−22.2, −13.7]** |
| Share of the one-leg-to-oracle gap recovered by C″ | 0.92 | 0.66 |
| the same, C″ + robust | 0.91 | 0.77 |

In operational units, primary condition: median range error 4,120 m for C″ and 3,460 m for
C″ + robust, against 2,000 m for the plain solve and 1,710 m for the robust control on the true
segmentation. Median course error 29° and 25° against 13° and 11°. Range within 10% by
zig + 10 min: 7% and 9% of engagements against 21% and 27%.

## Reading

- **This is where the mismatch hurts the system.** With the true manoeuvre times, mismatch
  doubles the error. On C's own segmentation it nearly triples it. The loss attributable to
  segmentation (C″ against the plain solve on the true segmentation) is 0.042 with no mismatch
  and 0.150 under the primary condition: more than three times as large. C recovers 0.92 of the
  one-leg-to-oracle gap on clean data and 0.66 under mismatch.
- **The robust control helps more here than on the true segmentation** (−17.6% against −12.0%),
  but it only treats the final solve. What remains, C″ + robust against the same control on the
  true segmentation, is a factor of two (0.230 against 0.114).
- **So Gate H's verdict and this table are both true, and they answer different questions.**
  Knowing the *error model* is worth nothing measurable to the solve once the segmentation is
  right. Getting the *segmentation* right under mismatch is worth a factor of two. The panel's
  red-team and domain reviewers predicted this; the gate's design (both sides on the true
  segmentation) could not see it.

## What this does not show

- **It is not evidence for learning.** C was tuned on clean data and run unchanged: its
  nominations divide by the stated σ, its confirmation costs assume white noise, and nothing
  robust reaches them. The obvious first step is classical: C with the robust control's σ and
  correlation estimates and Huber costs in its own tests. Until that control exists, the factor
  of two is headroom for a better segmenter of any kind.
- **Which kind of mismatch breaks C is unknown**: only the combined condition was run. Outliers
  (false nominations) and correlated error (which mimics a manoeuvre) are the candidates.
- **Whether C nominates falsely or misses** was not measured: no segmentation metrics here, only
  the downstream error.
- Validation seed only, 1,000 scenarios, one condition. Not a gate, no pre-registered criterion,
  and it was run after the test result was known.
