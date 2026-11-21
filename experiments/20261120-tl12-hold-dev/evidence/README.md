# Spec 033 diagnostic: why the joint solve loses beyond 70 min gaps

**Panel review (2026-11-21, `experiments/20261120-tl12-hold-dev/review.md`): three approve with findings; the readings below are narrowed there.** Where this README and the review differ, the review stands.

Development work on spent seed 348 (long simulator), not a registered result.

- **Run:** CI workflow `tl12-evidence.yml`, run 44803371523, at 8994151 (`results/tl12ev-tl12ev-hold-44803371523`).
- **Engagements:** the 21 hold-course engagements of `experiments/20261120-tl12-hold-dev/` that have a gap of at least 70 min.
- **Files:** one JSON per engagement from `scripts/research/tl12_evidence.py`, and `summary.txt` from `scripts/research/tl12_evidence_summary.py`.

## Method

For each engagement the diagnostic computes two Laplace log evidences on the same edited joint problem, both under the prior the declared history won:

- `ctl`'s **declared** history over the span, with the gaps' bearings masked;
- the **true** history: the truth's structure and kinds, fitted with that prior from `reference`'s neutral starts.

True manoeuvres cut by the span's start are left out (the edge rule). With them in, a 15-second fragment cost about 470 units in the change prior on engagement 6.

## What it shows

1. **The evidence prefers the simpler, wrong gap history in most engagements.**
   - The declared history has at least the truth's evidence in 15 of 21 (median true − declared −3.8).
   - It declares fewer manoeuvres in 18 of 21: 123 against 178 true.
   - The truth fits the bearings slightly better (median fit +1.6). Its extra Occam volume (+22.1) does not pay for its extra prior cost (legs −12.7, changes −16.7).
   - Across an hour of masked bearings, nothing in the data asks for the manoeuvres that happened. The prior's preference for fewer then decides, which reads as ambiguity in the Laplace evidence (panel: most differences are within ±10 units, and whether search matters is not resolved).
2. **The search falls short in about a quarter.** The truth has more evidence in 6 of 21, by more than 10 units in 3 (ordinals 13, 28, 33). More search could recover these.
3. **Both kinds lose to `ctl` alone on the periods after the long gap.**

   | engagements where | alone ÷ joint | engagements |
   |---|---|---|
   | the search fell short | 0.57 | 5 |
   | the evidence prefers the declared history | 0.80 | 12 |

   Panel: the re-run declared a different history from the scored run in 5 of 21 engagements (another CPU family), so this split is not a result (0.44 over 2 and 0.84 over 11 where counts match).

## Limits

- One spent seed, 21 engagements, and the Laplace approximation throughout.
- The "true history" is fitted with the prior, from neutral starts (`reference`), so it can sit in another minimum.
- On engagement 23 the change prior alone accounts for −134 units. A support edge (overlapping manoeuvres) is possible and was not examined.

## Reading

Beyond about an hour of gap, a single joint history must commit to manoeuvres the bearings never saw. The evidence picks fewer than happened, and that wrong gap history pulls the observed periods. This supports the operating rule suggested by the gap bands: join across gaps up to about an hour, and solve each period alone beyond that. The diagnostic suggests the rule; it does not decide it.
