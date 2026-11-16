---
title: "Kickoff: publish the site, a time-late page, persistent PR previews"
date: 2026-11-16T19:00
tags: [kickoff, spec-022]
---

The site has been built in CI but never published. This task publishes it to GitHub Pages on
every merge. It adds a time-late page that shows the standing system's whole-period tracks, and
gives every pull request a persistent preview, listed in an index. Spec:
`specs/022-site-publishing/`.

<!-- truncate -->

## Where we are

- [Specs 020 and 021](/blog/2026/11/16/browser-segmenter-slides) put the carried model in the
  browser. The [time-late account](/blog/2026/11/15/time-late-synthesis) closed the time-late
  track with a classical control standing.
- None of this is online. `gh-pages` holds only the first commit's README.

## Where this task moves to

- **Acceptance:**
  - after a merge, the root, the blog, `/viewer`, `/timelate` and `/previews` return 200;
  - a PR's preview and its post links work while it is open and after it is merged;
  - the time-late page's errors equal the record's, recomputed.
- **Plan:**
  - a `pages.yml` workflow deploys to `gh-pages`: the root on `main`, and `pr/<n>/` for each
    same-repository PR;
  - an index file and a `/previews` page;
  - the time-late page, from spec 016's test record;
  - a manual backfill for earlier PRs.
- **Risks:** the branch grows by a site per PR, though git stores identical files once. Pages
  must serve the `gh-pages` branch. It does today, since it serves the README.

## How progress will be shown

The PR for this task is the first with a preview. Its slides post links the published pages.
