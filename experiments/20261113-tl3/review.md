# Spec 015: panel review, round 1 (2026-11-13)

Five independent reviewers (numbers and provenance; the evidence repair; statistics and the
rule; code; scope and delivery) read the spec, the decision record, the development,
validation and test records and the code at the registered commit 30cc410, and recomputed
from the per-row errors and per-period records. **All five: approve with findings. Decided in
one round.** The registered figures stand as registered. No bug changes a decided number.
The record's reading of D3 and D5 leaned one way and is corrected below, and the repair of
the reference turns out to be the convention the headroom figure depends on most.

Figures in this file that are not in `tables.md` are the reviewers' own recomputations from
the per-row errors (results branch `results/timelate-tl-d-test-43404500552`) and the period
records; they are not registered results.

## Verdict on each decided quantity

| | As registered | Panel |
| --- | --- | --- |
| D1 | 0.33 [0.20, 0.45] | Reproduced. **"Between a third and a half", not "a third, excluding a half"**: without the refit's 10 worst periods 0.41 [0.29, 0.52]; pooled over three seeds 0.42 [0.32, 0.51]. It mostly restates how often C″ has the history right (26% of periods, where the refit obtains all of the search's gain; 0.25 elsewhere) |
| D2 | First right 0.64; wrong 0.44 / 0.13 / 0.43 | Reproduced, and stable to removing cut periods (the edge repair works). **The split between ambiguous and evidence failure is the threshold's**: 0.11 / 0.22 / 0.66 at threshold 1, 0.66 / 0.11 / 0.23 at 5. Only "search failure is the smallest class at thresholds 3 and 5" is robust |
| D3 | 1.06 inconclusive; 1.17 [1.10, 1.25] inconclusive | Reproduced. **Convention-bound and concentrated**: 1.11 to 1.19 by how the reference is fitted, 1.08 to 1.30 across the registered sensitivities; ten periods carry 54% of it; a third of it comes from references told the true times. An oracle figure, neither an upper nor a lower limit |
| D4 | 0.53 / 0.02 / 0.01 / 0.00 | Reproduced. The remaining rate is the prior's leg term (integrated numerically on 34 periods). **But 0.09 on short periods is not what a correct evidence gives**: integrated over where the manoeuvre might be, Annex B's prior favours "some manoeuvre" almost everywhere. The figure belongs to how finely a history is defined |
| D5 | By the rule: no GPU budget | **The registered outcome is "no GPU budget".** An override is a departure from the rule, not a reading of it, and the Annex B evidence for one is no stronger than the rule suggests. The argument for further work is in the splits where the simulator's assumptions fail, and there the classical controls do not exist yet |

## What was checked and found sound

- D1 to D4, their sensitivities, the paired ratios, the by-length rates, the counts of cut
  periods, fall-backs and runaways all recompute from the per-row errors and period records
  with independent code and a different bootstrap seed.
- `tl3_tables.py` reproduces `tables.md` byte for byte for the development, validation and
  test records. The committed `summary.json` and period records are byte-identical to the
  results branch.
- Every digest in `decision.json` equals the file at 30cc410 and at HEAD; `git diff 30cc410
  HEAD -- src configs .github schema scripts tests` shows only the figure script added
  afterwards. Both summaries carry the registered code digest, plan digest, commit and a
  clean tree.
- Order of events: decision record 08:30:55; one validation run, created 08:31 and finished
  09:40; one test run, created 09:49, attempt 1. No other workflow touched seeds 336 or 337.
- Between the development commit and the registered one, the only source change is the
  refit's fall-back rule (12 lines), as the decision record says; the development run used
  the earlier rule.
- Spec 014's modules (`run2`, `study`, `gate`, `controls`, `search`) are unchanged, and prior
  versions 1 and 2 are arithmetically what they were.
- Only the reference receives the true structure. `cut_flags` agrees with the list the
  runner builds. `same_history` and `counts.match` agree on every system and period of every
  split at 120 s. An overlap-based edge rule gives the same answer in all 72 cut periods.
