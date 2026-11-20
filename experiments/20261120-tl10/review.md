# Spec 028: panel review, round 1 (2026-11-20)

Five independent reviewers read the spec, the development, refinement, decision, validation and
test records and the code at the registered commit. They recomputed from the per-row errors and
looked at the record through five lenses:

1. numbers and provenance;
2. fairness of the comparison;
3. statistics and the rule;
4. code;
5. scope and conclusions.

**All five approve with findings. Decided in one round.**

The registered outcome stands: on Annex B a carried prior (k4) helps against `ctl` alone, and no
harm condition fires. No bug changes a decided number. What the test supports is narrower than
the first record's recommendation in four ways:

- it shows a carried prior helps, not that the 4× inflation matters;
- the gain is on rows the period cannot determine alone;
- k4's uncertainty is too wide, not calibrated;
- the use case is conditional.

Figures not in the generated tables are in `supplement.json`, from
`scripts/research/tl10_supplement.py`. They are the reviewers' recomputations, not registered
results.

## Verdict on each registered item

| | As registered | Panel |
|---|---|---|
| Soundness (validation 362) | 0.915 [0.709, 1.149], passes | Reproduced. A gross-fault screen only |
| Annex B alone ÷ k4, range | 1.592 [1.206, 2.132]: helps | Reproduced exactly; robust. Lower limit 1.18 to 1.22 over 20 bootstrap seeds; leave one engagement out 1.52 to 1.66; trimmed 10% at both ends 1.495 [1.153, 1.968]; sign-flip p ≈ 0.002. Median per period 1.087: the gain is not the typical period |
| Harm, every split and quantity, and Annex B own turn | none fires | Reproduced. The rule had little power. Own turn (n 32, 32 engagements) would show harm only below about 0.68, with about 20% power against a true 0.80. "No harm" means no loss larger than about a third was shown |

## Checked and found sound

- **Provenance.**
  - Plan `tl-o.json` (`74166535…`) has one commit, 09d03dc, the registration, and is byte-identical to both records' `plan.json`.
  - Code digest `90a19712…` matches every shard. Nothing under `src/` changed between fb5fa2a and the test.
  - Clean trees throughout. Seeds 362 and 363 appear first in the registration commit.
  - `tables.md` regenerates byte for byte.
- **Fairness of the mechanics.**
  - Same rows for every system.
  - k4 replaces `ctl`'s start from nothing; it does not add a start.
  - Same pooled candidates and priors.
  - Every later period was carried (none fell back), so no constructed tie hides in the shares.
  - No data leaked: k4 was chosen on spent 361, checked on spent 360, and 363 is fresh.
- **Code.**
  - The wrappers take effect, because `retest` imports at call time, and they are restored after an exception.
  - Density and volume pair for the four replaced state parameters.
  - The course Jacobian is right.
  - The chain carries the last state and time.
  - First periods are bit-identical across carried systems.
  - The ×16 is applied after propagation. `truth_md2` uses the covariance actually used.

## Corrections and narrowings

1. **A carried prior helps; the inflation is not shown to matter (fairness, statistics, scope).**
   - Paired uninflated ÷ k4 is 0.991 [0.781, 1.252] on Annex B, and 0.957 to 1.040 elsewhere.
   - The uninflated prior would also pass the registered rule on this seed.
   - k4 was chosen to remove an own-turn harm seen on seed 361 (0.51). That harm did not recur on 360, 362 or 363: uninflated own turn here is 1.217 against k4's 1.221.
   - The first record's "what the test shows of the inflation is the narrower own-turn interval" goes beyond the data and is withdrawn.
   - The recommendation is "a carried prior, inflated as a safeguard whose benefit on accuracy is not shown on fresh seeds".
2. **The gain is on rows the period cannot determine alone (fairness, scope).**
   - On rows the period determines alone, alone ÷ k4 is 1.040 [0.765, 1.476] on Annex B (median 1.00), 0.924 with wild bearings and 1.000 on held course.
   - Annex B periods without their own ownship turn: 1.968 [1.323, 2.956]. With one: 1.221 [0.843, 1.848].
   - So a carried prior makes undetermined periods answerable; it does not improve a period's own estimate. This is spec 025's pattern.
3. **Against the carried start, the existing alternative (fairness).**
   - Not registered: carry ÷ k4 is 1.600 [1.049, 2.742] on Annex B (median 1.06), 1.435 [1.141, 1.781] busier, 1.37 wild bearings, 1.54 held course.
   - On own rows it is level (1.02).
   - The recommendation survives against spec 027's start, narrowly on Annex B.
4. **k4's uncertainty is too wide, not calibrated, and it carries little beyond position (code, scope).**
   - Coverage 0.947 comes from a median d² of 0.51 against 3.36, so the sds are about 2.6 times too wide. The uninflated 7.58 implies about 1.5 times too narrow, which puts the right scale nearer 1.5 than 4.
   - The process noise is mis-shaped:
     - isotropic velocity noise puts half a turn's change into speed (speed sd 1.2 to 6.2 m/s against 0.4 to 0.8 true);
     - constant-velocity propagation runs the mean ahead of a turning target.
   - The Laplace covariance of one declared history is too narrow in the tail even with no manoeuvre in the gap: held-course coverage uninflated is 0.58.
   - After ×4 the course sd is at least 1 rad in every later period and the speed sd is above 5 m/s in 94 to 100%. k4 is in effect a weak cross-bearing position band with correlations, not a carried state.
