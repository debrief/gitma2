# Gate T (second registration), test seed 331

Run 43258614933 (`timelate/tl-b-test`, commit 34da02f, clean tree, Intel Xeon 6975P-C), plan
`configs/timelate/tl-b.json` (`08793d8b…`), time-late code `88d14eab…`, as bound in
`../20261112-gt2-decision/`. 300 periods a split; 277 (Annex B) and 267 (shift) have
determined rows (28,623 and 26,076 scored rows). Files: `summary.json`, `score.txt`,
`*.periods.json`, `plan.json`, `run.json`, `ci.json`; per-row errors on
`results/timelate-tl-b-test-43258614933`. Seed 331 was generated in this run and nowhere
before. **The verdict is the panel's (`review.md`); this file is the record.**

## The checks

| Check | Result | Forecast (probability) | Outcome |
| --- | --- | --- | --- |
| **T-a** reference soundness, band [0.8, 1.3] on rows bounded below 0.05 | 1.05 | 1.10; pass (0.80) | pass (validation 1.26 was the stop rule) |
| **T-b** C″ ÷ search, interval above 1.10 | **2.27 [1.76, 2.67]** | about 2.4; pass (0.92) | **pass** |
| **T-c** the same under the shifted prior, above 1.00 | **1.69 [1.39, 2.14]** | about 1.7; pass (0.85) | **pass** |
| **T-d** true history in the first three (≥ 0.60); calibration gap (≤ 0.10) | 0.71; −0.03 | 0.73; ±0.07; pass (0.60) | **pass** |
| **T-d-shift** calibration gap (≤ 0.10) | **+0.32** | +0.30; fail (0.90) | **fail** |
| **T-e** search ÷ reference with the prior, above 1.10 | **1.46 [1.24, 1.91]** | about 1.5; material (0.65) | **material** |

Registered consequences: the search is the standing time-late system and the control any
learned time-late model must beat (T-b); that standing holds when targets manoeuvre
otherwise than assumed, at these shifts (T-c); candidate probabilities may be shown as
probabilities when Annex B's statistics hold (T-d) and only with the warning that they
assume those statistics (T-d-shift); a learned full-period model is worth testing against
the search, with the shifted split as its control (T-e).

## Every system (median over periods of the period's median relative range error)

| System | Annex B | Over 10% | Shift | Over 10% |
| --- | --- | --- | --- | --- |
| C″ read as a track | 0.088 | 0.45 | 0.146 | 0.64 |
| **Search (best history)** | **0.039** | 0.26 | **0.086** | 0.46 |
| Search from C″'s transitions | 0.044 | 0.30 | 0.107 | 0.52 |
| Search from nothing | 0.048 | 0.32 | 0.106 | 0.52 |
| One leg | 0.410 | 0.84 | 0.364 | 0.88 |
| IMM as a track | no state on 60% of rows (0.364 on the rows it answers) | 0.98 | (0.314) | 0.98 |
| EKF as a track | likewise (0.390) | 0.99 | (0.343) | 0.99 |
| Reference, times held | 0.022 | 0.11 | 0.040 | 0.25 |
| Reference, times free | 0.026 | 0.13 | 0.046 | 0.27 |
| Reference, times free, with the prior | 0.026 | 0.13 | 0.046 | 0.24 |
| Truth-started fit (reported; not a reference) | 0.015 | 0.08 | 0.012 | 0.03 |

Other ratios: C″ ÷ search from nothing 1.83 [1.45, 2.22] (Annex B), 1.37 [1.18, 1.73]
(shift); search ÷ reference on the shift split 1.87 [1.57, 2.32]. Median over rows, search
against C″: course 2.5° against 7.7°, speed 0.50 kt against 1.17 kt (Annex B); 6.7° against
14.3°, 1.48 kt against 2.46 kt (shift).

Efficiency against the known-history bound over all determined rows (range, course, speed),
Annex B: C″ 3.64, 4.47, 3.74; search 1.73, 1.81, 1.74; reference times held 1.02, 0.97, 0.98;
times free 1.25, 1.30, 1.14; one leg 19.3, 26.0, 16.5.

## By how tightly the row is bounded (range efficiency; Annex B, then shift)