- `log_evidence` recomputed for stored candidates on regenerated seed 337 data agrees with
  the record to 1e-3; the recorded evidence of all 53 held references reproduces.
- Inside its support every open factor of prior version 3 has density × volume = 1:
  position, course, speed, each change's size, duration for all three kinds, the first
  start, interior starts above the leg minimum, the flat prior and the mixture.

## Major findings

1. **The headroom depends on how the reference is fitted, and the repair of the reference
   raised it** (statistics, scope, code). 73 of 364 periods are replaced in the composite.
   19 of them use a reference held to the true times, and those carry 34% of its log gain.
   A fit told the true times has more than identification: where the search already has the
   right history and the reference was held, the held fit is still 2.0 times better (22
   periods over three seeds; 1.07 where it was not held). On the same test periods:

   | Reference used on replaced periods | Headroom | By the rule |
   | --- | --- | --- |
   | Registered (held where it drifts) | 1.17 [1.10, 1.25] | inconclusive |
   | Free-time fit throughout (near spec 014's convention) | 1.15 [1.08, 1.22] | inconclusive |
   | Without held periods | 1.13 [1.06, 1.20] | inconclusive |
   | Held periods counted as no gain | 1.11 [1.05, 1.17] | inconclusive |
   | Times held everywhere | 1.19 [1.11, 1.28] | material |

   The code review adds that the reference is held more often than it needs to be: the
   runner keeps the higher-evidence of two fits and tests only that one for drift, and in 20
   of the 53 held periods the other fit had not drifted. Preferring it would hold 8%, not
   13%. This follows research R3 as registered; it is a design weakness, not a deviation.

2. **The composite is carried by a dozen periods and is neither an upper nor a lower limit**
   (statistics). 291 of 364 periods are unchanged. Ten carry 54% of the gain; without the
   top five the headroom is 1.12, without the top ten 1.08. Several of them are search
   runaways (period median range error 0.8 to 1.4) that a classical guard might remove; without
   the 36 periods where the search's error exceeds 0.2 the headroom is 1.11. Against that,
   the true-history fit is worse than the search in 24 of the 73 replaced periods, and the
   reference is noisy where nothing is replaced. "17% to win" is a mean log ratio: zero in
   80% of periods, a factor of 2 to 60 in about 10%, a loss in 7%.

3. **The record's D5 paragraph was slanted** (statistics, scope). It was right to give the
   rule's output first and the evidence separately (FR-013). It was wrong in three ways.
   "Between 10% and 30%, most likely about 17%" took its top from threshold 1, where the
   evidence difference exceeds the threshold in 36% of periods whose history the search has
   right, and left out the low end (1.08 at threshold 5 and 240 s; 1.11 with held periods as
   no gain). It quoted validation (material) and not development (inconclusive); five of the
   nine registered cells are inconclusive on test. And "the decision is a judgement, and it
   is the owner's" goes further than a rule allows that was written so that inconclusive
   counts as not material; a lower limit of 1.101 would not have drawn that paragraph. The
   verdict does flip with the interval method (BCa lower limit 1.101 to 1.103; one-sided 95%
   limit 1.105 to 1.107), which shows the rule had little power at this sample size: on the
   three seeds' pooled distribution, 364 periods return "material" about two times in three.
   A rule forecast as a coin's toss should not have been registered as a decision
   instrument. Fair wording: an oracle identifier is 8% to 30% ahead by convention, 11% to
   19% at the registered threshold by reference convention; what a real identifier would
   obtain is less and unmeasured.

4. **The low false-manoeuvre rate on short periods is not a property of a correct
   evidence** (evidence review). Integrating numerically over the invented manoeuvre's size,
   rate, sign and start on 34 held-course periods: the Laplace value is within about 1 nat
   of the integral at the same mode (median +0.6, at most +2.5), so approximation error is
   not inflating the 0.53, and with the leg statistics removed a manoeuvre is favoured in 3
   of 28 declared periods, so the leg term explains the rate, as the record said. But
   integrated over every start and both kinds, the evidence favours "some manoeuvre" in 27
   of 28 declared periods and in all 6 undeclared ones: Annex B's prior odds are about 6 to
   1 at 25 minutes and the bearings are silent (the posterior sd of the invented start is
   250 to 1,050 s). The 0.09 under 30 minutes exists because one mode is compared with the
   no-manoeuvre history. The repair removed an error; what remains is the question a
   history-by-history evidence cannot answer on a quiet target under this prior.

5. **Version 3's pairing fails at the edges of the prior's support, where the invented
   manoeuvres sit** (evidence review). 179 of the 212 declared held-course periods have a
   manoeuvre parameter at or outside a support edge or at the solver's 10 s floor (turns
   under the 30° minimum in 79 of 137; acceleration at its maximum in 68 of 111). At an
   edge, density × volume for a turn is 0.80 just inside and 0.08 just outside (2.3 nats;
   3.0 at the rate's edge): the one-sided shoulder switches on a curvature the stand-in does
   not know about. At the floor, the prior mass of a duration inside the solver's box is
   0.37 for a 5° turn and 0.03 for 1.7°, where Laplace assumes 1: 1.0 to 3.5 nats of
   over-credit against research R1's "about +0.7". It did not move D4 in the sample (margins
   on long periods are large). The tests integrate at interior points only and cannot see
   it. This is the fifth error of this family; the evidence repair is not finished.

