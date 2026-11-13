# Tasks: Time-late, repair and re-registration (spec 015)

- [x] T001 Prior version 3 in `src/tma2/timelate/prior.py` (`open_precision`, renormalised `_leg_sf`/`_leg_tail`, flat prior without the unpaired m!) and the call in `retest.log_evidence`; versions 1 and 2 unchanged (both fixtures pass)
- [x] T002 Tests in `tests/unit/test_timelate3.py`: density × volume = 1 for speed, course, each change's size, each duration (turn, speed change, both) and the first start; a spec 014 fixture for `search2`
- [x] T003 `src/tma2/timelate/match.py`: `same_history` (edge-aware) and cut flags from the engagement's table; tests on constructed cases (cut at start, at end, complete on the last row, a found manoeuvre paired with a cut one)
- [x] T004 `src/tma2/timelate/run3.py`: `search3`, `search3-flat`, `search3-mix`, `search2` beside; reference held when it drifts, flagged; refit fall-back (R4); period records with cut flags and reference flags
- [x] T005 `src/tma2/timelate/study3.py` and `tlscore`: readings with the one rule; headroom at thresholds 1, 3, 5 and tolerances 60, 120, 240; with and without flagged references; D1's other estimands and the flat-prior share; D4 by period length; manoeuvring targets declared quiet by true count; denominators stated
- [x] T006 `scripts/research/tl3_tables.py`: every table of a record from `summary.json`; a test that a record's tables equal its summary
- [x] T007 Development run on spent seed 335 (`timelate/tl-d-dev`): before and after; record `experiments/<date>-tl3-dev/`
- [x] T008 Register: plan `configs/timelate/tl-d.json`, run files, decision record with forecasts and every changed definition; SRD §9 line
- [x] T009 Validation seed 336 (soundness stop), then test seed 337 once; records
- [x] T010 Panel (five reviewers), corrections
- [x] T011 Write-up, slides post and deck, figures; AGENTS.md; kickoff update; PR description
