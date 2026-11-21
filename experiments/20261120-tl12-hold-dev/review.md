# Spec 033: panel review of the development records and write-up (2026-11-21)

Three independent reviewers read the spec, the two development records (`experiments/20261120-tl12-dev/`, `experiments/20261120-tl12-hold-dev/`, with `evidence/`), the code and the draft write-up and slides. They reviewed through three lenses:

1. numbers, provenance and code;
2. statistics;
3. scope.

**All three approve with findings.** Every committed number reproduces, and `readings.txt`, `paired.txt`, `evidence/summary.txt` and both `tables.md` regenerate byte for byte. The draft claimed more than the data support in four places, and the posts and READMEs are corrected below. This is development work on one spent seed. Nothing here is a registered result.

## Checked and found sound

- **Shared engagements.** Both runs share all 40 engagements: identical layouts, true histories and kinds. The configs differ only in the ownship's leg range.
- **`Period.ownship_turns`.** The change applies only when the meta carries a list. Generator data are unchanged and tested.
  - For earlier long-simulator windows it now returns every turn. The only consumers test whether any turn exists or read the first one, so no earlier record moves.
  - The comment at `long/windows.py:108` ("reads the first and second turns") is now stale. It is left as is: the long-engagement studies bind digests of `long/`.
- **The long split source** in `tma2-tlsolve`: no bug found.
- **Arithmetic.** Cost 11–16× checks out. "About −29" is a sum of medians (legs −12.7, changes −16.7), not a median.

## Corrections and narrowings

1. **"Join up to about an hour" is not supported as a rule.**
   - The bands and the one-hour cut were chosen with the data in view; the spec said only "by gap length".
   - Of 18 band intervals, one is separated: held course at 50–70 min, 2.85 [1.49, 6.05]. It is robust to leaving out any one engagement (2.31–3.36).
   - The slope of the per-period log ratio on gap length is not separated in either run: −0.16 [−0.39, +0.03] and −0.15 [−0.36, +0.04] per 10 min.
   - In the turning run the median period at 50–70 min is 0.80 and joining is better in only 35% of periods. The band means rest on tails.
   - The cut is fragile: split at 60 min, the two sides read 1.43 / 0.88 and 1.77 / 1.00.
   - The title, slide heading and track table worded it as a finding. They now say it is a suggestion from one seed and bands chosen after the data.
2. **"Beyond 70 min joining loses in both runs" becomes "reads below 1 in both runs; not separated".**
   - 0.80 [0.48, 1.28] and 0.71 [0.47, 1.02]; medians 0.95 and 0.88.
   - The geometric means are pulled by the 30–36% of periods that are twice as bad.
   - The per-period ratios barely correlate across the runs (r = 0.15; −0.18 in the ≥70 band). The own-turn share in that band is 0.87 in one run and 0.09 in the other. So the two readings are neither one observation seen twice nor a replication: they may have different mechanisms.
3. **The evidence diagnostic does not establish "identifiability, not search".**
   - Its re-run declared a different number of manoeuvres from the scored run in 5 of 21 engagements (ordinals 9, 13, 16, 20, 33). It ran on another CPU family (spec 024's gotcha). The cross-tab of evidence against errors therefore pairs one run's histories with another's errors.
   - Restricted to engagements whose counts match, the two groups are 0.44 over 2 engagements and 0.84 over 11. The 0.80 against 0.57 split is not a result: permutation p = 0.25, and 0.57 is a mean over engagements where the rest of the study pools periods (0.47).
   - Most differences are small:
     - 8 of 21 lie within ±5 units, 13 within ±10;
     - by a 10-unit margin, the declared history is better in 5 and the truth in 3;
     - three of the six "search shortfalls" are under 4 units.
   - Laplace pairing defects of 1–3.5 nats are recorded (spec 015). The "true" history is a prior-fitted mode from neutral starts, evaluated under the winning prior only. The edge rule removes cut manoeuvres from the truth with no counterpart for the declared history.
   - Allowed wording: in most engagements the Laplace evidence does not prefer the true gap history, and search shortfall is a minority. Whether better search would help is not resolved.
4. **The information through a long gap exists given the history.**
   - In the 70–90 min band, the span fitted with the true structure beats `ctl` alone: 2.35 [0.96, 5.98] (held course) and 2.48 [1.30, 4.90] (turning).
   - The joint solve is about 3.1 to 3.3 times that reference's error.
   - What fails is selecting the gap history. Any statement about long gaps concerns this evidence and this search, not joining as such.
5. **The clearest signal is whether a period has its own ownship turn.**
   - Joining helps periods without one: 2.15 [1.23, 3.71] in the turning run overall.
   - Below 70 min gaps: 2.24 [1.13, 4.50] (turning) and 2.13 [1.29, 3.55] (held course).
   - Periods with their own turn read about 1.1–1.25, not separated.
   - In the turning run the own-turn share rises with the gap (0.71 / 0.80 / 0.87), so the band trend is partly composition. The ≥70 band of the held run still reads 0.70 without own turns.
   - Any suggested practice is conditioned on both: join a period that has no ownship turn of its own across gaps up to about an hour.
6. **The carried prior:** the finding is scoped to k4 as tuned on spec 030's 5–30 min gaps, propagated at constant velocity with spec 030's isotropic process noise. It is not a finding about carried priors in general. In the turning run k4 is about 3.5 times the joint solve on periods without their own turn.
7. **Smaller points:**
   - "Everyone's error roughly doubles" holds for geometric means; the median for alone is 1.49.
   - The side-by-side "all periods" columns cover 109 and 92 periods.
   - The tl12-dev README's claim that the bands hold the own-turn share fixed is false for its ≥70 band.
   - Intervals near 1 are printed to three decimals: held overall 1.34 [1.01, 1.84] is marginal.
   - The joint solve's declared manoeuvres reach about 900 s in 18 of 189. A duration bound may contribute, which is untested.
   - The track table said "031"; this study is spec 033.

## Outcome, as the panel words it

On one spent seed of the long simulator, across 30–90 min gaps:
- joining helps periods without their own ownship turn at gaps under about 70 min, by about 2;
- readings beyond 70 min fall below 1 in both runs, not separated;
- the true gap structure would still help there, so the shortfall is in selecting the gap history: in most engagements the Laplace evidence does not prefer the true one;
- k4, as tuned in spec 030, adds nothing across gaps this long.

A suggestion, not a rule: join a period without its own ownship turn across gaps up to about an hour.

**Not to be claimed:**
- "identifiability, not search";
- that better search would not help;
- that joining fails or loses beyond an hour;
- that carried priors carry nothing in general;
- any threshold as practice beyond a suggestion.

## What next (owner's choice)

1. Stop and write up the gap track with the suggestion worded as above.
2. Register on fresh seeds (369 onward), held-course geometry, with a gap × own-turn rule fixed beforehand and about 140 periods per band.
3. First, a development check on spent seeds:
   - re-run the evidence comparison on the scored run's own histories, on one CPU family;
   - report it at several margins;
   - give the joint solve the true structure in the gap only.