6. **D2's "evidence failure" is inflated by a reference a few nats short, and a held fit's
   evidence is not a Laplace evidence** (statistics, code). Where the search's history is
   the truth, the evidence difference exceeds 3 in 22% of periods and one-sidedly (44 below
   −3 against 7 above): the true-history fit is often an under-optimised fit of the same
   history. Among wrong periods, 26 of the 56 evidence failures have a difference between −5
   and −3. A held fit's evidence is evaluated at a point that is not a mode in the times
   (held minus best free fit: median −1.2 nats, quartiles −2.5 to −0.5); re-running the 53
   held periods changes the class of 14 of 42 wrong ones. Net effect on the registered split
   about ±0.03; held wrong periods are search failures in 1 of 42 against 16 of 97 others.
   The record's reading 6 ("prefers a wrong history about as often as it cannot separate
   them") is not supported at this noise level.

7. **The before-and-after the spec promised is only partly delivered** (scope). SC-004 and
   FR-007 asked for each repair's effect on each decided quantity on the same periods. The
   record gave D4 and the first candidate only, and did not separate the repairs. The
   panel's recomputation on the test periods, first candidate right: spec 014's evidence
   with the old rule 0.50, with the edge-aware rule 0.59; repaired evidence 0.53 and 0.64.
   The edge rule is worth about +0.10 and the evidence repair +0.04 to +0.05; the record's
   0.598 to 0.652 showed only the smaller. D1 with spec 014's search as the whole is 0.36
   [0.22, 0.50] against 0.33, so the fall from spec 014's 0.43 is the seed, not the repair.
   D3 with a free-time reference is 1.15 against 1.17. Development used 200 periods of seed
   335 only, not seeds 333 to 335. FR-009 is not met for D2 (finding in the table above).

8. **The refit's fall-back does not do what it was built for** (scope, statistics). Seven
   refits have a period median of 1 or more; the rule caught one. Without the seven, D1 is
   0.37 [0.24, 0.49]. Under outliers the rule reduces to "cost at most C″'s chord cost + 9"
   against a track with more freedom, which is the 20 of 100. The rule was changed after
   development and first ran on validation.