| System | below 0.05 | 0.05 to 0.2 | 0.2 to 0.5 | | below 0.05 | 0.05 to 0.2 | 0.2 to 0.5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rows | 19,219 | 8,579 | 825 | | 10,888 | 13,410 | 1,778 |
| Reference, times held | 1.05 | 0.93 | 1.32 | | 1.03 | 1.14 | 0.98 |
| Reference, times free | 1.35 | 0.95 | 1.51 | | 1.24 | 1.18 | 1.05 |
| Reference, with the prior | 1.42 | 0.91 | 0.82 | | 1.38 | 1.20 | 0.83 |
| Truth-started fit | 0.91 | 0.44 | 0.55 | | 0.52 | 0.23 | 0.09 |
| Search | 1.87 | 1.48 | 1.11 | | 2.60 | 2.05 | 1.17 |
| C″ | 4.26 | 2.70 | 2.69 | | 5.48 | 3.57 | 1.66 |

The search beats C″ in every band on both splits. The truth-started fit is below the bound
in every band, as diagnosed in `../20261112-gt-val/`; the neutral-start reference is not.

## Candidates (temperature 3, five candidates)

| Stated probability of the first candidate | below 0.4 | 0.4 to 0.6 | 0.6 to 0.8 | above 0.8 | all |
| --- | --- | --- | --- | --- | --- |
| Annex B: periods | 65 | 136 | 84 | 15 | 300 |
| stated | 0.34 | 0.50 | 0.69 | 0.86 | 0.53 |
| it is the true history | 0.31 | 0.51 | 0.79 | 0.87 | 0.56 |
| Shift: periods | 71 | 127 | 81 | 21 | 300 |
| stated | 0.34 | 0.49 | 0.69 | 0.86 | 0.54 |
| it is the true history | 0.11 | 0.17 | 0.32 | 0.43 | 0.21 |

True history among the first three: 0.71 (Annex B), 0.36 (shift). Brier score 0.211 and
0.263. Under the shifted statistics the probabilities still rank (0.11 rising to 0.43) but
are about half what they should be at every level.

## What this record supports

- A classical search over manoeuvre histories, using Annex B's statistics as a prior and
  nothing trained, gives a whole-period track with a median range error of 0.039 against
  0.088 for the standing causal system read as a track: 2.3 times better, interval
  [1.8, 2.7], on a fresh seed. It is also better in course and speed, and in every band of
  observability.
- It keeps most of that advantage (1.7 times) when the targets' leg lengths, turn sizes,
  turn rates and kinds are drawn from different distributions than the search assumes.
- When its assumptions hold, its first candidate is the true history 56% of the time, the
  true history is among its first three 71% of the time, and the probability it states is
  honest at every level.
- A fit told the true history (and nothing else of the truth) is 1.5 times better than the
  search. That is the room left for anything that identifies histories better.

## What it does not support

- **Any statement about real targets.** Both splits come from the same simulator; the shift
  moves four distributions by amounts we chose.
- **That the search is good in absolute terms.** A quarter of periods are over 10% in
  range on Annex B data and nearly half under the shift. C″ read as a track was never
  designed for this task, so "2.3 times better" is against a weak opponent.
- **Candidate probabilities under a wrong prior.** They are overconfident by a factor of
  about 2.5 on the shift split, and the true history is usually not among the first three.
- **That the remaining factor of 1.5 is reachable.** The reference is told the true history;
  the first registration showed that about a third of difficult periods are ambiguous given
  the bearings and the prior. T-e says a better identifier has room, not that one exists.
- **A learned model.** Nothing here was trained.

## Deviations and things a reader should know

- This is the gate's second registration. The first stopped at validation because its
  reference started at the truth (`../20261112-gt-val/`). Seed 330 showed T-b, T-c, T-d and
  the shift calibration before this registration; no threshold was changed after.
- T-d-shift was registered expecting failure.
- No naive estimator on these periods (stated in both decision records).
- The IMM and EKF give no state before the ownship's first turn in a period: 60% of scored
  rows. Their period medians are infinite by the scoring rule; they are not re-tuned.
- Validation and test ran on different CPU families (Xeon 8573C, Xeon 6975P-C); nothing is
  compared across them.
