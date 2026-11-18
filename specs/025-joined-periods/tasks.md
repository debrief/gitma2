# Tasks: time-late over several periods of one target

Spec `spec.md`, plan `plan.md`, research `research.md`. [P] can run in parallel.

## Phase 1: build

- [x] T001 `src/tma2/timelate/layout.py`: `layout(seed, samples, dt)` → periods and gaps
      (R3); `span_period(engagement, layout, masked)` → a `Period` over the span with the
      gaps' bearings marked missing (or not); `period_rows(layout)`.
- [x] T002 `src/tma2/timelate/run8.py`: per engagement, `run_shard4` on each period alone,
      on the masked span (joint) and on the full span; per period: errors of `ctl-d1-q0.01`
      alone and joint (and `ctl` full, C″, one leg, `history-best` span and alone) on its
      rows; the span bound and the period's own bound; gap events (true manoeuvres in each
      gap, declared ones); histories; timings. Fall-back counted when the joint fit fails.
- [x] T003 `src/tma2/timelate/study8.py`: paired per-period ratios (range, course, speed)
      with engagement bootstrap; medians and shares; rows "own turn" / "no own turn", gap
      length bands, gap manoeuvre yes/no, span-bound tightness, own-bound rows; held-course
      false manoeuvres by place (period, gap); verdicts by the registered rule.
- [x] T004 CLI: `tlsolve` runner `run8` (JOIN_FILES digest) and `tlscore` runner `run8`.
- [x] T005 [P] `configs/timelate/tl-joined-ranges.json` and shifted / held-course variants
      (window ≥ 3600 s); generate locally first (AGENTS: manoeuvre-table limit).
- [x] T006 [P] `tests/unit/test_timelate8.py`: layout independent of the generator's draws
      and reproducible; masked span hides exactly the gaps; a one-period layout's joint
      equals alone; bootstrap resamples engagements; study on a synthetic summary.
- [x] T007 Smoke run of two engagements locally; emulate the workflow's command builder.

## Phase 2: tuning (seed 349)

- [x] T008 `configs/timelate/tl-j-draft.json`, `runs/tl-j-tune.json`; CI run; record in
      `experiments/20261117-tl8-tuning/` with tables.
- [x] T009 R4 checks: noise alone over a span; one manoeuvre in a gap; held course.

## Phase 3: registration and validation

- [x] T010 Decision record `experiments/<date>-tl8-decision/` (rule, sizes, forecasts,
      what follows; plan `tl-j.json` bound by digest; code digest).
- [x] T011 Validation seed 350: soundness (FR-012); record.

## Phase 4: test and report

- [x] T012 Test seed 351, scored once; record and tables by script.
- [x] T013 Panel of five (`review.md`); corrections.
- [x] T014 Write-up, slides post and deck, figures by script; AGENTS.md; SRD §9 line; PR.

Status 2026-11-18: done. The first registration stopped at validation (seed 350); re-registered
(owner, option A) and decided on seed 353 by the panel (`experiments/20261118-tl8/review.md`).
Not delivered: spec 024's carried state beside (not merged), IMM/EKF tracks, a unit test of
`run_shard8`'s slicing.
