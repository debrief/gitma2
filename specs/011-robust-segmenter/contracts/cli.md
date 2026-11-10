# CLI contracts: spec 011

```
tma2-segment --in <split> --out <seg.ndjson.gz> --segmenter C-r --params <C params json>
             --robust <settings json> [--start N --count N --workers 4]
```
Writes C-r's segmentations in C's format with the header's `robust` block. With
`--segmenter C` nothing changes (digests asserted in tests).

```
tma2-hpredict --in <split> --kind robust --segmentation file:<seg.ndjson.gz> --plan <plan> --out <pred>
```
The Gate H robust control on the segmentation file's transitions at each scored prefix. Refuses
a file whose dataset digest is not the split's.

```
tma2-gr --truth <split> --predictions base=<pred> cr=<pred> ref=<pred> [others] --plan <gr plan>
        [--decision <dir>] --experiment <dir>
```
Writes `gate.json`, `errors.npz`, `report.md`; exit 3 when the gate is not passed (R-a fails).

Workflow `gater/**` → `.github/workflows/gater.yml`, plans under `configs/gater/`; results to
`results/gater-<plan>-<condition>-<run id>`.