5. **The use case is conditional (scope).**
   - Spec 027's panel withdrew "where a joint solve is not available", because time-late the earlier bearings are normally held. Cost is no reason: joint takes 64 s against k4's 26 s an engagement on Annex B.
   - The supportable wording is: within this simulator, if only the previous declared state and its covariance are kept, a period solved under them is better than one solved from nothing.
   - A real hand-over carries another estimator's track and uncertain association; none of that was tested.
6. **Secondary splits are reported, not decided, and not all are firm (statistics, scope).**
   - Wild bearings' "helps" is 1.346 [1.010, 1.870], with the lower limit 0.999 to 1.027 by bootstrap seed, a trimmed interval of [0.935, 1.692] and a median of 1.012. Read it as "not separated; a tail".
   - Wild bearings in speed is twice as bad in 30% of periods and twice as good in 20%.
   - Held course's 2.32 is against a near-useless baseline (alone ÷ joint 12.7). Its median is 1.27.
   - Busier holds under trimming: 1.50 [1.21, 1.83].
7. **Against joining (numbers, statistics, scope).**
   - k4 ÷ joint on Annex B is 1.396; the lower limit runs 0.973 to 1.020 by bootstrap seed. That is on the line, not "close to joining".
   - By seed it is 2.18, 2.08, 1.67 and 1.40.
   - It is separated with wild bearings (1.74) and on held course (5.20).
   - Busier periods with a gap over 20 minutes: 1.87 [1.11, 3.14].
   - Joining is not shown unnecessary anywhere.
8. **Seeds.**
   - Annex B alone ÷ k4 by seed: 1.586 (360), 1.220 [0.942, 1.572] (361, which would not pass and chose k4), 1.512 (362), 1.592 (363).
   - Pooled over the four: 1.489 [1.325, 1.688] over 324 engagements. This is not an independent estimate, because 361 chose and 360 checked.
9. **Counts.**
   - The README's "later periods / engagements" gave the engagements run. The bootstrap resamples those with a scored later period: 63 Annex B, 80 busier, 45 wild bearings, 48 held course.
   - Coverage pools every carried period (76 on Annex B), including 4 with no scored rows.
10. **Recorded, not repaired** (the code is registered):
    - The wrapped course Gaussian is normalised on the line, not the circle (about 0.4 to 0.9 nats; the same for every candidate within a period, so declarations are unaffected at w = 1, though it biased the development mixtures).
    - `_log_prior` removes the first leg's speed density but its shoulder residual stays in the fit (active only outside 1.54 to 10.29 m/s).
    - `end_state_covariance` drops the carried term if called outside `carried_evidence()`.
    - run10 repeats the variance floor as a literal.
    - The wrappers are process-global.
    - The verdict is applied by hand: `summary.json`'s `verdict` is spec 025's rule, and no code computes spec 028's.
    - `tables.md` named `tl8_tables.py` as its generator; it is now `tl10_tables.py`, a header change only.

## Outcome, as the panel words it

By the registered rule, a carried prior (k4) helps against `ctl` alone on Annex B: 1.59 [1.21, 2.13]. The gain is in periods the bearings leave undetermined, about 2 without an ownship turn of the period's own; on rows the period determines alone it is level. No loss larger than about a third is shown on any split. The test does not show that the 4× inflation helps beyond the uninflated prior. k4's uncertainty covers the truth because it is too wide (about 2.6 times in sd). The joint solve stays the standing system for several periods of one target. Within this simulator, when only the previous declared state and its covariance are kept, a period solved under them is better than one solved from nothing.

**Not to be claimed:**

- that the inflation, or the factor 4, is better than none;
- that k4 states a calibrated uncertainty, or carries course or speed;
- that a sequential solve is close to joining;
- that a period's own estimate improves;
- secondary-split "helps" as decided;
- any operational recommendation beyond the simulator's hand-over;
- gaps over 30 minutes, more than three periods, an external track source, or uncertain association;
- any learning.

## What the panel wants next (owner's choice), in order

1. Restate the recommendation as conditional and record these narrowings. Done in the README.
2. A consistency flag: the carried prior's d² against the period's own fit, tested on whether it finds the twice-as-bad periods (11% on Annex B).
3. A calibrated carried prior on spent seeds:
   - a scale near 1.5, or per component;
   - process noise shaped to turns, speed changes and their effect on position;
   - the manoeuvre and no-manoeuvre mixture the spec named first;
   - a prior over the previous period's candidate histories.
4. A stress split with longer gaps and more periods, where a carried state is the realistic option.
5. Only if the hand-over case is real: a carried state from another estimator, with uncertain association, as its own registered study.
