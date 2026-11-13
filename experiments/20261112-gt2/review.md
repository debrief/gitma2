# Gate T: panel review, round 1 (2026-11-12)

Five independent reviewers read both registrations, both validation records and the test
record, and re-computed from the raw files (the `*.periods.json` here and the per-row errors
on the results branches). **All five: approve with findings. Decided in one round.**

## Verdict on each check

| Check | Registered outcome | Panel |
| --- | --- | --- |
| T-a | pass (1.05) | Accepted, **as a weak check**: consistent in the median, and blind to the fault that stopped the first registration |
| T-b | pass (2.27 [1.76, 2.67]) | Accepted. To be named for what it is: a prior-informed whole-period smoother against a causal prior-free filter read as a track |
| T-c | pass (1.69 [1.39, 2.14]) | Accepted **with qualification**: 1.3 to 1.7 across seeds, pooled 1.6; this shift only; mismatch cost not separated from difficulty |
| T-d | pass (0.71; −0.03) | Accepted **as registered, fragile**: it passes at the 120 s match and temperature 3 only, and by cancellation across period complexity |
| T-d-shift | fail (+0.32) | Accepted. Consequence sharpened: under a wrong prior, rank only, no probabilities |
| T-e | material (1.46 [1.24, 1.91]) | Accepted as registered. **Renamed**: the cost of not knowing the history, an upper limit; the paired figure (1.17) would not clear 1.10 |

## What was checked and found sound

- Over 40 figures in the README match `summary.json`; `gate.ratio` re-run on the per-row
  errors gives identical values.
- The plan, both run configurations, `decision.json` and `src/tma2/timelate` were last
  changed at b3b2903, before validation (21ac02c) and test (34da02f), both from clean trees.
  Recomputed digests equal those in `decision.json` and in every shard.
- Every threshold is identical in the two registrations. T-e's comparator became harder.
- The bootstrap is paired over periods, one period per engagement; lower bounds are stable
  across bootstrap seeds.
- No truth reaches the search: it receives the bearings, the ownship, the stated σ, its
  starts and the prior, and the prior file is the same for both splits.
- The reference receives the true spans and kinds, the first bearing and σ, and nothing
  else. From neutral starts its cost is within 1 of the truth-started fit's in 75% of
  periods, lower in 21%, higher in 4%.
- Dropping periods with no determined rows uses a mask from the truth's bound, the same for
  every system. Only the IMM and EKF have unanswered rows.
- The bootstrap intervals are honest: the spread of the shift ratio across three seeds
  matches what the intervals imply.

## Major findings

1. **T-b is mostly smoothing, not finding the history.** Where the first candidate is the
   true history (154 of 277 periods) the search is at 0.032 against C″'s 0.081; where it is
   wrong, 0.057 against 0.093. It wins either way. The baseline that would separate the
   search from the arc model and the prior (C″'s own transitions refitted with both, no
   search) is not in the gate and cannot be computed from the committed files.
2. **The headline ratios are ratios of medians, not typical gains.** The median per-period
   ratio C″ ÷ search is 1.68 [1.49, 2.04] on Annex B and 1.53 [1.36, 1.80] on the shift
   split. The search beats C″ in 70% and 72% of periods; it is worse in about 30% and more
   than twice as bad in 12% (8% on shift). Search ÷ reference per period: 1.17 [1.01, 1.32].
3. **T-e is misnamed.** Where the search names the true history its ratio to the reference
   is 1.01; where it names the wrong one, 1.54. The room sits wholly in the wrong-history
   periods, an untested share of which are ambiguous. It is an upper limit on what better
   identification could win.
4. **T-c is one draw of a variable quantity and does not isolate mismatch.** Three seeds:
   1.70, 1.26 [0.89, 1.84] (would fail), 1.69; pooled 1.59 [1.38, 1.86]. The shift also
   makes the task harder (true manoeuvres per period 1.94 → 3.23; median duration 120 s →
   60 s), and no search with the correct shifted prior was run. Against the reference the
   search degrades from 1.46 to 1.87. The shift is moderate, inside the same model family,
   and in one direction (busier, smaller): 75% of shifted turn angles lie inside the
   prior's support.
