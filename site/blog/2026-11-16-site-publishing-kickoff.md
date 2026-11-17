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

## Updates

- 2026-11-16, after the owner's review of the preview:
  - The time-late page shows each system's solution whole, as one fit to all the period's
    bearings. The time slider is gone; start and end markers and 10-minute ticks remain.
  - The viewer says it is the real-time model and points to the time-late page.
- 2026-11-17, issue 44: each PR now carries a comment linking its preview at `pr/<n>/`, the
  blog posts it adds or changes and the commit it was built from. One comment per PR, found by a
  hidden marker and edited in place on every push, as the argonautical repository does it. A
  backfill run publishes without commenting.
- 2026-11-17, issue 41 (the owner's request):
  - Both track plots zoom with the mouse wheel about the cursor. A drag pans, a double click
    resets, and buttons do the same for touch and keyboard users. Markers and line widths keep
    their size; the scale bar follows the zoom.
  - The viewer can show the measured bearings received so far, one a minute with the latest in
    bold. They come from the engagement's scenario file, checked against the manifest's digest.
    The time-late data carry no bearings, so that page has zoom only.
  - Both plots now use one scale on both axes. Before, north–south was drawn at 0.79 (viewer)
    and 0.73 (time-late) of east–west, which bent courses and squashed the 1-σ ellipse.
