---
title: "Generator 0.6.0: the owner's manoeuvre model, and its pipeline gate"
date: 2026-11-04
tags: [generator, pipeline-gate, results]
---

Steady-leg segmentation (spec 005, Gate S) uses the owner's thresholds: a leg is at least 5 min,
a transition at least 1 min. Generator 0.5.0 did not fit them. Its target legs lasted 4 min at the
median and its turns took 50 s. The owner chose to change the simulation to the stated manoeuvre
model rather than the thresholds to the simulation. Generator 0.6.0 is that model. Its pipeline
gate, G0-MAN2, passed after two rounds of the agent review panel.

<!-- truncate -->

## The model

Called MAN2 (SRD Annex B), the model works as follows:

- **Target legs** last N(25, 9.1) min with a 5-min floor, so 5% are 10 min or less and 5% are
  40 min or more. This is the owner's "typically 10 to 40 minutes with a bell curve, only turning
  at 10 minutes on 5% of occasions".
- **Leg ends** are a course change (80%), a speed change (10%) or both (10%). They come at slower
  rates than 0.5.0's, so a transition takes about a minute or more. The median is 116 s.
- **Windows** last 40–120 min, up to 720 rows at 10 s, against 0.5.0's 360.
- **Ownship** steers with helm wander (an autoregressive course error clipped at ± 4°) or
  autopilot oscillation (1–3°) on each steady leg. Its turns are unchanged.
- **Target changes** may now overlap the ownship's zig. That happens in 13% of engagements.
- **0.5.0 compatibility:** all of this sits behind new ranges fields, so 0.5.0 ranges reproduce
  0.5.0 byte for byte. Seed 304's 10,000 validation scenarios regenerate identically.

## The gate

The checks were fixed before the first run (`specs/006-generator-man2/g0-checks.md`). On the
record of decision (`experiments/20261104-g0-man2-r2/`), all 17 pass:

| Check | Result |
| --- | --- |
| gitma's fixtures, regenerated | byte-identical |
| two or more target changes per engagement | 93.5% (≥ 60%) |
| change kinds | 0.798 / 0.101 / 0.101 (each within 2 points) |
| ownship course off its planned leg | 4.00° worst (≤ 5°) |
| noise-free zig leg, least squares and physics layer | 9.3e-6 relative range error (≤ 1e-3) |
| straight-leg IMM NIS | 1.018 (0.75–1.3) |
| least-squares speed efficiency on the zig leg | 1.010 (0.8–1.3) |
| physics layer equals least squares, 720-row windows | 7.6e-5 (≤ 1e-4) |
| 720-row export, Python / browser / Java | 3.1e-10 / 2.3e-10 / 3.1e-10 (≤ 1e-5) |
| kernel throughput | 26,666 scenarios/s (≥ 10,000) |

### The zig leg

gitma's noise-free check fits batch least squares up to the target's first manoeuvre. On MAN2
data, that manoeuvre can come before the zig, where range is not yet observable. So the check now
fits the steady target leg that contains the zig, alone.

## What the panel changed

Five independent reviewers covered TMA geometry, numerics, statistics, reproducibility and a red
team. In round 1 the red team rejected, and the others approved with findings. Three findings
mattered.

- **The 720-row export check never used a row past 240.** Its golden batch had shrunk to two short
  scenarios. The fix masks bearings before the zig leg and takes only legs ending at row 480 or
  later.
- **The browser and Java results were bound only to the model's digest.** That digest does not
  change when the test inputs do, so stale results would have passed. Both legs now record a
  digest of the inputs too.
- **The pre-registration had dropped two checks the spec required.** These were the tracker NIS
  check and the efficiency check. Both were registered before their first run, and both pass.

Two criteria were changed after a result, both by the owner and both recorded:

- **Check 4 coverage.** The noise-free check skips 42% of scenarios. The 20% limit set beforehand
  was wrong for the leg model: with 25-minute legs, about 40% of zigs fall too close to a target
  change. The limit became "at least 500 of 1,000 fitted". The accuracy limit is unchanged.
- **Throughput method.** Throughput is now timed on the path training uses: the numba kernel on
  four threads, with nothing else running. The one-thread Python loop gives about 7,600/s and is
  reported beside it.

## What it leaves open

- **The knot path at 720 rows is untested.** The physics layer's knot path has not been checked
  for equivalence or export conformance at 720 rows, and Gate S needs it.
- **The noise-free check is weak against off-by-one errors.** It would catch a one-row bookkeeping
  error at the leg's ends only through its worst case.
- **The IMM and EKF need re-tuning.** They are being re-tuned on the new validation split (seed
  314), and the GLR + confirm reference is re-measured on it, before spec 005's decision record.
