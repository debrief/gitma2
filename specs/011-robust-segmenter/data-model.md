# Data model: spec 011

## RobustConfirmSettings (schema 0.32.0)

| Field | Type | Meaning |
| --- | --- | --- |
| `huber_k` | float | Huber constant (2.0, Gate H's) |
| `reweightings` | int | IRLS passes (3) |
| `scale` | `estimated` or `stated` | second-difference estimate, or the stated σ |
| `correlation` | bool | inflate the threshold by the estimated lag-1 correlation |
| `weights` | `own` or `base` | each hypothesis's own weights, or the base's reused |
| `tau_factor` | float | multiplies C's χ² point (1.0; the reference lines use 1.5, 2.0 with no robust cost) |

## Segmentation header (existing record, new optional block)

`segmenter: "C-r"`, `segmenter_sha256` and `code_sha256` as C's (the frozen parts it runs),
`robust`: the settings above, `robust_code_sha256`: digest of `segment/robust.py` and
`headroom/gls.py`. Absent for C.

## GateRCriteria / GateRDecision

`r_a` (point limit 0.05, interval limit 0.02), `r_b_closed` (0.10), `level` (0.975), seeds,
sizes, plan digest, C's digests, C-r's settings and code digest, forecasts, at-most yield.

## Gate R record (`gate.json`)

Per condition: medians for each system (range, course, speed), share closed with interval,
remainder ratio with interval, the registered breakdowns, segmentation counts, verdict.
