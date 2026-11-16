# Implementation Plan: publish the site, a time-late page, persistent PR previews

**Spec**: `spec.md` · **Date**: 2026-11-16 · No result, no seed, nothing trained.

## Approach

- **Deploys go to the `gh-pages` branch**, not to an Actions Pages artifact. An artifact
  replaces the whole site on every deploy, so previews would not persist. A branch keeps every
  `pr/<n>/` directory until someone deletes it.
- **`.github/workflows/pages.yml`**:
  - Triggers: `push` to `main`, `pull_request` (opened, reopened, synchronize, closed) and
    `workflow_dispatch` (pr, ref) for backfill.
  - Runs are not serialised (review): each publish re-applies its change on the latest branch
    and retries. Superseded builds of one PR are cancelled. The `closed` state update runs under
    `pull_request_target`, using the default branch's code.
  - Fork PRs are skipped.
  - Steps:
    1. Build the site with `SITE_BASE_URL`.
    2. Check out `gh-pages` into a temporary folder.
    3. Copy the build to the root (excluding `pr/`) or to `pr/<n>/`.
    4. Update `pr/index.json` with `scripts/site/preview_index.py`.
    5. Commit and push, retrying on rejection by rebasing on the branch.
- **`site/docusaurus.config.js`** reads `baseUrl` from `SITE_BASE_URL` (default `/gitma2/`).
- **The previews page** (`site/src/pages/previews.js`) fetches `/gitma2/pr/index.json` from the
  root, whichever build it is in.
- **Blog post links**: the PR's added or changed `site/blog/*.md` files, excluding
  `_templates`. A file `YYYY-MM-DD-slug.md` maps to `blog/YYYY/MM/DD/slug`, unless its front
  matter sets a `slug`. The title comes from the front matter.
- **The time-late page**: `scripts/research/timelate_viewer_data.py` writes
  `site/static/timelate-data/` from `experiments/20261114-tl4/`:
  - `tracks.npz`, for 20 stored periods per split: man2, man2-out, shift;
  - `<split>.periods.json`, for the true and declared spans.

  It writes a manifest with digests and the headline table from
  `experiments/20261115-tl-synthesis/tables.md`'s source `summary.json`s. The page is
  `site/src/pages/timelate.js`.
- **Checks**:
  - unit tests for `preview_index.py`, covering the slug mapping and the state update;
  - a check that the page data's per-period errors equal those recomputed from `tracks.npz`;
  - headless screenshots of `/timelate` and `/previews` with a fake index.

## Constitution check

No record, gate or criterion changes. The time-late page shows committed records and says
which. Publishing stays on the repository's own site.
