# Data model: Steady-leg segmentation and Gate S

Every persisted type is defined once in `schema/tma.yaml` (constitution I) and generated into
`tma2.types`. Rows are sample indices of the scenario, and times are seconds from the scenario's
start.

## SegmentInterval

| Field | Type | Rule |
| --- | --- | --- |
| kind | enum `steady`, `transition`, `unknown` | — |
| start_index | int | ≥ 0 |
| end_index | int | ≥ start_index; inclusive |
| open | bool | true only for the last interval, when a transition is still in progress at the prefix end |

## Segmentation

One record per vessel, scenario and prefix.

| Field | Type | Rule |
| --- | --- | --- |
| scenario_index | int | the generator's scenario index |
| vessel | enum `ownship`, `target` | — |
| prefix_row | int | k: only bearings at rows ≤ k were used |
| intervals | SegmentInterval[] | tile [0, k] exactly, in order, no overlap; steady ≥ L_min rows unless unknown; transition ≥ T_min rows unless open |
| cost | float | the physics-layer cost of the accepted segmentation on [0, k] |
| margin | float | the smallest cost drop among accepted transitions, minus its threshold; null for O |
| segmenter | string | e.g. `C`, `L-s2`, `oracle`, `one-leg`, `glr-confirm` |
| segmenter_sha256 | string | the configuration digest (C) or the weights digest (L) |
| parameters | SegmentParameters | — |

## SegmentParameters

These are fixed for a run and copied into each record header, not repeated per row. Defaults
follow Annex B (4 Nov 2026) and the MAN2 re-plan; the 0.5.0 research (R1–R2) used 2°, 12-row legs
and 3-row transitions.

| Field | Type | Default |
| --- | --- | --- |
| course_tol_deg | float | 5.0 (C, Annex B) |
| speed_tol_kt | float | 0.5 (S) |
| course_change_deg | float | 10.0 (D) |
| speed_change_kt | float | 1.0 (D_S) |
| l_min_rows | int | 30 (L_min = 5 min) |
| t_min_rows | int | 6 (T_min = 1 min) |
| t_lengths_rows | int[] | initially [6, 9, 12, 18, 24, 36]; final from the MAN2 re-measurement (tasks T010) |
| search_penalty | float | set by the decision record |
| nominator_far | float | 0.2 |
| retest_rows | int | 6 |
| tau | float | 13.8 |
| mode | enum `gap`, `chord` | set by the decision record |

## TruthLabels

| Field | Type | Rule |
| --- | --- | --- |
| scenario_index | int | — |
| vessel | enum | — |
| labels | enum[] per row | `steady`, `transition`, `unknown`, from R4's function |
| parameters | SegmentParameters subset | the tolerances used |

These are recomputed from the stored true tracks and never hand-edited. A golden test pins them on
fixture scenarios.

## GateSDecision (decision record)

See [contracts/decision-record.md](contracts/decision-record.md). Fields:
- the plan, and the seeds with their digests;
- SegmentParameters, final;
- the S1 limit (contamination P90), and the S3 limits (contamination, false split);
- the carried-seed rule, and the shuffled-control rule;
- the S2 reference outcome on validation;
- the forecast;
- amendments, listed by digest.

## GateSRecord

| Field | Type |
| --- | --- |
| decision_sha256 | string |
| split, seed, digest | string, int, string |
| per segmenter | contamination (median, P90), coverage, false-split rate, leg-count accuracy, boundary error ± 60 s and ± 3 min, gap recovered (range, velocity), downstream medians (range, course, speed; all and settled), gross rates, efficiency; each overall and per stratum, with 97.5% intervals |
| differences | C − GLR + confirm, and L − reference, gap recovered with intervals |
| verdicts | S1–S4: pass, fail or inconclusive |
| decided_by | panel round |

## State transitions

- **Segmenter C:** configured → validated (decision record fixes its parameters) → frozen, with
  its digest in the record.
- **L:** untrained (equal to C) → trained (three seeds) → carried (median seed by rule) → frozen.
- **Gate S:** pre-registered → scored → panel rounds → verdict.
