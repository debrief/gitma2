---
title: "Kickoff: a carried prior across gaps"
date: 2026-11-19
tags: [kickoff, spec-028]
---

Spec 027 showed that handing the next period only a starting point does almost nothing:
the period's own bearings decide. This task hands it a *prior*: the previous period's state and
uncertainty, run through the gap with room for a manoeuvre the gap may hide, inside the next
period's evidence. It is the sequential approximation to the joint solve, scored first on spent
seeds (owner, option A). Nothing is trained.

<!-- truncate -->

## Where we are

- [Spec 027](/blog/2026/11/19/carry-across-gaps): joining beats a carried start (Annex B 2.33
  [1.66, 3.43]); the carried start ties with `ctl` alone in about half of periods.
- The joint solve is the standing time-late system for several periods of one target.

## Where this task moves to

- Spec `specs/028-carried-prior/`: a Gaussian prior on each later period's starting state,
  applied through wrappers so no registered code changes; equal to `ctl` with no prior.
- Development readings on spec 027's spent test engagements: carried prior against joining,
  against `ctl` alone and against the carried start; and whether the carried uncertainty is
  honest.
- Then a proposal: register a study on fresh seeds, or stop.
- Risk, already seen on three engagements: the previous period's Laplace uncertainty is
  overconfident where its fit is wrong, so the prior can pull the next period away from the
  truth.

## How progress will be shown

- The ratios by split and by kind of period; how often the truth falls inside the carried
  two-sigma ellipse.