9. **The mixed prior is one point of a curve, at its expensive end** (evidence review).
   Every Annex B period where the mixed search differs is a history collapsed to "no
   manoeuvre"; two-manoeuvre targets are called quiet in 10 of 117 against 1. Re-ranking the
   stored candidates at other stated probabilities of a quiet target:

   | Quiet probability | Held-course false | One-manoeuvre called quiet |
   | --- | --- | --- |
   | 0 (repaired search) | 0.53 | 0.13 |
   | 0.01 | 0.09 | 0.14 |
   | 0.1 | 0.02 | 0.15 |
   | 0.5 (registered) | 0.00 | 0.19 |

   A small quiet probability buys nearly all the benefit at a third of the cost. A re-ranking,
   not a re-run; no split has a mixed population, so the 0.00 is close to guaranteed.

10. **The decided statistics' code is untested** (code). `run_shard3`, `study_split3`,
    `classify3`, `_headroom`, `candidates3`, `counts3`, `declared_quiet` and `soundness3`
    have no unit test; "a drifting reference is caught and held" has none; the density ×
    volume test covers one manoeuvre of the Annex B kind at interior points and asserts the
    first start's formula against itself. The README's own tables are still typed by hand:
    the script that checked them is not committed.

## Minor findings

- **Forecasts.** "Seven of eight held" was not enumerated and is wrong by the record as
  written: D1 missed two of its three clauses (the interval excludes 0.5 and includes 0.25);
  D4's "above 0.90 over an hour" is in the decided row of the decision record and missed
  (112 of 125 = 0.896). Fair count: five of seven rows. And the forecasts were written two
  minutes after the development run from its numbers, with near-identical code: "held" is
  replication, not prediction. The one forecast of a quantity known to move, D1, missed.
- "Five readings on four seeds from 0.33 to 0.64" for D1: four readings on three seeds; with
  spec 014's other seeds the range is 0.30 to 0.79.
- Reading 8: correlated errors multiply false manoeuvres by 5.8 (1.29 a period against
  0.22), not three; outliers are the triple.
- Reading 3 ("improves which history comes first") has no interval or paired test.
- The whole-engagement split's fall-backs (4 of 60) and headroom (1.22 [1.03, 1.48]) are
  missing from the record's lists. The headroom on the shifted, correlated and outlier
  splits (1.71, 1.44, 1.50) was quoted without saying that 21% to 30% of their references
  are held, above the limit the study set itself for Annex B.
- "Two thousandths" below the line: 1.3 thousandths by the registered bootstrap, about 3 at
  50,000 resamples; the README's 50,000-resample check did not state its seed.
- D4's denominator is 398, the registered wording says 400 (disclosed; 0.535 over 400).
- "First candidate right" appears as 0.64 (scored periods) and 0.652 (all) without saying
  why they differ.
- Attribution of the long-period false manoeuvres to the prior is consistent (the prior's
  log probability of no manoeuvre is −2.7 at 30 minutes, −12 at 60, −31 at 90) but there is
  no ablation in the search itself; 187 of 398 periods are 30 to 60 minutes and are a
  mixture. D4's 0.53 reflects the split's mix of lengths.
- Where a false manoeuvre is declared under 45 minutes its margin over "no manoeuvre" is
  under 3 in 88% to 100% of cases: a declaration margin is an untried cheap remedy.
- Missed single manoeuvres under the repair are not over-correction: the missed turns are
  33° to 117°, 14 of 16 in periods under 30 minutes, and integrated numerically the
  one-manoeuvre against quiet factor is within ±1 nat in 7 of 10. Unidentifiable, not
  suppressed.
- Prior, small and recorded, not repaired (the code is registered): combined manoeuvres
  have no acceleration constraint (invented ones reach 0.21 m/s² at the 90th percentile);
  speed after a change is unpaired (0.1 to 0.3 nats); `_leg_tail` returns 0 for periods of
  5,868 s or more, so the no-manoeuvre leg term is −690.8 instead of about −40 in 15 quiet
  periods (no decision changes); the no-manoeuvre history is scored from one start (flips 2
  of 212 declarations); interior legs under the 300 s minimum lose their curvature; the flat
  prior without m! penalises m manoeuvres by log m! where the times are determined, which
  bears on its 0.085 of two-manoeuvre targets called quiet.
