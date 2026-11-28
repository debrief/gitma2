# Spec 037 (proposed) — Steady-leg headroom: where the gap to told-truth lies

28 November 2026 · work order for Claude Code, for owner review before it is run.

## Summary

Four measurement experiments in this repository, run in order, that decide what a better
steady-leg detector has to deliver. They build no new detector. Each has its comparison and
decision rule written here beforehand.

They exist because a stand-alone investigation (brief section 11; the theory note and its nine
scripts) produced five hypotheses that cannot be trusted until repeated against generator
0.6.0, segmenter C″ and the physics layer:

| # | Hypothesis from the stand-alone work | Experiment |
|---|---|---|
| H1 | Most of C″'s missed changes are undetectable, not missed | E1 |
| H2 | A 25 σ² threshold is conservative on white noise and far too low under mismatch; a short window removes the bias-wander part | E2 |
| H3 | The estimate is very sensitive to knot timing and transition length, even with the structure right | E3 |
| H4 | Bounds on target speed and initial range improve the told-truth solve substantially | E3 |
| H5 | Undetectable manoeuvres can be left out of the solve at little or no cost | E3 |

## Inputs to bring into the repository

- `docs/research/14-steady-leg-detector-brief.md`: the updated brief (replaces the current one).
- `docs/research/15-steady-leg-theory-note.md`: the theory note.
- `experiments/20261128-standalone/`: the nine stand-alone scripts, unmodified, as a record.
  They are not to be imported by repository code; port what is needed.

## Rules

- **Read first.** Before writing code, read `src/tma2/physics/layer.py`,
  `src/tma2/timelate/arc.py`, `src/tma2/segment/`, `tma2-hpredict` and
  `experiments/20261128-gd/`. If anything below assumes an interface that does not exist,
  stop and report; do not work around it.
- **C is frozen.** Nothing in `src/tma2/segment/` changes.
- **Seeds.** Develop on seed 321 (spent). E1 to E3 are then re-run once on one fresh seed and
  only that run is quoted. Record the seed and commit in each experiment README.
- **Same rows for every system**, clean and primary mismatch both, 500 engagements minimum.
- **Paired statistics**: per-engagement ratios with medians, a bootstrap interval, and the
  shares twice as good and twice as bad.
- **Truth isolation.** Any function that plays the part of an algorithm receives only time,
  bearings, validity flag, stated sd and ownship's track. Add a test that calls it with the
  truth columns removed and asserts identical output. Oracle references (told-truth and its
  variants) are labelled "oracle" in every table.
- **Prior knowledge is declared.** Any use of the simulator's ranges (speed, range, leg
  length) is listed in the README, and every system in the comparison gets the same.

## E0 — Two facts about the existing solve (no experiment)

Answer from the code and record in the README:

1. Does the told-truth solve bound target speed and initial range? To what limits?
2. Does it exclude transition bearings, model the turn as an arc, or both? Where does the
   transition length come from when C″ supplies the knots?

## E1 — Omission cost against C″'s outcome (H1)

- For every true target change: the drop in the physics solve's cost when that change is
  removed from the true structure, other changes held at their true times. Compute it on
  noise-free bearings (expected cost) and on the realised noisy bearings; using all data, and
  using data up to the next change.
- Cross-tabulate against C″'s outcome for that change: found within two minutes, found late,
  missed; with C″'s declaration delay.
- Stratify by kind (course, speed, both), range, and whether ownship zigs during the following
  leg.
- **Comparison written beforehand:** share of C″'s misses with omission cost under 25 σ²
  (clean) and under the E2 threshold (primary).
- **Decision rule:** if over two thirds of C″'s misses are below the threshold, "fewer misses"
  (brief 7.3, priority 1) is closed as having no headroom, and missed-change counts are
  reported on detectable changes only from then on. If under one third, H1 is rejected and
  missed detectable changes become the first target.

## E2 — Null distribution of the split statistic (H2)

- Port the linearised scan (brief 5.6) to `src/tma2/detect/`. Linearise at the fitted
  solution, not the truth.
