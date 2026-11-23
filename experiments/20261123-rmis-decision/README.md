# Spec 037 decision record: the regressor under mismatch (written before the three fine-tunes)

A registered study, not a gate. Nothing here is edited after the first of the three GPU runs
starts; later choices that the protocol leaves open (interval scales, the temperature control's
widths, the hybrid's settings) are bound by a dated addendum in this folder before the test
scoring.

## What is bound (`digests.json`, made by `scripts/research/rmis_digests.py`)

- `configs/rmis/protocol.json` `beb6af49…`: seeds, sizes, conditions, systems, the statistic,
  the readings M1–M5, Y1, Y2 and their thresholds, what validation may be used for.
- The fine-tune plans `configs/regress/ft-s1..s3.json` (`2d9bccd0…`, `de78d5af…`, `e99209aa…`),
  the mix `ft-mix.json` (`c8ac3601…`), the held-out conditions (`b0bb69e3…`), Gate H's
  conditions and plan (C″'s frozen parameters and the robust solve's settings).
- Code `e8e2fc5d…` over the listed files (overlay, stream, model, training, prediction,
  intervals, readings).

## Readings (test seed 371, 1,000 engagements a condition, scored once)

Each is a paired per-engagement ratio of range error with an engagement bootstrap; "better" if
the interval is wholly above 1, "worse" if wholly below, otherwise "not separated"; three seeds
pooled, and each alone beside.

| | Ratio | Condition | Note |
|---|---|---|---|
| M1 | C″-robust ÷ fine-tuned | all-central | in the training ranges: not a mismatch for the model |
| M2 | C″-robust ÷ fine-tuned | ho-both | kinds never drawn in training or tuning |
| M3 | unchanged ÷ fine-tuned | all-central, ho-both | the fine-tune's own effect |
| M4 | unchanged ÷ fine-tuned | off | "no cost" if the lower limit is at least 0.95 |
| M5 | coverage of the stated 95% intervals in [0.90, 0.99] per quantity on off, all-central, ho-both; interval score ÷ the temperature control's wholly below 1 | | scales fitted on validation's off and all-central rows only |
| Y1 | C″-robust ÷ hybrid | off, all-central | fall-back rows are constructed ties, excluded and counted |
| Y2 | fine-tuned ÷ hybrid | off, all-central | |

Harm (hybrid): range, course or speed wholly below 1 against C″-robust on clean data.
Reported beside every reading: course and speed, efficiency, the median ratio and the shares
better, twice as good and twice as bad, by range third, counts, each seed alone.

## What the readings can and cannot show

- M1 inside the training ranges is "robust to this simulated error family". Only M2 speaks to
  errors the model was not shown, and its kinds are still a simulator's.
- The regressor knows the simulator's manoeuvre statistics; C″ is not told them. A win over C″
  is a win of a prior-informed estimator, as spec 012's panel put it.
- The robust solve on the true segmentation is told the manoeuvre times: a reference, not a
  ceiling, and not a comparator in any reading.
- 1,000 engagements: a ratio within about 5% of 1 will read "not separated".
- The detectable size for M4: a cost under about 5% cannot be told from none.

## Forecasts (written 2026-11-23, before any fine-tuned seed exists)

Basis: step 1 on spent seed 321 (unchanged regressors, 300 engagements) and one pilot of 4,000
updates read on monitors of 384 to 512 scenarios. One pilot is one draw.

| | Forecast | Basis |
|---|---|---|
| M1 | better, 1.5 to 2.2 | unchanged already 1.18; the pilot halved the all-central monitor error |
| M2 | better, 1.2 to 1.9; low confidence | the pilot recovers ho-both on its monitor; C″ under ho-both has never been scored |
| M3 | better on both, 1.4 to 2.0 and 1.3 to 1.9 | pilot monitors |
| M4 | **a cost**: ratio 0.92 to 0.98, lower limit under 0.95 | the pilot lost 7% on clean data |
| M5 | range honest on clean and primary, not on held-out; course and speed uncertain; head better than the temperature | unchanged head covers 0.947 on clean data unfitted and 0.77 under the primary condition |
| Y1 | better on all-central, 1.2 to 1.6; clean 1.2 to 1.5 | the regressor's lead over C″ in range |
| Y2 | below 1 in range (the hybrid is worse than the regressor alone), level or better in course | spec 012's range-prior control did not carry the margin |

## Budget

Ledger at registration: $40.89 (`ledger.txt`; the pilot was $0.31). Each seed's plan may use at
most $2.27; three take the total to at most $47.70 against the $49 guard and the owner's $50.

## Not registered here

The hybrid's code does not exist yet; it is written while the seeds train and its settings are
chosen on validation (addendum). The temperature control and the interval score are likewise
written before validation is read. The test plan names the fine-tuned checkpoints by digest once
they exist.
