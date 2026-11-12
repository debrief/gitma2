# Gate T decision record (spec 013)

`decision.json` is committed before validation seed 330 or test seed 331 is generated, and so
before any score on either. It binds the plan `configs/timelate/tl-a.json` (`6f15a246…`), the
two run configurations, the three ranges files, the search's code (`a40eb130…`, the digest
`tma2-tlsolve` writes into every shard) and the frozen C (`4d2c084f…`) by SHA-256. None of
them is edited after this; later additions are new files here. No criterion may change once a
validation result exists.

**Status:** the workflow's smoke run on the tuning seed passed at 6da75cf (run 43200187567, four
periods a split; two earlier attempts failed on the shifted ranges file and on a shell detail in
the scoring step, neither in the search's code). Every digest below was re-checked against the
files at this commit and is unchanged since the record was first committed (9ada270).
Validation is launched from this commit; it is the one that counts.

## Fixed here

- **The SRD:** §5 Gate T row as proposed on this branch (owner to merge). The criteria below
  are the row's.
- **Nothing is trained.**
- **Data:** generator 0.6.0 at 5-second bearings (`configs/timelate/tl-ranges.json`), σ = 1°
  engagements of the `train` split, one period cut at random from each
  (`timelate/periods.py`: length uniform between 20 minutes and the engagement, then the start).
  A second split, **shift**, draws targets from `tl-shift-ranges.json`: legs of mean 15 min
  (sd 5, min 5) where Annex B has 25 (sd 9, min 5); turns of 15° to 75° where it has 30° to
  120°; turn rates half as fast again; kinds 0.60 / 0.25 / 0.15 where it has 0.80 / 0.10 /
  0.10. The search keeps Annex B's prior on both. Validation: seed 330, count 450, the first
  150 periods of each split. Test: seed 331, count 900, the first 300 of each.
- **Systems, each giving the whole track:** C″ run causally to the period's end on 10-second
  points and read as a track (no fade); the evidence-scored search from two starts (C″'s
  transitions; no manoeuvres), its best history and its first five candidates
  (`timelate/search.py`; 12 steps, at most 10 manoeuvres); one leg; the IMM and EKF at their
  frozen settings read as tracks (not re-tuned for this task; no state before the ownship's
  first turn in the period); the true history fitted to the bearings alone and fitted with
  the prior (the reference; the only use of the truth).
- **Scoring:** rows 30 s apart (every sixth); a row counts where the known-history bound on
  relative range is below 0.5; a period's figure is its median relative range error over
  those rows, with a row a system does not answer counted as infinite; a system's figure is
  the median over periods. Ratios carry a 95% percentile bootstrap over periods, 2,000
  resamples.
- **The true history is "found"** by a candidate with the same number of manoeuvres whose
  mid-times, in order, are each within 2 minutes of the true ones.
- **Candidate probabilities:** evidence at temperature 3, normalised over the five
  candidates. The temperature was read off 99 tuning periods of seed 329
  (`../20261112-tl-search/histories.json`: at 1 the first candidate is given 0.80 and is right
  in 0.51; at 3, 0.52 and 0.51) and is not refitted.
- **Criteria** (`decision.json`):
  - **T-a** (soundness): range efficiency of the true history fitted to the bearings alone
    within [0.8, 1.3] on the Annex B split.
  - **T-b** (the verdict): C″ ÷ search, interval wholly above 1.10.
  - **T-c** (the prior's reach): the same on the shift split, interval wholly above 1.00.
  - **T-d** (the candidates): true history among the first three in at least 0.60 of periods,
    and the mean stated probability of the first within 0.10 of the share in which it is the
    true history.
  - **T-e** (headroom, a reading): search ÷ true history fitted with the prior; material if
    the interval is wholly above 1.10.
- **Validation rule:** T-a on seed 330 stops the gate before seed 331 is generated. T-b to
  T-e are reported on validation and cannot stop the gate.
- **The panel decides.**

## Forecasts (from tuning seed 329 only)

| Check | Forecast | Probability |
| --- | --- | --- |
| T-a | efficiency about 1.0; pass | 0.90 |
| T-b | ratio about 2.0, interval about [1.6, 2.6]; pass | 0.90 |
| T-c | ratio about 1.4; pass | 0.55 |
| T-d | in the first three about 0.70; gap within 0.10; pass | 0.50 |
| T-e | ratio about 2.2; material | 0.90 |

## What the tuning seed has already shown

On 99 fresh tuning periods the search was at 0.042 against C″'s 0.088 (2.12 [1.62, 2.96]),
so T-b is expected to pass. That is disclosed: the threshold follows the owner's 10% level,
the settings were committed before that run and not tuned on it, and the validation and test
seeds are untouched. The shift split and the candidate checks have never been run.

## Known weaknesses, stated before the result

- **C″ is a weak opponent for this task.** It is the standing causal system read as a track,
  not a system designed to give one. Passing T-b shows the search is better than what we
  had, not that it is good.
- **The prior is the simulator's own.** T-c is the only check on that, and it shifts four
  quantities by amounts we chose; it is one point on a surface.
- **The reference with the prior is biased** (its efficiency on tuning data is below 1), so
  T-e compares two prior-informed estimators and says nothing about the bound.
- **The temperature comes from one tuning seed** and may not transfer; T-d may fail for that
  reason alone, in which case the probabilities are simply not offered.
- **"Found within 2 minutes"** is loose; the range error is sensitive to timing inside it.
- **The evidence is Laplace's approximation.** A first version of it produced a wrong
  conclusion on 12 November (`../20261112-tl-prior/`); it is checked here only by its results.
- **No naive estimator** on these periods: the project's naive predictor is fitted to
  10-second real-time rows and has no meaning for a track. This departs from the rule that
  every result carries the naive line; one leg stands in as the uninformed reference.
- The IMM and EKF are not re-tuned and are silent before the ownship's first turn, so their
  period medians will often be infinite; their error on the rows they answer is reported.
- σ = 1° only; clean Gaussian bearing errors; one cut per engagement.
- A C″ segmentation depends on its chunk (16 periods padded together), so a shard's C″ and the
  search started from it are reproduced only with the run's shards.
