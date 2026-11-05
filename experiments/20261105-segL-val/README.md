# L on validation: the three seeds and the shuffled control (spec 005 T036)

Training run 41923847724 (`segtrain/gs-a` at 4abab2a, `results/segL-41923847724`). The models
were scored by `tma2-gs --modes gap` on seed 314's 1,000 scoring ordinals (500–1499, 3,934 G5
rows), beside C and the references. These are the rows of `experiments/20261104-gs-val/c-final/`.

Each L segmentation came from `segment.yml` (`configs/segment/segL-val-*.json`) at a clean
commit (65b6bbf), with the decision's parameters. Each file's segmenter digest binds its
weights (`segment/gate.py: expected_l_sha`).

## Training

| Model | Epochs (best) | Validation CRF loss, untrained → best | Seconds per epoch |
| --- | --- | --- | --- |
| untrained (zero evidence) | — | 55.580 | — |
| segL-s1 | 4 (1) | 55.185 | 1,060–1,064 |
| segL-s2 | 15 (12) | 54.794 | 1,053–1,173 |
| segL-s3 | 5 (2) | 55.167 | 1,051–1,098 |
| segL-shuffled | 7 (4) | 55.268 | 1,074–1,131 |

The loss is in nats per prefix, over tuning ordinals 0–499. The untrained figure was measured
locally on tables rebuilt at 65b6bbf; the trained models' losses reproduce CI's to the last
digit.

**Throughput (T033):** about 18 min per epoch over 10,000 scenarios on one runner thread, against
the 1 h budget.

**Early stopping:** a relative minimum improvement of 1e-3 (0.055 nats) ended s1 after epoch 4
and s3 after epoch 5, while their losses were still falling slowly.

**The learning is small, and much of it does not depend on the labels.**
- The best seed improves the loss by 0.79 nats per prefix, 1.4%.
- The shuffled control, trained on another scenario's labels, improves it by 0.31.
- Most of the gain is therefore a label-independent bias, most likely a prior on steady against
  transition.
- Only s2 has a clear label-specific part, about 0.5 nats beyond the control.

**Provenance caveat.** Every training job recorded `git_dirty: true`. The workflow downloaded
the tables into `tables/` and wrote checkpoints to `ck/` inside the checkout. The code was clean
at 4abab2a. Both directories now live in `RUNNER_TEMP` (65b6bbf). The weights are bound by
SHA-256 in each `meta.json` and in the decision's `carried.json`.

## Downstream on validation

Median relative range error; gap recovered in range from one leg (0) to the oracle (1). Intervals
are 97.5%, scenario-clustered, 2,000 resamples, paired against C.

| Segmenter | Range | Gap recovered (range) | Minus C |
| --- | --- | --- | --- |
| C (gap) | 0.120 | 0.891 [0.871, 0.911] | — |
| segL-s1 | 0.122 | 0.887 [0.866, 0.905] | −0.0045 [−0.0143, 0.0039] |
| segL-s2 | 0.120 | 0.891 [0.870, 0.911] | −0.0003 [−0.0099, 0.0086] |
| segL-s3 | 0.122 | 0.888 [0.867, 0.908] | −0.0036 [−0.0128, 0.0054] |
| segL-shuffled | 0.121 | 0.889 [0.869, 0.908] | −0.0020 [−0.0093, 0.0047] |
| GLR + confirm | 0.447 | 0.259 [0.157, 0.333] | −0.632 |

Each L changes C's segmentation on 37–39% of prefixes; the control changes it on 27%. L adds
1–2% more transitions. Contamination P90 is 0.267–0.278 against C's 0.272. The false-split rate
is 2 of 24 change-free prefixes for every segmenter.

## Rules (decision record)

- **Carried rule:** the median of the three seeds by gap recovered in range. The seeds score
  s1 0.8868, s3 0.8877 and s2 0.8910, so **segL-s3** is carried. Its weights are
  `models/segL-s3/best.safetensors`, SHA-256 `1b243020…`, frozen in
  `experiments/20261104-gs-decision/carried.json`.
- **Shuffled rule:** the control minus C is −0.0020 [−0.0093, 0.0047]. The interval includes
  zero, so the rule **passes**: the control does not beat C.

## Reading

**On validation, learning is not shown.** No seed beats C: every point is at or below C, and every
interval includes zero. The forecast in the decision record was L − C ≈ +0.01
[−0.01, +0.03], most likely inconclusive. The validation result is lower: about −0.003, with
intervals of ±0.01. On test, S4 is therefore most likely inconclusive or a fail.

The decision record has no rule that stops at validation, so Gate S is scored on seed 315 as
pre-registered.

**Two causes are plausible (not tested here):**
1. **Little headroom.** C already recovers 0.89 of the gap. The remaining 0.11 lies mostly in
   changes the bearings barely show, the low-detectability bands.
2. **The objective and the mechanism do not match.** The CRF trains the evidence through the
   additive search's lattice. C's accepted transitions come mostly from GLR nominations confirmed
   by the coupled cost, and there the evidence only shifts a capped threshold.

Files:
- `metrics.json`, `report.md`: from `tma2-gs`. The per-row `errors.npz` is not committed.
- `models/`: each model's `meta.json`, `train.log` and `best.safetensors`, and the tables'
  digests.

**The carried model's export (T035):** `python -m tma2.segment.evidence_export --weights
models/segL-s3/best.safetensors`. ONNX SHA-256 begins `24cb8bdd`. The Python and WASM legs agree
with torch to 2.8e-16; WASM takes 85 ms for four 720-row windows. Seeded weights pass all three
legs in CI.