5. **The search under-counts manoeuvres.** Annex B: fewer than true in 19% of periods, more
   in 8%; 132 of 583 true manoeuvres missed (23%), 93 false. Shift: fewer in 67%, more in
   0.3%; 401 of 969 missed (41%). With no true manoeuvre (12 periods) it invents one in 58%.
   Correctness of the first candidate falls from 0.77 with one true manoeuvre to 0.26 with
   four. On the shift split its best evidence exceeds the true history's by more than 3 in
   68% of periods: there the prior, not the search, is the limit.
6. **T-d passes by cancellation and at its registered settings only.** Stated probability is
   flat (about 0.54) across period complexity while accuracy is not (0.77 with one
   manoeuvre, 0.40 with three or more). At a 60 s match the true history is in the first
   three in 0.57 (below 0.60); at 240 s the gap is −0.10. At temperature 1 the gap is +0.26,
   at 5 −0.16. First-candidate-right was 0.61, 0.45 and 0.56 on three seeds. On the shift
   split no temperature calibrates (the best Brier score equals the base rate): ranking
   survives (AUC 0.68), probabilities do not.
7. **T-a would have passed the faulty reference.** On the tightly bounded rows it reads,
   the truth-started fit scores 0.91 [0.76, 1.05] on Annex B: inside the band. Only the
   shift split (0.52) and the middle band (0.44) expose it. T-a's own interval is 1.05
   [0.91, 1.17]. It is also partly circular (the arc model is the generator's) and blind to
   tails: 3.1% of tight rows exceed three times the bound and 1.7% five times.
8. **The record does not say what spec 013 promised and did not deliver**: the owner's
   bearing-rate thinning study (FR-030, FR-031, User Story 4); matched, missed and false
   manoeuvre counts and timing error as gate outputs (FR-011); splits by ownship manoeuvre,
   position in the period and range band (FR-013); the correlated-error variant scored
   beside (FR-003); uncut engagements as a stratum; a smoothed IMM line (FR-022: the
   forward filter is silent on 60% of rows and is a null line).
9. **A target that never manoeuvres is untested**, and is the commonest real case and the
   analyst's worst false alarm for a system whose prior expects manoeuvres.

## Minor findings

- The reference "with the prior" is outside T-a's band on its own (1.42 tight, 0.82 loose);
  T-a vouches for the times-held fit, T-e uses the other.
- Prior-using systems may sit below the bound legitimately; the by-band table should say
  the bound does not bound them. The loose band is 825 rows from 38 periods.
- The truth-started fit should not sit in the systems table as if attainable.
- Candidates are scored on all 300 periods, ratios on the 277 or 267 with determined rows.
- `prior.py`: properly normalised and paired with the Occam term; three small errors, all
  penalising extra manoeuvres (leg curvature counted twice, at most 0.35 nats a manoeuvre;
  uniform directions' volume; the leg normal not renormalised at its minimum).
- The two starts each supply the first candidate about equally (130 and 127 periods); from
  nothing alone T-b still passes (1.83 [1.45, 2.22]).
- Worst periods: Annex B none above 0.70; shift one at 17.9. C″ has 23 periods over 0.5
  against the search's 4.
- Validation and test ran on different CPU families; confounded with seed, untestable.
- `gate.py` and `tlscore.py` are outside the code digest (unchanged since b3b2903).

## What the panel wants before any learned model or GPU spend

1. The owed classical studies: thinning, correlated and outlier bearing errors, held-course
   periods with a false-manoeuvre rate, manoeuvre counts as gate outputs.
2. The standing controls: C″'s transitions refitted with the arc model and prior (no
   search), and the search with a flat prior.
3. The ambiguity share: how often the true history's evidence is within reach, so that the
   upper limit in T-e becomes an attainable figure.
4. A prior-robust search (a broadened or mixture prior; a sampler in place of Laplace) and
   a diagnostic for prior mismatch.
5. Then a learned model, registered against the search under the same prior, with the shift
   and a quiet-target split, an Annex-B-only training arm scored on the shift, and
   efficiency per slice.
