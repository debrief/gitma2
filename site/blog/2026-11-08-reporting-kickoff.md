---
title: "Kickoff: reporting plans and progress, two posts per task"
date: 2026-11-08
tags: [kickoff, process]
---

The owner asked for progress to be visible before and after each task, not only at gate verdicts:
a post that says where we are and where we are going when a task starts, and an illustrated deck
with charts and track plots when it ends. This task sets that up and uses it on itself.

<!-- truncate -->

## Where we are

- **Gate 2 passed** on the owner's manoeuvring scenarios, decided by the panel in round 2
  ([write-up](/blog/2026/11/08/gate-2)). E, the learned model, beats the classical segmenter C by
  +0.025 of the one-leg-to-oracle gap; most of that is two rules a designer could write, and the
  learning beyond them is +0.007 [+0.001, +0.012].
- **Carried**: E, with C″ (zig veto and fixed fade, nothing learned) as a standing control.
- **In progress**: spec 008, uncertainty calibration (Gate 3). Test seed 320 is reserved for it.
- **Reporting so far**: five gate write-ups, critical in substance, no figures. P0 had no post
  until today's [backfill](/blog/2026/11/01/gate-p0). Nothing describes direction between gates.

## Where this task moves to

- **Constitution 1.3.0**: two posts per task (a Spec Kit feature or a gate run), a kickoff before
  implementation and a slides post before the PR. Owner-merged, as every constitution amendment.
- **Practice**: `AGENTS.md` (Reporting), a [process page](/process/reporting), two post templates,
  a reveal.js deck template, and Spec Kit after-hooks so `/speckit-specify` writes the kickoff and
  `/speckit-implement` builds the slides.
- **Tooling**: `tma2-plot`, a CLI that draws track plots (ownship blue, target red, each
  estimator's belief with 1-σ ellipses at named times) and error curves from any truth split and
  prediction files, with a provenance sidecar per figure.
- **Plan**: plotter and tests; documents and templates; hooks; a P0 backfill post; this kickoff;
  the slides post for this task from a seeded demo split; PR.
- **Risks**: decks for small changes become boilerplate (so the rule is scoped to specs and gates,
  with dated paragraphs for the rest); a second narrative per gate (so a gate's slides post is the
  write-up's illustrated companion and links to it); figures that cannot be remade (so each has a
  sidecar naming data digests, command and commit). We would stop if the site build or the repo
  grew beyond reason: figures are SVG and kept under about 200 KB.

## How progress will be shown

- A track plot of a near engagement (demo split from seed 316, 12 scenarios, the MAN2 ranges;
  scenario 8, 7.7 km mean range) with batch least squares, the frozen MAN2 IMM and the oracle,
  marked 5 and 10 minutes after the zig.
- A track plot of a far one (scenario 0, 28 km) where the IMM drifts.
- Error curves against time for scenario 8.
- All three made by `tma2-plot` at the PR's commit, with sidecars.
