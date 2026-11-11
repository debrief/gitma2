# Spec 011 pilot: C-r's settings (plan research R4)

Tuning seed 323, the first 60 σ = 1° engagements (237 scored rows), primary condition (all four
mismatches, central) and no mismatch. CI run 42918535867 (`headroom/gr-pilot`, code fea9a01; a
first launch failed on a plan bug, an empty settings object dropped by the workflow). Every
system has the Gate H robust control in its final solve and C″'s zig veto and fade; they differ
only in the confirmation test. `summary.json` from `scripts/research/gr_pilot.py` (paired,
scenario-clustered, 95%). **Not a gate result, and too small to separate the settings.**

| Confirmation test | Primary: median range error | Gain over the baseline | Share of the gap closed | Clean | Clean cost |
| --- | --- | --- | --- | --- | --- |
| True manoeuvre times (the reference) | 0.099 | | 1 | 0.055 | |
| C″ as frozen (the baseline) | 0.298 | | 0 | 0.144 | |
| C-r, Huber 2.0 | 0.248 | +0.050 [−0.007, +0.127] | 0.25 [−0.05, +0.50] | 0.127 | −12% [−23, +4] |
| C-r, Huber 1.345 | 0.245 | +0.053 [−0.010, +0.142] | 0.27 [−0.07, +0.55] | 0.122 | −16% [−27, +13] |
| C-r, Huber 2.0, estimated scale | 0.265 | +0.033 [−0.019, +0.120] | 0.17 [−0.13, +0.42] | 0.127 | −12% [−25, +13] |
| Plain C, threshold × 1.5 | 0.278 | +0.020 [−0.051, +0.110] | 0.10 [−0.31, +0.42] | 0.133 | −8% [−23, +14] |
| Plain C, threshold × 2 | 0.247 | +0.050 [−0.025, +0.147] | 0.25 [−0.16, +0.53] | 0.133 | −8% [−23, +14] |

Run time per engagement on one shard (primary): C″ 41 s, C-r 78–85 s, plain C at a raised
threshold 39 s.

## What this supports

1. Every variant's point estimate is better than the baseline on both conditions, and **no
   interval excludes zero**. At 60 engagements nothing is shown.
2. **The robust test is not shown to beat simply raising C's threshold**: Huber 2.0 and plain C
   at twice the threshold both read 0.25 of the gap. The project's standing lesson (Gate 2
   panel) applies: a design must beat the trivial rule it might be.
3. On clean data every variant reads *better* than the frozen C, not worse. That is consistent
   with the diagnosis (C declares 248 unmatched transitions on clean data) and suggests C's
   threshold is low for MAN2 in general; untested beyond these 60.
4. The estimated scale is no better than the stated σ (0.265 against 0.248): by R4 it is fixed
   at the stated σ, the cheaper value.
5. The point estimates (0.25) are well short of the 0.63 that C's clean-data segmentation would
   close (`../20261110-gr-diagnosis/`).

## Next (declared before its data)

The 150 engagements of the diagnosis, with segmentations dumped so that false transitions and
misses are counted for every variant: the baseline, Huber 2.0, Huber 1.345, plain C at × 2 and
× 3, and Huber 2.0 with the threshold × 2 (a combination the pilot suggests; added after the
pilot, on the tuning seed, recorded here). R4's rule then picks: lowest primary error among
those within 2% of the baseline on clean data, ties to the cheaper, and a robust variant is
carried only if it beats the best plain threshold with an interval that excludes zero;
otherwise C-r is plain C at the chosen threshold and the write-up says so.