- On held-course engagements only, record the scan maximum for: each condition in
  `configs/gateh/conditions.json` separately and the primary condition; window lengths of
  whole, 40, 20 and 12 minutes; with and without the wild-bearing editing rule; with bearings
  dropped during ownship's turns and for two minutes after.
- Report the 95th and 99th percentiles and the false-split rate at 25 σ².
- **Comparison written beforehand:** the stand-alone figures (95th percentile 10.6 white, 58
  correlated only, 171 primary, whole window; bias inflation ×4.8 whole, ×1.2 at 20 minutes).
- **Decision rule:** a threshold table by condition and window is published. If no window of
  12 minutes or more gives under 10% false splits under the primary condition at a threshold
  that keeps half of the E1 changes detectable, "a stated false-alarm rate under mismatch"
  (priority 2) is recorded as not achievable by a goodness-of-fit test alone.

## E3 — What the solve needs from a segmentation (H3, H4, H5)

All variants are oracles: the true structure, altered. Score through `tma2-hpredict` at the
standard scored moments, range and course and speed, beside one leg, C″ and told-truth.

| Variant | Alteration |
|---|---|
| T0 | Told-truth as it stands |
| T-shift | Every transition moved by −120, −60, +60, +120, +240 s |
| T-len | True midpoints; transition length fixed at 1, 2 and 4 minutes |
| T-jitter | Each midpoint moved by an independent draw, sd 30 s and 60 s |
| T-det | Only changes above the E1 threshold (25 σ² clean; E2's value under primary) |
| T-bounds | T0 with speed and initial range bounded to the simulator's limits (skip if E0 shows it already is) |
| T-det-bounds | Both |

- **Comparison written beforehand:** paired ratio of each variant to T0. Stand-alone figures:
  +120 s gave 3.5; fixed two-minute length about 1.04; bounds 0.66 clean and 0.55 primary;
  detectable-only 1.0 clean and 0.8 primary.
- **Decision rules:**
  - If T-shift at ±60 s is over 1.3 times T0, timing to better than a minute is the main
    requirement and the next spec is about transition start and end, not detection.
  - If T-bounds is under 0.85 times T0, the bounds go into every system, and the numbers to
    beat in brief section 8 are re-stated with them.
  - If T-det is within 1.1 times T0 on clean data, T-det replaces told-truth as the reference
    ceiling in "gap recovered".

## E4 — Joined-leg splitter at scale (brief 5.5), only after E1 to E3

- Port the joined-leg arctan splitter from `site/static/demo-data/js/splitters.js` to Python
  and score it as a whole-window segmenter through the same harness, with the E2 threshold.
- Report all measures in brief section 8, with missed changes split into detectable and not.
- This is a baseline measurement, not a candidate; no tuning beyond the threshold.

## Deliverables

- `experiments/<date>-headroom-e1/`, `-e2/`, `-e3/`, `-e4/`, each with a README: question,
  comparison written beforehand, result, decision reached, seed and commit.
- The ported scan in `src/tma2/detect/` with unit tests, including the truth-isolation test.
- Brief section 11 updated: each stand-alone row marked confirmed, revised or rejected.
- A one-page summary for the owner: which of H1 to H5 held, and the recommended next spec.

## Out of scope

- Any new detector, learned or classical. Any change to C. Real data.
- Causal re-placement of knots, a structure prior, or "unknown" labelling. They wait for the
  result of E3.

## Risks

- **The stand-alone solve is cruder than the physics layer** (told-truth 0.166 against 0.065
  on clean bearings). H3 in particular may be a property of that solve; E3 is designed to
  find out, and a null result there is useful.
- **Omission cost depends on the solve's cost function.** If the physics layer's cost is
  robust or weighted, thresholds in σ² units need restating; record the conversion.
- **Compute.** E1 needs one extra solve per true change per data cut-off. If that exceeds the
  runner budget, sample 200 engagements and say so.

## Open owner decisions

- [ ] Spec number and whether E4 belongs here or in its own spec.
- [ ] Which fresh seed is spent on the quoted run.
- [ ] Whether the decision-rule thresholds above (two thirds, 1.3, 0.85, 1.1) are acceptable
      as written.
