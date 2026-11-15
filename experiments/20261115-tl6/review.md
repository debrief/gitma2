# Spec 018: panel review, round 1 (2026-11-15)

Five independent reviewers (numbers and provenance; the design and its fairness;
statistics and the conditions; the hedged track and its spread; scope and conclusions)
read the spec, both tuning records, the decision record, the validation and test records
and the code, and recomputed from the per-row errors (results branch
`results/timelate-tl-g-test-43677426621`). **All five: approve with findings. Decided in
one round.** The registered outcome stands: no gain on either busier-target split for
either output; by the rule the standing control stays. No bug changes a decided number.
Several of the first record's secondary sentences read sampling noise as findings, and
are corrected.

Figures here that are not in the generated files are the reviewers' recomputations from
the test's (and, where marked, the tuning run's) per-row errors and period files. They are
not registered results.

## Checked and found sound

- All 36 cells of the conditions table recompute to the printed digits with independent
  code; the spread coverages, control ÷ true, the by-kind, tercile and pooled-group
  figures reproduce.
- "No gain" for the declared control on shifted targets holds under every statistic tried:
  t = −0.05, sign test 166 up and 181 down, 10% trimmed mean 0.998, median 1.000; five
  bootstrap seeds move the limits by 0.003.
- All 23 files bound in `decision.json` match at registration (a9c7500), at the test's
  commit (d126456) and at HEAD; nothing under `src`, `configs` or `.github` changed
  between them. The control's code digest is study L's (`e5040f5e…`).
- Order: registration 02:24:15; validation launched 02:24:24 and recorded 04:35:14; one
  test run, attempt 1, 04:35:20; one results branch.
- `tables.md` and `supplement.md` regenerate byte for byte.
- The member chosen is the member with the most evidence in all 1,250 periods; the
  declared adaptive track is that member's in every period; key order, columns and the
  harm loop over all six splits are right.
- Mean of ranges against range of the mean state: the same to five parts in a million.

## Findings that change the reading

**1. What the null means: this evidence does not rank these priors by accuracy in one
period.** The per-period posterior over the 30 members is nearly flat (median largest
probability 0.12 to 0.15; over 0.5 in at most 3% of periods; the top two members are 0.17
nats apart in the median). Within a shifted period, a member's probability and its range
error are uncorrelated (median rank correlation −0.05; wrong sign in 54% of periods). The
chosen member is 1.9 times the member best in hindsight; against a central fixed member
it is 1.03 to 1.05 better, not separated. The choice avoids bad members; it does not
adapt. Not shown: that a prior cannot be adapted from one period in general.

**2. "No gain" is a null about gains over about 8%, not about any gain.** The test could
detect 1.12 at 80% power; its power at the tuning effect (1.10) was 0.67. Pooled over the
tuning, validation and test seeds the declared control is 1.01 [0.95, 1.08] on shifted
targets. The first record's "flattered by all of the effect" overstates it: regression to
the mean after choosing a second design is a sufficient reading, not a demonstrated one.

**3. The cost on Annex B targets is understated by the rule's output.** Three seeds give
0.90, 0.80 and 0.93; pooled, 0.91 [0.84, 0.98] in range. And it is the design's, not
adaptation's: the standing control's first candidate comes from Annex B's own prior in 207
of 273 periods, where the adaptive control is 0.89 [0.80, 0.99]; in the other 66 it is
1.05. A crude hybrid (the control when its top evidence beats the family's best, else the
adaptive control) is 1.00 [0.94, 1.06] on Annex B, 1.02 on shifted and 1.06 [1.00, 1.13]
on shifted 2: an estimate only, with incommensurable evidences. A family that included
Annex B's prior was not run.

**4. The family was not blind to the splits.** Its grid (leg means 900, 1,350, 2,000 s; sd
ratio 0.35; largest turns 60°, 100°, 150°) was set after the first tuning run named what
the grid lacked, and sits close to the test splits' own statistics (900/0.33/75°,
1,500/0.36/120°, 2,100/0.29/160°). That favours the family, which still gained nothing,
so the verdict is strengthened; but "not told the split" in the decision record
understates what the designer knew.

**5. "None of the three is it" over-reaches.** Members refit one shared candidate set from
two searches; the true prior has its own search. On shifted targets the true-prior
search's declared history is declared by none of the 30 members in 42% of periods (there
adaptive ÷ true is 1.22 [0.99, 1.51]; elsewhere 1.03). The family also differs from the
truth in dimensions not varied: speed-change range, kind weights, turn-rate floor,
smallest turn. Search-against-refit and those dimensions are confounded. A fixed member
that refits shared candidates is not a search under that prior.

