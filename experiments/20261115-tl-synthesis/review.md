# Spec 019: review of the account of the time-late track (2026-11-15)

Three independent reviewers (every number; claims against the panels; conclusions and the
diagnostic) checked the write-up `site/blog/2026-11-15-time-late-synthesis.md`, its deck,
`tables.md` here and the diagnostic record `experiments/20261115-tl7-dev/` against the
committed records and panel reviews of specs 013 to 018. **All three: approve with
findings.** The corrections below were applied before the account was put forward; the
first draft is in the branch history (commit 8728dc4).

## Found sound

- `tables.md` regenerates byte for byte; every figure of the account's tables and of the
  diagnostic section matches its source; the deck carries no number the post does not.
- The diagnostic's eleven ratios, intervals and medians recompute from the per-row errors
  to ±0.01.

## Corrections applied

1. **The diagnostic's "tail" was an artefact (major).** Dropping only a system's ten best
   periods reads any widely spread ratio as a tail: a true ratio of 1 with this spread
   reads 0.85. Trimmed at both ends the true prior is 1.14; it wins in 55% of periods, is
   over twice as good in 25% and over twice as bad in 13%. The same statistic was behind
   spec 018's "ten periods carry 87%"; a note is added to that record.
2. **"Worth having only whole" contradicted the ladder (major).** Legs, turn sizes and turn
   rates reach the whole prior's figure in range; legs are the largest step; "each part
   alone" left the legs out. Reworded as a direction, not a decomposition.
3. **"What remains" quoted the undeclared control against the free reference as if it were
   the standing control (major).** Both conventions are now given: 1.3 / 1.2 / 1.8 to 2.1
   and, for the declared control against times held, 1.6 / 1.5 / 2.3 to 2.7.
4. **"The remainder is mostly not closable" over-reached (major).** The spec 017 panel
   named that wording as over-reach. Now: the share depends on the line (0.65, 0.44, 0.14
   attainable at 10, 20, 40) and the single-omission measure overstates what is hidden.
5. **The control's costs were missing (major).** A list of its known faults is added under
   "What is standing".
6. Minor, all applied: the clean Annex B comparison is separated on one seed (1.09 [1.02,
   1.18]); the gate's own C″ ÷ search figures (1.68, 1.53) stand beside the later ones;
   replication over three seeds holds for outliers and correlated errors only; the
   evidence was wrong five times, not four, and the edge rule is a classing fault; the
   spec 014 forecast was 0.75 (0.79 was the tuning value) and 0.33 belongs to spec 015
   against a forecast of 0.50; periods run from 20 minutes, not 40, and whole engagements
   were scored in three studies; bias was tested and is unremedied, not untested; "one
   period cannot choose its prior" is scoped to this evidence and these 30 priors; "the
   answer is no" becomes the spec 016 panel's "not shown, at a small budget, with a direct
   model"; "every large gain came from stating a classical piece of knowledge exactly"
   becomes "the motion model and bad-bearing handling; the statistics added about a
   fifth"; items added to "never tested" (the owner's thinning idea, a prior-mismatch
   diagnostic, a larger budget, a family with Annex B's prior); a paragraph on what was
   shown beyond range.

## Not done

- The reviewers did not regenerate the diagnostic's `supplement.md` (its inputs are on
  results branches) beyond the recomputation above.
- The account still reports range first; course and speed appear where they differ.
