# Spec 033 follow-up: the evidence re-check, histories and errors in one job

Owner 2026-11-21, option 3 of spec 033's panel order. This is development work on spent seed 348
(the long simulator), not a registered result; nothing was trained.

- **Run:** CI workflow `tl12-evidence.yml`, run 44904137666 at b372401 (`results/tl12ev-tl13ev-hold-44904137666`).
- **Engagements:** the 21 hold-course engagements of `experiments/20261120-tl12-hold-dev/` with a gap of at least 70 min.
- **Files:** one JSON per engagement from `scripts/research/tl13_evidence2.py`, and `summary.txt` from `scripts/research/tl13_summary.py`.

## Why again

The first diagnostic paired a re-run's declared histories with another run's errors, on another CPU family. In 5 of 21 engagements the re-run declared different histories from the scored run (spec 033 panel).

Here each engagement's job computes everything itself, on one machine (recorded per engagement):

- the joint solve and `ctl` alone, scored on the scored run's rows;
- three structures refitted with the prior from neutral starts:
  - the true history;
  - the declared history;
  - the declared manoeuvres outside the gaps with the true ones inside them (the panel's "true structure in the gap only");
- the evidence of each.

## What it shows

1. **The truth's refit does not beat the declared history.** The true history is compared with the better of the declared history as searched and as refitted (21 engagements):

   | margin | truth better | declared better | within the margin |
   |---|---|---|---|
   | 1 unit | 5 | 12 | 4 |
   | 3 units | 1 | 11 | 9 |
   | 10 units | 0 | 6 | 15 |

   The first diagnostic's six "search shortfalls" came from comparing a refitted truth with the searched history. A neutral refit can land in a worse minimum: the searched history beats its own refit by 10 to 24 units in 4 engagements.
2. **A gain from the true gap structure is not shown, at this size.**

   | after gaps of at least 70 min (22 periods, 17 engagements) | ratio |
   |---|---|
   | declared refit ÷ gap-true (like with like) | 0.96 [0.67, 1.40] |
   | joint ÷ gap-true | 0.88 [0.56, 1.39] |
   | alone ÷ true | 2.07 [1.07, 3.76] |

   - Over all later periods, declared refit ÷ gap-true is 1.14 [0.74, 1.68].
   - The full true history still beats `ctl` alone, at 2.38 over all later periods.
   - So its advantage comes from the manoeuvres inside the observed periods, not from the gap.
   - The gap-true structure also has lower evidence than the best declared history in 20 of 21 engagements. Its refits are fragile (−199 on ordinal 16).
3. **The ">70 min reversal" does not reappear on one machine.** After gaps of at least 70 min, alone ÷ joint is 0.97 [0.58, 1.73], median 1.03: nothing shown either way. The interval contains the scored run's 0.71; the shift between them is the search's known CPU-family sensitivity, not sampling noise. Over all later periods it is 1.02.
4. **The refit costs little.** Joint ÷ declared refit is 0.94 [0.81, 1.11] over all later periods.

## Review (one agent, approve with findings)

All numbers reproduce from `summary.txt`. The wording above was narrowed on its findings:

- The truth is refitted from neutral starts while the declared side keeps the better of search and refit, so finding 1 does not show that the search is not the limit.
- Gap-true's evidence is below the declared refit's by 21 to 197 units in eight engagements, far beyond an Occam penalty. Those refits are in poor minima, so finding 2 may be a fitting failure. Where gap-true fitted well it sometimes won (ordinal 16: 6.72; ordinal 32: 24.6).
- Gap manoeuvres are classed by midpoint (`tl13_evidence2.py`). A declared manoeuvre straddling a gap edge stays "outside" while the true one is added, so gap-true can hold a manoeuvre twice.
- Engagements 6, 25 and 30 enter the evidence counts but have no scored later periods.
- Subsets with fewer than five engagements now print a median without an interval.

## What this changes in spec 033

- **"The true gap structure would still help beyond 70 min (2.35, 2.48)" is withdrawn as a statement about the gap.** That reference is the whole true history. Given only the true gap manoeuvres, no gain is shown (fragile refits).
- **"What falls short is choosing the gap history" is withdrawn.** The shortfall, as far as this can see, is in the observed periods' own histories.
- **Beyond about an hour, nothing is shown either way.** The suggestion stands as "joining a period without its own ownship turn helps across gaps under about an hour; beyond, nothing is shown".
- "The evidence rarely separates the true history from a simpler one" stands: no engagement has the truth's refit better by more than 10 units.

## Limits

- One spent seed and 22 periods after long gaps.
- Engagements ran on four CPU families, but each one entirely within a single job.
- The refits from neutral starts are fragile.
- The full-truth reference is told the observed periods' manoeuvres too, so it is not a bound on joining.
