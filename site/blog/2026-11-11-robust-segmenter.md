---
title: "The robust segmenter: what broke C, and why the fix was a threshold"
date: 2026-11-11
tags: [write-up, spec-011]
---

Spec 011 set out to build a robust classical segmenter and gate it. It stops earlier, on the
tuning seed, with no gate: the robust test we built does no more than raising the frozen
segmenter's threshold, and neither closes most of the gap. The owner chose to publish this and
move on. Nothing here is a gate result; every figure is from tuning seed 323.

<!-- truncate -->

## What was asked

Gate H's last comparison showed that bearing-error mismatch costs most in the segmentation:
the standing classical system C″ went from 0.102 to 0.280 in median relative range error under
the primary condition. [Spec 011](/blog/2026/11/10/robust-segmenter-kickoff) was to find out
what breaks C, make its tests robust by classical means, and measure the share of the gap
closed on fresh seeds.

## What broke C

On 150 engagements, with each mismatch kind alone and all four together
(`experiments/20261110-gr-diagnosis/`):

| Mismatch | C: median range error | False transitions | Missed changes |
| --- | --- | --- | --- |
| None | 0.131 | 248 | 406 |
| Bias | 0.128 | 283 | 394 |
| Untold σ | 0.120 | 230 | 389 |
| Correlated | 0.214 | 643 | 350 |
| Outliers | 0.236 | 923 | 368 |
| All four | 0.306 | 1,126 | 358 |

- Outliers, then correlated error, make C declare transitions that are not there. Misses do not
  rise. Bias and an untold σ do nothing at this severity.
- Outliers' loss is the segmentation's (+0.091 [+0.054, +0.148] of +0.105). Correlated error's
  is mostly lost on the true manoeuvre times too.
- Handing C the true change starts as nominations does not help: the false transitions enter
  at confirmation.

## What a better segmenter could yield

With the robust final solve everywhere (`.../yield/`):

- True manoeuvre times: 0.116 under mismatch, 0.057 clean.
- C″ on the bearings it is given: 0.250 under mismatch, 0.122 clean.
- C″'s segmentation of the *clean* bearings, applied to the mismatched ones: 0.165.

A segmenter as good under mismatch as C″ is on clean data would close 0.63 [0.46, 0.81] of the
gap and still sit 43% above the reference. On clean data C″ is already about twice the
reference. The 10% "closed" verdict the owner registered could not have been met by any
segmenter of C's quality; that was known, and stated, before any design was scored.

## What we built, and what it did

C-r is C with only its confirmation test changed: each hypothesis fitted by Huber-weighted
least squares and compared on Huber cost (`src/tma2/segment/robust.py`). C's code and
parameter digests are unchanged, and with plain costs C-r reproduces C exactly.

On the same 150 engagements (`experiments/20261111-gr-choice/`):

| Confirmation test | Range error | Share of the gap closed | False transitions | Misses |
| --- | --- | --- | --- | --- |
| C″ as frozen | 0.254 | 0 | 1,137 | 361 |
| Huber 2.0 | 0.236 | 0.13 [−0.11, +0.38] | 815 | 380 |
| Plain C, threshold × 2 | 0.223 | 0.22 [−0.02, +0.41] | 807 | 383 |
| Plain C, threshold × 3 | 0.213 | 0.29 [+0.05, +0.50] | 600 | 442 |
| Huber 2.0, threshold × 2 | 0.217 | 0.27 [+0.01, +0.52] | 464 | 439 |

- The robust test removes 28% of the false transitions under mismatch and leaves clean data
  alone, as designed. Doubling the threshold removes as many.
- No pair of variants is separated. Under the rule declared before these data, the robust
  variant is not carried: the "robust segmenter" would be C with its threshold tripled.
- Removing 59% of the false transitions moves the error from 0.254 to 0.217. Every cut in false
  transitions brings more misses, and about 30% of true changes are missed even on clean data.

## Criticism

- **The design was aimed at half the problem.** The diagnosis counted false transitions rising
  and misses not rising, and the design followed the change. But the gap that matters is to
  the true manoeuvre times, and misses are a large part of it with or without mismatch. The
  yield measurement said so before the design was scored; the design was not revisited.
- **The trivial control was registered only because of an earlier panel.** Without the
  raised-threshold lines, Huber's 0.13 would have been reported as a modest success.
- **The sample decides nothing.** 150 engagements cannot separate a share of 0.13 from 0.29.
  The plan allowed no more on a tuning seed; a gate would have been needed, and the owner
  judged a gate on a threshold re-tune not worth its cost.
- **C's threshold looks low on clean data too.** Every raised-threshold variant reads better
  than the frozen C with no mismatch (none with an interval excluding zero). C was frozen at
  Gate S with a different final solve. This is untested on a fresh seed and is not a result.
- **The outlier model is the one Huber weights were made for** (independent, additive, 10 σ).
  That the robust test still did not beat a threshold is the more notable for it.
- **Two CI runs were lost to plan and quoting bugs** in the workflow, about two and a half
  hours. An early failure check is now part of every launch.

## What is kept

- The diagnosis and yield measurements, and the tools: `tma2-hpredict --segments-from`,
  `--segmentation c2r`, `--dump-segmentation`; `scripts/research/gr_diagnosis.py`.
- C-r's code, tested, as a reference implementation of a robust confirmation test.
- Seeds 324 and 325 are unused; the next fresh seed stays 324 for whoever needs it, after
  spec 012's 326 to 328.

## What follows

- C stays frozen and C″ stays the standing classical system.
- In [spec 012](/blog/2026/11/10/scaled-regressor-kickoff) the regressor is also reported
  beside C with a raised threshold, so that it faces the best classical system we know of. That
  line is reported, not a reading.
- The open question this leaves is misses: changes that leave too little trace to confirm.
  Research note 08 found most changes are like that. It is a limit of information before it is
  a limit of method, and no spec is proposed for it here.

Slides: [the illustrated companion](/blog/2026/11/11/robust-segmenter-slides).
