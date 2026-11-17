# Tasks: Longer engagements (6 to 48 hours)

**Spec**: `spec.md` · **Plan**: `plan.md` · **Issue**: #42

- [x] T001 Simulator `src/tma2/long/sim.py`, settings `configs/long/long.json` (seed 348)
- [x] T002 Windows, thinning and the veto at every turn `src/tma2/long/windows.py`
- [x] T003 Unit tests `tests/unit/test_long.py` (determinism, kinematics, windows, chain)
- [x] T004 Real-time runner `src/tma2/long/realtime.py` (E, C″, one leg, IMM)
- [x] T005 Time-late runner `src/tma2/long/timelate.py` (chain, stitch, scaling)
- [x] T006 CLI `tma2-long`; workflow `.github/workflows/long.yml`; run `configs/long/run.json`
- [x] T007 Local pilots: three real-time estimates and one time-late window on the 6-hour engagement
- [x] T008 Kickoff post `site/blog/2026-11-17-long-engagements-kickoff.md`
- [x] T009 Report `scripts/research/long_report.py`; page data `scripts/research/long_viewer_data.py`
- [x] T010 Component `site/src/components/LongEngagements.js` on `/viewer` and `/timelate`
- [x] T011 CI run; record `experiments/20261117-long/` (raw outputs, `summary.json`, `tables.md`)
- [x] T012 Page data `site/static/long-data/` from the record
- [x] T013 Cost of the whole-engagement bound (`timelate.bound.period_bound`) on 2 to 48 hours
- [x] T014 Research note `docs/research/12-long-engagements.md`
- [x] T015 Figures `scripts/research/long_charts.py` → `site/static/img/2026-11-17-long-engagements-slides/`
- [x] T016 Slides post and deck; AGENTS.md entry; PR description
