# Research notes: spec 019

**R1. The ladder's parts.** The broadened and the shifted targets' priors differ in exactly
five groups of fields: legs (mean, spread, minimum), turn sizes, turn rates, speed changes
(size and rate) and the weights of the kinds of manoeuvre. A unit test asserts that taking
all five gives the true prior. Order: legs first (what spec 018 varied), then turn sizes
(also varied), then the three it never varied.

**R2. Why both a ladder and single parts.** A cumulative ladder shows where the gain
appears in one order; if parts interact, the order decides which rung "carries" it. Each
part alone on the broadened prior shows its effect without the others. Four extra searches.

**R3. Search against refit.** Spec 018's test stored, for the same 150 periods, the
declared track of member `L900-s0.35-a60` refitting shared candidates. Here that member
gets its own search. The two runs are on different CPU families, so the comparison is each
against its own run's standing control, not track against track.

**R4. Size and what it can show.** 150 periods, about 133 scored: the half-width of a
paired ratio is about 0.13 (spec 018's tuning run at 132 periods). Only a part worth about
15% or more is separated. The true prior's own gain on this seed's 355 periods was 1.10
[0.99, 1.21], so the likeliest outcome is that nothing is separated and the reading is of
direction and concentration. That is stated in advance; it is still the cheapest way to
remove the confound from the account.

**R5. Used data.** Seed 347's shifted periods were scored in spec 018. Nothing here is a
registered result; no decision rule; no forecast is needed for a diagnostic, but one is
recorded in the kickoff's risks (parts may interact; little may be separated).

**R6. The account's sources.** Test records and panel reviews: `experiments/20261112-gt2/`
(spec 013), `20261112-tl2/` (014), `20261113-tl3/` (015), `20261114-tl4/` (016),
`20261114-tl5/` (017), `20261115-tl6/` (018). Each figure is read from the record's
`summary.json` by script where the record has one, and from `review.md` where the panel's
recomputation is the figure of record (marked as such).
