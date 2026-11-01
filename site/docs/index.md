---
id: index
title: Welcome
slug: /
---

# TMA via ML, second attempt

Can a learned component, trained end to end with explicit bearing geometry, be at least as
accurate as batch least squares wherever the constant-velocity model holds, and better than a
tuned IMM wherever it does not, with calibrated uncertainty, from a single exportable model?

gitma2 starts from [debrief/Gitma](https://github.com/debrief/Gitma), which showed that a plain
recurrent regressor learns usable range, course and speed from simulated bearings, is more robust
than least squares near unobservability, and beats a tuned IMM after a target turn, but stays about
3 × the Cramér–Rao bound on straight legs. The design here keeps the network for judgement (when
the target manoeuvred, how much to trust each bearing, where to start) and lets a differentiable
piecewise-constant-velocity batch solve do the numerics.

## The gates

| Gate | Question | Status |
| --- | --- | --- |
| P0 pipeline | Does the Python generator reproduce gitma's files, and do the references reproduce gitma's predictions? | **passed** (agent panel round 3, record `experiments/20261101-p0-r4/`): generator byte-identical, references and evaluation equal to gitma's, physics layer equal to batch least squares on every fixture row, oracle reproduced, export agrees across Python, browser and Java |
| Gate 1, constant velocity | Within 1.1 × batch least squares on every metric? | not started |
| Gate D, steady-leg detector | Beats CUSUM/GLR at matched false alarms, under 5% held-leg false alarms, and the piecewise solve it feeds beats the IMM? | not started |
| Gate 2, manoeuvres | Below the re-tuned IMM overall, within 1.1 × least squares on settled rows, half the gap to the oracle recovered? | not started |

Requirements: [`docs/SRD.md`](https://github.com/debrief/gitma2/blob/main/docs/SRD.md) and
[Annex A](https://github.com/debrief/gitma2/blob/main/docs/SRD-annex-A.md). Principles:
[the constitution](https://github.com/debrief/gitma2/blob/main/.specify/memory/constitution.md).
Research: [`docs/research/`](https://github.com/debrief/gitma2/tree/main/docs/research).

All data is simulated. Nothing above OFFICIAL belongs in this project.
