---
title: "Kickoff: was it compute? The scaled end-to-end regressor"
date: 2026-11-10T18:00
tags: [kickoff, spec-012]
---

Spec 012 runs the experiment research note 04 proposed and the project never ran: one large
model that regresses the target's state straight from the bearings, trained on a GPU with about
a hundred times gitma's data. gitma's networks sat at about three times the Cramér–Rao bound,
but they were small and trained on 80,000 scenarios. Was that floor compute and data, or the
architecture? The owner asked for it to start now, alongside spec 011.

<!-- truncate -->

## Where we are

- **Gate H** ([write-up](/blog/2026/11/10/gate-h)): under the declared bearing-error mismatch,
  learning the error model on the true segmentation is not worth pursuing; the cost of mismatch
  is in the segmentation.
- **Spec 011** ([kickoff](/blog/2026/11/10/robust-segmenter-kickoff)) is in progress: the
  diagnosis found that outliers make the classical segmenter declare false transitions, and a
  robust version (C-r) is in its pilot.
- **Carried**: C″ as the standing classical system; the tuned IMM and EKF; the oracle.
- **Open since gitma**: whether a large direct model reaches the bound on straight legs
  (research note 10, §5).

## Where this task moves to

- **SRD** §5 and §7; spec `specs/012-scaled-regressor/`. No gate: the model is a **control**,
  never the project's estimator (the constitution requires the reported estimate to come from a
  physics layer, and this model has none).
- **Read by**, fixed before any GPU run:
  - *Held course*: efficiency (error over the bound) on settled rows. **Reaches the bound** if
    its interval is wholly below 1.25; **flat floor** if wholly above 2.0 and not improving with
    geometry; otherwise partial. Batch least squares on the same rows should read 0.95–1.01.
  - *After manoeuvres*: paired differences against C″ and the IMM.
- **Plan**:
  1. Training code and an on-the-fly data stream (about 10⁷ scenarios from seed 326), tested at
     toy size on CPU.
  2. A `gputrain/**` workflow that starts a detached GPU run and brings weights and metrics back.
  3. Decision record: architecture, sizes, budget split, readings, forecasts.
  4. Pilot, then three seeds, inside the cap.
  5. Score on CPU with the existing scorer (validation seed 327, test seed 328); panel review.
- **Budget** (owner, 10 November): one month of free GPU credit, about 50 T4-hours, as a hard cap.
- **Owner-only prerequisites**: the GPU account, a spending limit and two repository secrets.
  Steps 1 to 3 do not need them.
- **Risks**: the cap is too small to train the model to convergence (the pilot decides the size,
  once, before the three seeds); a result between the two readings; GPU runs are not
  bit-reproducible (three seeds, hardware and versions recorded).
- **What each outcome means**: reaches the bound, and the physics layer is not needed for
  precision, so the design question reopens with evidence. A flat floor, and gitma's result was
  architecture: the hybrid design stands.

## How progress will be shown

- **Efficiency by geometry band**, the regressor's three seeds beside batch least squares (test
  seed 328).
- **Error against scenarios seen** during training, with the tenth-of-the-data control.
- **After manoeuvres**: the regressor, C″, the IMM and the oracle, with paired intervals.
- **Track plots** of the regressor, C″ and the oracle on one representative engagement, at
  zig + 10 and zig + 20 min.