- T-a moved from 1.26 on validation to 1.05 on test; the validation pass was near the edge.

## Corrections after the panel (2026-11-12; `review.md`, five approve with findings)

**Verdict: decided by the panel, round 1.** T-a pass (a weak check); T-b pass; T-c pass,
qualified; T-d pass as registered, fragile; T-d-shift fail; T-e material as registered,
renamed. The figures above stand. These statements above are withdrawn or narrowed:

- **"2.3 times better" and "1.7 times"** are ratios of medians. Period by period the median
  ratio C″ ÷ search is 1.68 [1.49, 2.04] (Annex B) and 1.53 [1.36, 1.80] (shift). The search
  is better than C″ in 70% and 72% of periods, worse in about 30%, and more than twice as
  bad in 12% and 8%.
- **What T-b shows** is that a whole-period smoother with the arc model and Annex B's prior
  beats a causal, prior-free filter read as a track. It wins where it names the true history
  (0.032 against 0.081) and where it does not (0.057 against 0.093), so most of the gain is
  the model, the prior and the whole period, not the finding of histories. The control that
  would separate them (C″'s transitions refitted with the same model and prior) was not in
  the gate.
- **"It keeps most of that advantage" (T-c)** is withdrawn. Across three seeds the shift
  ratio is 1.70, 1.26 [0.89, 1.84] and 1.69; pooled 1.6. The shift also makes the task
  harder (3.2 manoeuvres a period against 1.9), no search with the right shifted prior was
  run, and against the reference the search degrades from 1.46 to 1.87. Supportable: at
  this shift (busier and smaller manoeuvres, same model family) the search remains better
  than C″.
- **"The probability it states is honest at every level" (T-d)** is withdrawn. It is honest
  on average and by stated-probability bin at temperature 3 and a 120 s match. It is not
  honest by period complexity (one manoeuvre: stated 0.53, right 0.77; three or more: 0.56
  against 0.40), the 0.6 to 0.8 bin is under-confident, and at a 60 s match the true history
  is in the first three in 0.57, below the 0.60 line.
- **T-d-shift's consequence** is sharpened: under a wrong prior the candidates carry a
  ranking and no probability (no temperature calibrates them). An analyst cannot tell from
  the output which regime applies, so candidates are shown as ranked alternatives until a
  prior-mismatch diagnostic exists.
- **"That is the room left" (T-e)** is withdrawn. 1.46 is the cost of not knowing the
  history: an upper limit. Period by period it is 1.17 [1.01, 1.32]; where the search names
  the true history it already matches the reference (1.01), and the whole gap sits in the
  periods where it does not (1.54), some of which are ambiguous.
- **T-a** is a weaker check than registered: on the rows it reads the faulty truth-started
  fit would also have passed (0.91). T-a's interval is 1.05 [0.91, 1.17]. It shows the bound
  and the scoring agree in the median for the generator's own model with true times; 3.1%
  of those rows are over three times the bound.
- **The truth-started fit** in the systems table is below the bound and not attainable; it
  is there to show the fault, not as a floor.
- In the by-band table, the bound does not bound systems that use a prior: the reference
  with the prior and the search may sit below 1 in loosely bounded rows without fault.
- Candidates are scored on all 300 periods; the ratios on the 277 and 267 with determined
  rows. No fielded system could select those rows: they are defined from the truth.

**What the search gets wrong** (panel, from `*.periods.json`): it under-counts manoeuvres.
Annex B: 23% of true manoeuvres missed, 93 false, the count right in 73% of periods. Shift:
41% missed, fewer than true in 67% of periods. With no true manoeuvre (12 periods) it invents
one in 58%.

**What spec 013 promised and this gate did not deliver**: the owner's bearing-rate thinning
study (FR-030, FR-031); manoeuvre counts and timing error as gate outputs (FR-011); splits
by ownship manoeuvre, position in the period and range band (FR-013); the correlated-error
variant scored beside (FR-003); uncut engagements as a stratum; a smoothed IMM line
(FR-022); held-course periods and a false-manoeuvre rate. None was run. They are owed.

Every bullet under "What this record supports" holds for σ = 1°, independent Gaussian
bearing errors, one simulator, and an arc model that is the generator's own.
