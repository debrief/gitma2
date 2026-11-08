---
title: Reporting progress
description: Two blog posts per task, a kickoff and a slides post, and how their figures are made.
---

# Reporting progress

Since 8 November 2026 (constitution 1.3.0, an owner decision) every task reports twice on this
site. A task is a Spec Kit feature (`specs/NNN-...`) or a gate run. The gate write-ups that the
constitution has required since the start continue unchanged; these two posts sit around them.

## The kickoff post

Written before implementation starts, from the specification. It answers three questions in
under a page:

1. **Where we are.** The last gate's verdict, what is carried forward, what is open.
2. **Where this task moves to.** The SRD section it implements, the criteria or acceptance it
   will be judged by, the plan in a few steps, the risks, and what would make us stop.
3. **How progress will be shown.** Which figures the closing slides post will carry.

Template: `site/blog/_templates/kickoff.md`. Command: `/speckit-report-kickoff`, which
`/speckit-specify` runs as its after-hook. Smaller changes between tasks (a fix, a CI repair)
append a dated paragraph to the current kickoff post rather than opening a post of their own.

## The slides post

Built before the pull request is opened, so the PR carries it and reviewers see it. It is a
reveal.js deck under `site/static/slides/<date-slug>/index.html`, embedded in a blog post:

```mdx
import Slides from "@site/src/components/Slides";

<Slides slug="2026-11-08-reporting" />
```

The deck has four parts:

- **Overview**, illustrated: what the capability, feature or fix is, one figure or diagram per idea.
- **Demonstration of progress**: charts and track plots. A track plot shows the true ownship
  track in blue, the true target track in red, and where the estimator believed the target was:
  its trail from the ownship zig, a marker and 1-σ ellipse at the named times.
- **What was not achieved**, plainly.
- **What comes next.**

For a gate the slides post is the illustrated companion of the critical write-up and links to it;
it does not retell the result. Template: `site/blog/_templates/slides.md` and
`site/static/slides/_template/index.html`. Command: `/speckit-report-slides`, which
`/speckit-implement` runs as its after-hook; a gate run makes its slides post after the panel has
decided.

## Figures

Figures are SVG, committed under `site/static/img/<date-slug>/`, each next to the `.json` sidecar
written by `tma2-plot`, which names the truth file and the prediction files with their SHA-256
digests, the scenario, the command line and the code commit. A figure can therefore be remade:

```bash
uv run tma2-plot track --truth data/demo/train.f32pack \
  --predictions lsq.ndjson imm.ndjson oracle.ndjson --labels "batch LS,IMM,oracle" \
  --scenario 8 --at 2440,2740 --out site/static/img/<post>/track-8.svg
uv run tma2-plot errors --truth data/demo/train.f32pack \
  --predictions lsq.ndjson imm.ndjson oracle.ndjson --labels "batch LS,IMM,oracle" \
  --scenario 8 --out site/static/img/<post>/errors-8.svg
```

Rules:

- Data behind a figure is seeded and regenerable. The post names the seed, count and ranges
  file of a demo split, or the committed experiment the predictions came from.
- Rows before the ownship zig are hidden: the physics layer's pre-zig states are finite but
  undetermined (range sd far above range), and plotting them misleads.
- Rows that fail the one plausibility rule (`plausible_row`) are masked.
- Figures made by a research script instead of `tma2-plot` name the script and its commit.
- Keep each figure under about 200 KB. No raster images, no hand-edited figures.

## Why

The gate write-ups read results critically, but they appear only when a gate ends, and they carry
no pictures. Between gates the only trace of direction was the PR descriptions. The kickoff post
makes the plan visible before the work, and the slides post makes the result visible to someone
who will not read a metrics table.
