---
title: "Slides: the site, published, with persistent PR previews"
date: 2026-11-16T20:00
tags: [slides, spec-022]
---

import Slides from "@site/src/components/Slides";

The site is published to GitHub Pages on every merge. A new [time-late page](/timelate) shows
the standing time-late system's tracks. Every pull request now keeps a preview, listed on
[PR previews](/previews). Spec: `specs/022-site-publishing/`.

<!-- truncate -->

<Slides slug="2026-11-16-site-publishing-slides" />

## What was built

- **`.github/workflows/pages.yml`**:
  - Merges to `main` publish the site at the root of `gh-pages`.
  - Each same-repository PR publishes its own build at `pr/<n>/`, and the copy is kept after
    the PR completes.
  - Closing a PR updates its state in `pr/index.json`.
  - A manual run builds a preview for an earlier PR.
  - Deploys run one at a time.
- **`/previews`** lists every PR with a preview: its state, a link to the preview, and links to
  the blog posts it added or changed, opened in that preview.
- **`/timelate`** draws whole-period tracks from spec 016's test record (seed 341, used):
  - the 20 first stored periods each of Annex B targets, 2% wild bearings and a shifted
    manoeuvre prior;
  - the standing control, C″, the true-history fit and the learned model;
  - true and declared manoeuvres on a timeline;
  - per-period errors, checked against the record by a unit test.

## What was not achieved

- PRs before this one have no preview until the manual backfill is run for them.
- The page's medians are over every stored row, not the scorer's rows, so they are not the
  record's figures. The page says so.
