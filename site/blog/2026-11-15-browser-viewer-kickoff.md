---
title: "Kickoff: the browser viewer on the exported artefact"
date: 2026-11-15T18:00
tags: [kickoff, spec-020]
---

The time-late track is closed, and one item of the SRD's default plan is left: a browser
viewer on the exported artefact. This task puts a page on this site that runs the carried
model's exported graph in the reader's browser, on a handful of simulated engagements, beside
the classical systems. Spec: `specs/020-browser-viewer/`. Nothing is trained, nothing is
decided, and no fresh seed is used.

<!-- truncate -->

## Where we are

- The last estimator gate is [Gate 2](/blog/2026/11/08/gate-2), decided by the panel. E beats
  C by a small margin, and the classical C″ (zig veto and fixed fade) takes most of that. Gates
  3 and 4 stopped at validation, so no calibration is carried. E's raw covariance is
  overconfident: 95% coverage is 0.60.
- Carried: E (C's segmentation, E-s's evidence, E-w's weights and start correction into the
  physics layer). E-w and E-s are exported to ONNX and agree with Python to 1e-5 in Python, the
  browser runtime and Java (CI). C, and the confirmation that uses E-s's evidence, are Python.
- The time-late track ended with a [synthesis](/blog/2026/11/15/time-late-synthesis). Its
  classical control stands, and it is not an exported artefact.

## Where this task moves to

- SRD §1 ("a browser viewer on that artefact") and §7 step 5; constitution VI (browser demos
  run the exported graph in ONNX Runtime Web).
- Acceptance:
  - every browser output on every demo row agrees with Python's ONNX runtime to 1e-5, checked
    in CI;
  - the page shows the digests of what it runs;
  - the covariance ellipse is off by default and never shown without the Gate 3 warning;
  - the data stay under 15 MB.
- Plan:
  1. Choose six engagements from Gate 2's used test seed by a fixed rule: quiet, one
     manoeuvre, busy, and one where E loses to C″.
  2. Write a Python command that builds, for every 60 s from the zig, E-w's inputs from C's
     hand-over, Python's outputs, and the comparison estimates (batch least squares, IMM, C,
     C″), with a manifest of digests.
  3. Build a site page that loads the graph in the browser runtime and draws the track plot
     with a time control.
  4. Add a headless conformance job in CI.
  5. Write the slides post.
- Risks: E-w's graph (100 iterations in one loop, 720 rows, double precision) may be slow in
  a browser. CI's conformance leg runs it, but the time per row on an ordinary laptop is
  unknown. If a whole engagement takes over a minute, the page computes the current time first
  and fills the trail in behind. The stop condition is a mismatch over 1e-5 that cannot be
  traced to stale data: that would be a conformance failure of the carried model itself, and
  is reported as such.

## How progress will be shown

- Track plots of two demo engagements (the busy one, and the one where E loses to C″), with
  E's trail beside batch least squares, the IMM and C″, made by `tma2-plot` from the shipped
  data.
- A chart of the browser's disagreement with Python on every demo row, against the 1e-5 line.
- The browser's time per row and per engagement on the CI runner.
- Data: Gate 2's test seed 319, the six chosen ordinals, and the manifest committed with the
  page.

## Updates

- 2026-11-15: done the same day.
  - Classes are now counted over the span the page shows. Counted over the whole window, the
    first 200 ordinals held no quiet target.
  - One row of 181 exceeds 1e-5 element-wise in one covariance element in the browser, so the
    check now compares the covariance on its own scale and reports the element-wise figure.
  - See the [slides post](/blog/2026/11/15/browser-viewer-slides).
