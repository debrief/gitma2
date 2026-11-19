# Spec 026: panel review, round 1 (2026-11-19)

Five independent reviewers read the spec, the decision record, the tuning, validation and
test records and the code at the registered commit, and recomputed from the per-row errors:

1. numbers and provenance;
2. fairness of the comparison;
3. statistics and the rule;
4. code;
5. scope and conclusions.

**All five approve with findings. Decided in one round.**

The registered outcome stands: on Annex B joining is better than the carry, and a gain from
carrying is not shown. No bug changes a decided number. The recommendation the first record
drew from busier targets went beyond the rule, and what was tested is narrower than its title
says. Figures not in the generated files are the reviewers' recomputations; they are not
registered results.

## Verdict on each registered item

| | As registered | Panel |
|---|---|---|
| Soundness (validation 360) | 0.79 [0.60, 1.04], passes | Reproduced. A gross-fault screen only. The band [0.6, 1.6] has a geometric centre of 0.98, not 0.79 as the record said, and the interval reaches the band's edge (0.601) |
| Annex B carry ÷ joint | 2.332 [1.664, 3.428]: joining better | Reproduced to 4 decimals. Robust under BCa (1.70), cluster-t (1.61), 10 bootstrap seeds (1.62 to 1.67) and 5% trimming (1.54) |
| Annex B alone ÷ carry | 1.072 [0.875, 1.335]: not shown | Robust. It excludes harm worse than about 12% and gains above about 33%; it says nothing about smaller gains |
| Busier carry ÷ joint | 1.351 [0.993, 1.820]: not separated | Stands by the rule, but on a knife edge: the lower limit runs 0.959 to 1.008 over 40 bootstrap seeds (3 of 40 read "joining better"), and course 1.574 [1.069, 2.272] and speed 1.440 [1.013, 2.005] are wholly above 1 |
| Busier alone ÷ carry | 1.287 [1.085, 1.543]: carrying helps | Holds on intervals (BCa, cluster-t, trimmed 1.157 [1.025, 1.436]). But 48 of 92 periods are exact ties, 29 better and 15 worse (sign test p ≈ 0.05). It survives Holm over the 8 range tests but not correction over all 24 |
| Harm | none | None fires. Held course alone ÷ carry in course 1.239 [1.020, 1.540] and busier in speed 1.126 [1.018, 1.262] are wholly above 1 (gains the range-only rule does not decide) |

## Checked and found sound

- **Provenance and order.** Plan `tl-m.json` (`0f1a8cae…`) has one commit, c151052. Every
  shard: seed 361 (validation 360), code `cee4a319…`, clean. Order: registration 23:30:20;
  validation run created 23:30:30 and finished 00:45; test run created 01:59:04 at c151052.
  Seeds 360 and 361 appear in no earlier commit.
- **Recomputation.** Every decided figure and count recomputes independently, and every
  record's `tables.md` regenerates byte for byte.
- **Code.**
  - `solve_ctl(carried=None)` follows `run4`'s `ctl` path step for step, including edit
    and correlation selection, tags, pool order, elimination path and declaration.
  - On every first period of every split the carry equals `ctl` alone: within 2.4e-7 in
    range, and 0.008 in position, which is the float32 rounding of `run8`'s stored tracks.
  - The carried θ's frame and units are right; rows align.
  - No later period lacks a state, and nothing fell back.

## Corrections and narrowings

1. **The recommendation was not the rule's output (scope).** The decision record recommends the
   carry only if carrying helps on Annex B, which decides. It does not (1.072, not shown). The
   busier-target "helps" is a reported observation. "Recommended where a joint solve is not
   available" is withdrawn. Time-late, the earlier bearings are normally held, so that case
   was also undefined.
