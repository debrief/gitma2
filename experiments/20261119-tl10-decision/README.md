# Spec 030 decision record: a carried prior across gaps (k4), against `ctl` alone

Registered 2026-11-19, before seeds 362 (validation) and 363 (test) exist (neither appears in any
earlier commit, run file or record). Nothing is trained; CPU only. A registered study, not a gate.
Owner 2026-11-19: register k4.

## What is bound

- Plan `configs/timelate/tl-o.json`, SHA-256
  `741665359bf8cc6fa37a850696e9814aafcd03d9099e522be28f9c18be67cf1f` (never edited after).
- Code: time-late modules digest (`tma2-tlsolve`'s `CPRIOR_FILES`, runner `run10`)
  `90a19712a3fcd95fafb589cf39f760be98562c4b2466c26316ddbb86e844c017`, unchanged since the
  refinement runs at fb5fa2a. Scorer `tma2-tlscore` (`study10`), tables
  `scripts/research/tl10_tables.py`.
- Runs: `configs/timelate/runs/tl-o-val.json` (seed 362, Annex B, 110 engagements),
  `configs/timelate/runs/tl-o-test.json` (seed 363; Annex B 70, busier 100, wild bearings 50,
  held course 50 engagements).

## Systems

`ctl` alone, the joint solve and spec 027's carried start (all unchanged); **k4**: each later
period's evidence holds a Gaussian prior on its starting state (x, y, course, speed) from the
previous period's declared last state and its Laplace covariance, run through the gap at constant
velocity with Annex B's manoeuvre noise, the covariance then multiplied by 16 (4 in sd); its search
starts from the carried state. The uninflated carried prior (`cprior`) is run and reported beside.

How k4 was chosen (development, spent seeds; `experiments/20261119-tl10-dev/`,
`experiments/20261119-tl10-refine/`): the uninflated prior was overconfident (truth inside its 95%
ellipsoid in 41 to 50% of periods) and harmed Annex B periods with their own ownship turn on seed
361 (0.51). Of five variants, the rule written beforehand selected k4 on seed 361; the declared
check on seed 360 passed.

## Rule, over periods after an engagement's first (rows as spec 025)

- **Helps**: alone ÷ k4 in range, engagement-bootstrap 95% interval wholly above 1, on Annex B
  (which decides).
- **Harms**: alone ÷ k4 wholly below 1 in range, course or speed on any split, or in range on
  Annex B's periods with their own ownship turn. Harm overrides helps.
- Otherwise **not shown**.
- Reported by the same intervals: k4 ÷ joint (joining stays the standing system whatever this
  shows; the question is what to use when the earlier bearings are not kept), the uninflated
  prior, by own turn, own rows, ties, and the coverage of k4's stated uncertainty (4 dof).

What follows: helps without harm → k4 is recommended where a period must be solved without
the earlier bearings (the carried state and its covariance are all that is kept), with the joint
solve standing where they are kept. Not shown or harms → the carried prior is not recommended
and the track stops at the joint solve.

## Soundness (validation, seed 362; stops the study if it fails)

As spec 027: the span reference with times held, per engagement (at least 10 rows with span bound
below 0.05), geometric mean within [0.6, 1.6] (a gross-fault screen; centre 0.98), joint solve
answering at least 0.95 of periods. k4 is not scored on validation beyond being reported.

## Forecasts (from the development seeds; restatements of two spent seeds, not predictions)

Annex B alone ÷ k4 about 1.2 to 1.6 (seed 361: 1.22 [0.94, 1.57]; seed 360: 1.59 [1.27, 2.01]):
"helps" is likely but not certain at 70 engagements; one of the two development seeds would not
have passed. Busier about 1.55; held course larger (alone is poor there); wild bearings unknown.
k4 ÷ joint about 2.1 on Annex B, 1.15 to 1.2 on busier. No harm expected; coverage 0.92 to 0.97.

## Known before registration

- k4 is the coarse end of a two-point grid and over-cautious (median d² 0.4 to 0.9 against 3.36).
- Seed 361 both chose and was spec 027's test seed; the check on 360 is one seed.
- The variant was chosen on Annex B and busier splits only; wild bearings and held course are
  first seen at test.

## Renumbered, and a seed claimed twice (2026-11-20)

This study was developed, registered and run as spec 028. Another session's spec 028 (the previous
window as a prior, long engagements) and spec 029 (held course) merged to main first, so this one is
spec 030 (`specs/030-carried-prior/`). The bound plan `configs/timelate/tl-o.json`, the earlier plans
and the code (`cprior.py`, `run10.py`, `study10.py`) keep the words "spec 028": they are bound by
digest and are not edited.

Seeds: spec 029 registered seeds 362 to 364 at 15:42 UTC on 2026-11-19 on another branch, before
this registration (18:33 UTC), which could not see it. It used them in the long-engagement simulator
(`src/tma2/long/sim.py`), this study in the time-late layout simulator (`timelate/layout.py` on
generator 0.6.0 periods), so the streams and engagements differ, but the numbers were used twice
(as specs 025 and 026 did with 349 to 351). Neither study saw the other's data. The next fresh
seed is 365.
