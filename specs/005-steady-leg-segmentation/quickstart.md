# Quickstart: spec 005 validation scenarios

Prerequisites:
- `uv sync`;
- the MAN2 validation split `data/man2-val/validation.f32pack` (seed 314, generator 0.6.0, made at
  d72cb81; digests in `experiments/20261104-g0-man2/dataset-digests/`).

Contracts: [contracts/cli.md](contracts/cli.md). Full-size runs go to CI (section 6); the commands
below are local, on small slices (checked on 2–3 scenarios each). `tma2-segment` refuses an
uncommitted tree: pass `--allow-dirty` for local experiments, never for a gate input.

## 1. Unit and golden tests

```bash
uv run pytest -q tests/unit/test_segment_foundations.py tests/unit/test_segment_ownship.py tests/unit/test_segment_search.py tests/unit/test_segment_c.py tests/unit/test_segment_crf.py tests/unit/test_segment_score.py tests/unit/test_segment_l.py tests/unit/test_segtrain.py tests/unit/test_gs_gate.py
```

Expected results:
- Truth labels match the generator's span rows exactly (R4).
- O agrees with `ownship_legs`.
- log Z equals brute-force enumeration, and the CRF gradient at zero evidence matches finite
  differences and is non-zero (SC-003).
- An untrained L reproduces C byte for byte, and the exported form of the evidence network
  equals the network.
- The metrics give contamination 0 and gap recovered 1 for the oracle, and gap recovered 0 for
  one leg (SC-002).
- The gate's pass, fail and inconclusive logic and its refusals hold.

## 2. C on validation

The decision's parameters are in `configs/segment/gs-plan.json` (`segmenter.parameters`). Write
them to a file and run C on a slice of the scoring ordinals (500–1499):

```bash
uv run python -c "import json; json.dump(json.load(open('configs/segment/gs-plan.json'))['segmenter']['parameters'], open('/tmp/c-params.json', 'w'))"
```

```bash
uv run tma2-segment --in data/man2-val/validation.f32pack --out data/seg/val-C.ndjson --segmenter C --params /tmp/c-params.json --start 500 --count 20 --rows g5 --workers 4
```

Expected: about 10 s per scenario on a 4-core runner (SC-004). A test re-runs a prefix with the
later bearings removed and compares, so no interval uses a bearing after its prefix row.

## 3. Scoring on validation (diagnostic)

```bash
uv run tma2-gs --truth data/man2-val/validation.f32pack --start 500 --count 20 --segmentations C=data/seg/val-C.ndjson --imm imm-cv0.03-ct1-w0.01-s0.0003-p4-r2 --ekf ekf-sa0.00003-p4-r0.03125 --detectability --experiment /tmp/gs-val-smoke
```

Add `--glr-confirm <dir>:glr-q0.2-t13.8` to score GLR + confirm from its confirm files (section 6).
On the full 1,000 scoring scenarios, expect:
- GLR + confirm reproduces its MAN2 reference record (`experiments/20261104-man2-refs/`) (SC-002);
- every measure appears per detectability band (SC-006).

The committed full run is `experiments/20261104-gs-val/`.

## 4. Gap or chord (R3)

Score the same segmentations in both hand-over modes with `--modes gap chord`. Compare median
range over G5 rows in `metrics.json`; the lower one goes into the decision record (gap was chosen).

## 5. L, after the decision record

Build the training tables, then train one seed for one epoch on a small slice:

```bash
uv run tma2-segtrain tables --in data/man2-val/validation.f32pack --plan configs/segment/gs-plan.json --start 0 --count 20 --sigma1 --out /tmp/segL/val.npz --workers 4
```

```bash
uv run tma2-segtrain train --plan configs/segment/gs-plan.json --model segL-s1 --train /tmp/segL/val.npz --val /tmp/segL/val.npz --checkpoint /tmp/segL/ck --epochs 1
```

Then run L with its weights; the plan names the evidence network's configuration:

```bash
uv run tma2-segment --in data/man2-val/validation.f32pack --out data/seg/val-L.ndjson --segmenter L --weights /tmp/segL/ck/best.safetensors --plan configs/segment/gs-plan.json --params /tmp/c-params.json --start 500 --count 20 --rows g5 --workers 4
```

Expected: `tma2-segtrain train` refuses tables built under other segmenter parameters. With
untrained weights, L's segmentations equal C's (tested in `test_segment_l.py`).

## 6. Full runs on CI

- **Segmentations:** push `segment/<name>` with a plan `configs/segment/<name>.json` (data block,
  ordinals, shards, `params_from` or `set`, and `weights` for L). `.github/workflows/segment.yml`
  regenerates the split at its commit, checks the digest and pushes the merged NDJSON to a results
  branch.
- **GLR + confirm:** push `glr-confirm/<name>` (`.github/workflows/glr-confirm.yml`).
- **L training:** push `segtrain/<name>` (`.github/workflows/segtrain.yml`).

## 7. The gate

```bash
uv run tma2-gs --truth data/gs-test/test.f32pack --start 0 --count 5059 --segmentations C=<C.ndjson> L=<L.ndjson> --glr-confirm <dir>:glr-q0.2-t13.8 --imm imm-cv0.03-ct1-w0.01-s0.0003-p4-r2 --ekf ekf-sa0.00003-p4-r0.03125 --detectability --decision experiments/20261104-gs-decision/decision.json --plan configs/segment/gs-plan.json --split test --experiment experiments/<date>-gs
```

It refuses a mismatched decision, plan, data digest, segmenter digest or carried weights, and a
segmentation from a dirty tree. It writes `verdict.json` and `manifest.json`, and exits 3 unless
S1–S4 all pass. It takes about 1.5 h on 4 cores.
