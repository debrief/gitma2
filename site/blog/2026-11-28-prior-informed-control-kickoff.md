---
title: "Kickoff: a classical control that is told what the regressor is told"
date: 2026-11-28T14:00
tags: [kickoff, spec-039]
---

Twice now the control meant to test whether the regressor's gain is prior knowledge could not
move the classical solve, so its null said nothing. This task builds the control that can: a
classical estimator told the generator's own distribution of range and limits on speed, which
reports the centre of its posterior and not the peak of a likelihood. Nothing is trained and no
GPU time is used. Spec: `specs/039-prior-informed-control/`.

<!-- truncate -->

## Where we are

- [Spec 038](/blog/2026/11/28/gain-decomposition): classical hardening closes part of the
  regressor's lead under bearing errors; the ownship-only prior explains nothing, and was too
  weak to test anything. Three reviewers approved with findings.
- The lead that points at a prior: against a robust solve told the true manoeuvre times, the
  regressor wins in range where the bound is loose (1.15 clean, 1.34 under mismatch) and loses
  where it is tight (0.77, 0.93).
- Standing: C″ for real-time estimates, C frozen. Nothing was carried from spec 038.

## Where this task moves to

- SRD §5 and §7; a registered study, not a gate. Nothing is carried by it.
- Plan:
  1. A read-out that profiles the robust solve's cost over the target's range at the scored row,
     weights it by the generator's distribution of range and its limits on speed, and reports
     the posterior median.
  2. Applied to the true manoeuvre times, it is a reference told everything but the bearings'
     errors. Applied to C″'s segmentation, it is a causal classical system told the priors.
  3. On spent seeds: show it moves the solve, choose its settings, read it by thirds of the
     bound.
  4. On development data, the time-late evidence search under the manoeuvre prior, cut at the
     scored row, with its cost.
  5. Register, then score fresh seed 373 once; three reviewers.
- Judged by: the share of the regressor's loose-bound advantage over the told-truth solve that
  the priors remove, with no loss where the bound is tight; and the share of the gap from
  C″-robust to the regressor that the priors close in a causal system.
- Risks: under bearing errors the stated sd is wrong and the posterior too narrow; a profile
  costs tens of solves per row; the cut evidence search may be too slow to register.
- Stop rule: a control that does not move the solve on development data is not registered.

## How progress will be shown

- Told-truth solve, prior-informed told-truth solve and regressor by thirds of the bound, clean
  and under mismatch.
- The gap from C″-robust to the regressor with and without the priors.
- A range profile of one engagement: the likelihood's valley, the prior, the posterior and where
  each estimator lands.