- `counts.match` and `strip_cut` are two functions, not one rule; they agree on every record
  here and can differ at 240 s. `strip_cut` forgives any found manoeuvre within tolerance of
  a cut one's visible mid-time. 32 of 716 whole true manoeuvres lie within 105 s of a period
  end, where the search proposes nothing.
- `tlsolve --thin` on a run3 plan would be silently run unthinned. `soundness3` falls back
  to 0.15 if the plan omits the limit.
- "Spec 014's search beside" cannot be confirmed as the same search from the records: on the
  200 shared periods of seed 335 its first candidate's evidence differs by more than 1 nat
  in 30 between the two studies' runs. The code path is identical and an unchanged path
  differs as often, so this is believed to be CPU family; the same-run before-and-after rows
  are unaffected.
- Validation and test ran on different CPU families. The limit on held references was moved
  from 0.15 to 0.25 after development hit it; unneeded on Annex B (0.147, 0.133).
- Process: D5 is a line with a budget consequence, which is a gate criterion without an SRD
  §5 row. Do not register a third such rule. Spec to test record took nine hours, which
  explains findings 7 and 10.

## What the owner may conclude about a learned whole-period model

| Where | What the two studies show | Classical control needed first | Not known |
| --- | --- | --- | --- |
| Annex B identification | An oracle is 1.1 to 1.2 ahead; three seeds give inconclusive, material, inconclusive; not decidable at 400 periods | None new; the search is the control | Whether any real identifier gets a third of it |
| Shifted prior | Search 0.095 against the true history's 0.042; first candidate right 0.23; probabilities meaningless | A broadened or mixture prior with a mismatch diagnostic | Whether the gap is the prior or busier targets |
| Correlated errors | 0.165 against 0.098; 1.29 false manoeuvres a period | A correlated-error likelihood (the whitened layer of spec 010 exists) | One severity, 100 periods |
| Outliers | 0.087 against 0.046 | A Huber or edited likelihood in the search | 2% at 10 sd is the easy case |
| Hedging | Both studies are silent | A posterior-weighted track from the stored candidates | Everything |
| Held course | 1.53, self-inflicted; a small stated chance of a quiet target removes most of it | Exists | The cost at other mixes |

Nothing here shows that learning cannot help, nor that it would. Where the simulator's
assumptions hold there is little and uncertain room; where they fail there is a factor of 1.4
to 1.7 against an oracle and no cheap remedy has been tried, so a learned win there now would
be uninterpretable. This project has been caught that way three times (Gate 2's veto, spec
012's prior, Gate T's refit). Free credit changes the cost side of a rule that was written for
the owner's money; it does not change what a result would mean without the controls.

## What the panel wants next (the owner's choice)

1. Corrections to this record (done in the README's corrections section).
2. A hedged track from the stored candidates, and a declaration margin: cheap, classical, CPU.
3. A Huber or edited likelihood and a correlated-error likelihood in the search; a broadened
   prior with a mismatch diagnostic; a small stated quiet probability. Scored on the shifted,
   correlated and outlier splits at more than one severity.
4. Only then a learned whole-period model, registered against 2 and 3 on those splits, with
   a classical control given the same prior.
5. No fourth Annex B identification study: at 400 periods it cannot decide a 1.10 line.

## What should not be concluded

- That learning has 17% to win on Annex B data, or that there is nothing for it to win.
- That the rule's "no GPU budget" is a finding about learning.
- That the evidence repair is finished, or that 0.09 on short periods is what a correct
  evidence gives.
- That 0.44 of wrong histories are ambiguous: the share is the threshold's.
- That the refit's share is a third as a constant.
- That the long-period false manoeuvres are shown to be the prior's by experiment in the
  search.
- That anything here transfers outside this simulator, its independent Gaussian errors or
  this one test seed.