**6. The true statistics' gain is a tail, and "worth less than spec 017 found" is
sampling.** Three seeds give 1.17, 1.22 and 1.10, mutually consistent; pooled 1.15 [1.07,
1.23]. In course it is separated here (1.20 [1.04, 1.39]). On this seed the ten best
shifted periods of 355 carry 87% of the gain (1.01 without them), and the true-prior
search is over twice as bad as the control in 13% of periods. It is a reference, not a
ceiling.

**7. The hedge costs about 10% in course everywhere, as a tail; the two bold cells are the
ones that crossed the line.** The shifted course cell's upper limit is 0.998 and flips
with the bootstrap seed; the outlier split is the first 93 Annex B periods under other
bearing errors, not an independent sample. Pooled over the six splits the hedge is 0.90
[0.85, 0.95] in course and 0.93 [0.88, 0.98] in speed against the control, and worse than
its own declared track in course on shifted (0.91), shifted 2 (0.89) and held course
(0.85). The median period is level and the hedge is better in more periods than it is
worse. No split shows the hedge worth having.

**8. The spread verdict is a coin's toss, and one factor cannot state this spread.**
Bootstrapped by period, shifted coverage is 0.897 [0.870, 0.923] and Annex B 0.944 [0.920,
0.965]: "not honest by three parts in a thousand" should read "not separated from the
band's edge". The factor is a tail quantile set by about 20 periods (tuning 1.95 [1.53,
2.22]; test 2.68 [2.24, 3.30]). With it, one stated sd covers 0.74 to 0.96 where a normal
spread gives 0.68, and 8% of shifted periods have coverage under a half. The spread fails
where the mixture is confident (shifted coverage 0.96 where the first candidate has under
half the weight, 0.84 where it has over 0.95) and is honest where candidates disagree.
What an analyst could be shown: the declared track and a flag "candidates disagree".

## Corrections to the first record

- "No fixed member is separated from the control on shifted targets" is wrong: none is
  better; 9 of 30 are separately worse on shifted targets and 27 of 30 on Annex B.
- "The inferred rate barely moves" is wrong as worded: the medians order correctly and the
  two busiest leg means are chosen in 43% of shifted periods against 21% on Annex B and 9%
  on shifted 2. It moves, shrunk by about half and widely scattered per period.
- "It loses where the bearings say most" is a post hoc tercile, a tail (trimmed means 0.91
  and 1.07; no difference on ranks), and does not repeat on the tuning seed (tight third
  1.06 [0.79, 1.41]).
- "Not separated from nothing on the main split" holds in range only.
- "Level with the declared control in range and worse in course": worse in course on
  shifted, shifted 2 and held course; level on the other three.
- The validation figures were on 53 scored periods of 60. The miss rates exclude
  manoeuvres cut by the period's edge (0.49 and 0.51 counting all).
- Two-decimal intervals hide the side of 1: the hedge's shifted 2 speed upper limit is
  1.005 (not harm); the declared Annex B range and speed limits are 1.015 and 1.014; the
  declared correlated range limit is 1.005.
- The standing control's own hedge at 0.71 on held course is the undeclared search's
  fault (its first candidate has a manoeuvre in 0.49 of quiet periods), not hedging's;
  the median period is 0.93.
- The adaptive control's share of the true-prior search's gain (SC-001) is undefined
  (−0.02 [−2.17, 1.56]): the denominator is not separated from zero.
- The runaway shifted period (246) also dominates its groups of 5 and 20; only the
  whole-split choice was checked without it.

## Recorded, not repaired (the code is registered)

- The member is chosen on plain evidences while the declaration and the mixture use the
  quiet probability.
- `hedged_spread` treats a candidate's non-finite sd as zero (count not recorded);
  `np.linalg.inv` does not raise on near-singular curvature (0.5% of shifted rows state an
  sd above the range); the mixture keeps each history's heaviest member and does not sum
  over members; the sd is not tempered at temperatures 2 and 3.
- `range_sd`, `hedged_spread` and `run6` have no unit tests.

## Not delivered (added to the README's list)

A family member with Annex B's own prior; a search under each member; IMM, EKF and one leg
on these periods (a constitution rule; scored in spec 017 on splits of the same kinds); a
single table for SC-004; a spread for course and speed.

## The panel's order for what follows (the owner's choice)

1. **Recommended: stop identifying the prior, and write up specs 013 to 018 as a whole**,
   with `ctl` standing.
2. One development-only diagnostic on spent seeds (a search under the nearest member, and
   under the truth's speed-change and kind ranges) to settle finding 5. No new seed.
3. Change the information, not the inference: ownship manoeuvre advice, longer periods
   (spec 017: 0.37 of busy targets' manoeuvres barely show).
4. The "candidates disagree" flag as an output, with a quantile-calibrated spread.
5. Over-reach: any learned proposer or GPU run; "priors cannot be adapted"; adopting the
   quiet-target gain (1.05 here, 0.91 on the tuning seed).