2. **This is a carried start, not carried information (fairness, scope, code).**
   - The carried state only seeds a fit to the period's own bearings, and it replaces only
     `ctl`'s start from nothing. Nothing from the earlier period enters the likelihood or
     the prior.
   - "Joining better" was therefore near-certain by construction. On Annex B the per-period
     true-history reference is itself 8.4 times worse than joining on these rows; the better
     of alone and carry, taken with hindsight, is 1.97 [1.39, 2.86] worse.
   - The study is a lower bound on carrying. It says "a carried start does not substitute
     for joining", not "carrying is weaker".
   - A carried prior (the state and its covariance, widened through the gap, as a prior in
     the period's evidence) was not tested.
3. **Where carrying moves anything (fairness, statistics).**
   - About half of periods are exact ties with `ctl` alone: 51% Annex B, 52% busier, 62%
     held course. The "median 1.00" is that tie.
   - On busier targets the gain is about a quarter of periods, about twice as good there,
     almost all where the period has no ownship turn of its own (1.72 [1.20, 2.48]; with
     one, 1.01).
   - Where the period's own bearings fix range, nothing changes (alone ÷ carry on own rows
     0.95 to 1.12).
   - Where the carried state is wrong it replaces the safeguard of a start from nothing:
     Annex B periods with their own turn read 0.91 [0.78, 1.02].
   - So "costs nothing" becomes "no harm shown".
4. **Where a period stands alone (fairness).** On rows the period determines alone, carry ÷ joint
   is 1.50 [0.91, 2.41] on Annex B, not separated. With spec 025's busier-target 1.06, neither
   joining nor carrying is shown to help a busier period that stands alone.
5. **Counts (numbers).**
   - Engagements without a two-period layout are skipped: 7 of 70 Annex B, 10 busier, 4 and
     4 on the other splits.
   - Later periods without a scored row: Annex B 70 of 75, busier 92 of 107.
   - The validation README mixed bases: 229 periods, 218 scored for alone ÷ joint, 118
     later periods scored.
6. **Splits share engagements** (wild bearings is Annex B's; held course nearly all its
   layouts), so agreement across them is not replication.
7. **Minor code points, recorded, not repaired.**
   - `_per_period_facts` marks a gap manoeuvre if either neighbouring gap holds one, but the
     carry crosses only the gap before. This affects a by-kind reading only.
   - The fall-back count covers a missing previous track, not a solve that returns nothing.
   - No unit test covers the edit or correlation branches of `solve_ctl` against `run4`, or
     `carry_chain`; the equivalence script covered two short periods.
8. **Cheaper, in figures.** Shared-runner timings: the joint solve about 2.3 to 2.7 times
   `ctl` alone; the carry about the same as alone.
9. **Seeds.** 354 to 359 are unused (skipped to stay clear of PR 47's numbering, not spent).

## Outcome, as the panel words it

By the registered rule, joining is better than this carry on Annex B (2.33 [1.66, 3.43]), on
wild bearings and on held course. On busier targets the two are not separated in range (1.351
[0.993, 1.820], a knife edge; joining is better in course and speed). The joint solve stays the
standing time-late system for several periods of one target, within spec 025's conditions.

A carried start (the previous period's declared state as a start for the period's own search)
shows no effect on Annex B. On busier targets it helps in about a quarter of periods (1.29
[1.09, 1.54]), almost all without an ownship turn of their own. No harm is shown. It is a
different start, not carried information, and nothing here bears on carrying a prior.

**Not to be claimed:**

- that carrying costs nothing, or helps, without the split;
- a recommendation as the rule's outcome;
- that carrying state cannot match joining;
- that joining beats carrying on busier targets in range;
- that the carry's gain is a determined answer;
- anything beyond spec 025's conditions;
- any learning.

## What the panel wants next (owner's choice), in order

1. A carried prior: the previous period's state and covariance, widened through the gap by
   Annex B's manoeuvre rates, as a prior in the period's evidence. Score it against joint and
   alone on spent seeds first; this decides whether joining is needed.
2. A per-period consistency flag (alone against joint or carry, by history and evidence),
   tested on whether it finds the twice-as-bad periods; markers on inferred gap manoeuvres.
3. A stated uncertainty for the joined track.
4. A stress split with longer, busier gaps.
5. Association across a gap: owner's scope.
