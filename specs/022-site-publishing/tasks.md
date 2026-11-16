# Tasks: publish the site, a time-late page, persistent PR previews

- [x] T001 `SITE_BASE_URL` in `docusaurus.config.js`; build at a preview base URL locally.
- [x] T002 `scripts/site/preview_index.py` and its unit tests.
- [x] T003 `.github/workflows/pages.yml`: main deploy, PR preview, closed-state update,
  manual backfill.
- [x] T004 `site/src/pages/previews.js`, and the navbar links.
- [x] T005 `scripts/research/timelate_viewer_data.py` → `site/static/timelate-data/`,
  with a check against the record.
- [x] T006 `site/src/pages/timelate.js`.
- [ ] T007 Kickoff and slides posts, AGENTS.md, PR. Backfill previews for PRs 37 and 38 after
  merge.
