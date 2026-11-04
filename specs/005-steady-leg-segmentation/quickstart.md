# Quickstart: spec 005 validation scenarios

Prerequisites: `uv sync`, and the MAN2 validation split `data/man2-val/validation.f32pack` (seed
314, generator 0.6.0; digests in `experiments/20261104-g0-man2/dataset-digests/`). Contracts: [contracts/cli.md](contracts/cli.md).

## 1. Unit and golden tests

```bash
uv run pytest -q tests/unit/test_segment_truth.py tests/unit/test_segment_ownship.py tests/unit/test_segment_search.py tests/unit/test_segment_confirm.py tests/unit/test_segment_crf.py tests/unit/test_segment_metrics.py
```

Expected results:
- Truth labels match the generator's span rows exactly (R4).
- O agrees with `ownship_legs`.
- The CRF gradient at zero evidence matches finite differences and is non-zero (SC-003).
- The metrics give contamination 0 and gap recovered 1 for the oracle, and gap recovered 0 for
  one leg (SC-002).

## 2. C on validation

```bash
uv run tma2-segment --in data/man2-val/validation.f32pack --out data/seg/val-C.ndjson --segmenter C --params configs/segment/c-default.json --rows g5 --vessel both
```

Expected: under 10 s per scenario on a 4-core runner (SC-004), and no interval that uses a bearing
after its prefix row. A test re-runs a prefix with the later bearings removed and compares.

## 3. Scoring on validation (diagnostic)

```bash
uv run tma2-gs --truth data/man2-val/validation.f32pack --segmentations data/seg/val-C.ndjson --experiment experiments/<date>-gs-val
```

Expected:
- GLR + confirm reproduces its MAN2 reference record (`experiments/<date>-man2-refs/`, spec 006
  T033) on the same 1,000 scoring scenarios (SC-002).
- C's false-split rate is at most the declared 5%.
- Every metric appears per detectability band (SC-006).

## 4. Gap or chord (R3)

Run step 2 with `mode` set to `gap`, then to `chord`. Compare median range over G5 rows in
`metrics.json`. The lower one goes into the decision record.

## 5. L, after the decision record

```bash
uv run tma2-segtrain --plan configs/segment/l-plan.json --seed 1 --out models/segL/s1
uv run tma2-segment --in data/man2-val/validation.f32pack --out data/seg/val-L0.ndjson --segmenter L --weights <untrained>
```

Expected: an untrained L's segmentations equal C's byte for byte (SC-003).
