# Research: time-late over several periods of one target

Spec: `specs/025-joined-periods/spec.md`. Development data only; nothing here is a result. The spike (R1) ran
on seed 348 with the time-late generator before it was known that spec 023 (long
engagements, another simulator) had used that seed; it is development work and nothing is
decided on it. The study's seeds are 349 tuning, 350 validation, 351 test.

## R1. The joint solve needs no new search: `ctl` on the span, gap bearings marked missing

`ctl`'s problem is `(t, ox, oy, z, v, σ)` with `v` the bearing mask (dropouts already exist
in the generator). A span from the first period's start to the last period's end, with `v`
false in the gaps, is a problem `ctl` solves unchanged: the arc model runs through the gap,
the score test proposes candidate manoeuvre times there as anywhere (a manoeuvre in a gap
changes every later bearing), and the evidence and declaration are as registered.

So the joint solve is `run4`'s `ctl-d1-q0.01` on the masked span, and FR-001 holds by
construction: no line of `ctl` changes. FR-013's check (one period, no gap, reproduces
`ctl` alone) is then an identity on the runner's plumbing, tested as such.

Spike (`scratchpad`, 9 engagements of seed 348, two periods of 15 to 30 min, one gap of 5 to
30 min; development): it runs; 90 to 1,600 s an engagement for both systems. Alone ÷ joint
on the span-bound rows: 4.7, 7.1 / 4.2, 2.3 / 4.2, 0.95 / 4.9, 0.60 / 1.1, 0.27 / 4.9, 6.1 /
0.96, 0.80 / 3.2, 1.1 (first period / second). Large gains where a period is undetermined
alone (its own bound median 1.4 to 7.5, the span's 0.02 to 0.19); losses where the period
holds the ownship turn and the target manoeuvred in the gap (engagement 6: three true
manoeuvres, two declared).

Alternatives considered: a gap manoeuvre with its time integrated out analytically (exact
volume over the gap); a search seeded from the periods' own histories. Both are kept as
tuning options only if the Laplace evidence misbehaves for manoeuvres inside gaps (R4).

## R2. Scoring rows

Spec 016 scored a period at rows whose own known-history bound is below 0.5. For a period
with no ownship turn that is no row at all, so the main effect would be invisible. Rows are
chosen by the bound from the *span's* bearings (the information the joint solve holds,
gaps without bearings), the same rows for both systems. The ratio on rows the period
determines alone is reported beside (FR-008). The bound is the known-history bound
(`bound.period_bound`) computed on the masked span.

## R3. Layout

Per engagement, from a stream of its own (`mix64(seed ^ LAYOUT_STREAM)`, as `periods.cut`
does): the number of periods K in {2, 3} with equal odds; period lengths uniform 15 to 30
min; gaps uniform 5 to 30 min; if the layout does not fit the window, K is reduced; the
span's start uniform over what fits. Engagements whose window holds no two-period layout
are skipped (counted). Windows 60 to 120 min (`configs/timelate/tl-joined-ranges.json`:
`tl-ranges.json` with `window_s.min` 3600; the shifted and held-course splits likewise).
The generator's draws are untouched (the layout reads nothing it writes).

## R4. Risks to check on tuning

- Laplace evidence for a manoeuvre whose time sits inside a gap: the time is set by the
  prior alone; check its evidence against the same manoeuvre at a period's edge, on noise
  alone (no manoeuvre) and with one manoeuvre in the gap (AGENTS gotcha: run an adaptive
  rule on noise first).
- Held course over the span: false manoeuvres declared in gaps, where no bearing can
  contradict them except through the later period.
- Cost: about 15 minutes an engagement; `timelate.yml` shards of 4 engagements.

## R5. Interval

Periods of one engagement share a target and a joint solve: the bootstrap resamples
engagements (all their periods together). Geometric mean of per-period ratios; the median
per-period ratio and shares better, twice as good and twice as bad beside.

## R6. Splits

`man2` (Annex B, decided), `shift` (shifted prior, decided), `man2-out` (2% wild bearings,
decided: `ctl` edits them), `quiet` (held course: false manoeuvres; ratio reported). Same
seed per split, as spec 016. Sizes from tuning variances in the decision record.
