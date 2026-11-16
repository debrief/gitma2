---
title: "Kickoff: the carried model end to end in the browser"
date: 2026-11-15T22:00
tags: [kickoff, spec-021]
---

The owner chose to port the classical segmenter C to JavaScript, so that the
[viewer](/viewer) runs the carried model from bearings alone, with nothing prepared in Python.
Spec: `specs/021-browser-segmenter/`. Nothing is trained, no gate, no fresh seed.

<!-- truncate -->

## Where we are

- [Spec 020's viewer](/blog/2026/11/15/browser-viewer-slides) runs E-w's exported graph in the
  browser, on C's hand-over shipped from Python. CI checks it against Python to 3e-6 on 181
  rows.
- The carried model is still [Gate 2's E](/blog/2026/11/08/gate-2): E-s's evidence, C's
  confirmation, and E-w into the physics layer. E-s and E-w are exported graphs. C is Python.

## Where this task moves to

- SRD §1 (the viewer) and constitution VI (the browser as a runtime).
- Acceptance:
  - on at least 30 scenarios of seed 319, the browser's segmentation equals Python's on at
    least 95% of scored rows;
  - every difference is traced to a decision near its threshold;
  - the live estimate matches Python's where the segmentation does;
  - the busiest demo engagement finishes in under 10 minutes on a CI runner.
- Plan:
  1. Export the physics layer as a cost graph, with three-runtime conformance.
  2. Port C's host code to JavaScript: LS states, GLR, search, confirmation, hand-over.
  3. Write a Python dump of every intermediate and a headless comparison, stage by stage.
  4. Add a live mode on the page, and pasted scenarios if time allows.
  5. Slides.
- Risks:
  - **Speed.** C's confirmation needs about 600 physics-layer rows on a busy engagement,
    about 2.5 minutes in the browser, and E's segmentation as much again.
  - **Fragile decisions.** A threshold decision can flip on last-bit differences, so the
    claim is "identical except near the threshold", with the margins reported.
- Stop condition: if the port cannot reach 95% identical rows for reasons other than
  near-threshold decisions, the record says so and the page keeps the shipped mode as its
  default.

## How progress will be shown

- Each stage's agreement with Python (statistic, costs, decisions) on the check scenarios.
- The share of identical rows.
- Every near-threshold decision with its margin.
- Stage times per engagement.
- A track plot from live mode beside the shipped one.
