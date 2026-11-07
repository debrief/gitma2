# C after the Gate S panel's fixes, on validation: the open-transition hand-over (spec 007 T001)

C with the fixes of PR 16 (monotone cost tables, no overlap through open transitions; code digest
6c2eba38…, segmentation at 0f606c3 on CI, `results/segment-c3-val-42228602685`; parameters as
Gate S, digest 60e6ee63…), scored on seed 314 validation ordinals 500–1499 (3,934 σ = 1° G5
rows) with each open-transition hand-over, on CI (`score.yml` run 42238225577 at 46392c2,
`results/score-c3-val-42238225577`, CPU AMD EPYC 9V45). 97.5% scenario-clustered intervals.

| Hand-over | Median range (all G5) | Gap recovered | Open at k (210 rows): gap recovered | Gross (range > 50%) |
| --- | --- | --- | --- | --- |
| `knot_at_k` (spec 005) | 0.120299 | 0.8907 [0.8706, 0.9097] | **0.695** (median 0.203) | 11.5% |
| `start_masked` | 0.120299 | 0.8907 [0.8706, 0.9107] | 0.653 (0.219) | 11.6% |
| `start_chord` | 0.120358 | 0.8905 [0.8698, 0.9089] | 0.680 (0.208) | 11.5% |

Paired differences in gap recovered between the three are all within ±0.004 (e.g. knot_at_k −
start_chord +0.0001 [−0.0025, +0.0038]).

**Choice: `knot_at_k`.** The rule (spec 007 FR-002) is the lowest median range error over G5
rows; `knot_at_k` and `start_masked` tie exactly (0.12029864977502473), so the tie is broken on
the open-at-k rows the convention exists for, where `knot_at_k` recovers the most (0.695). It is
spec 005's default, so C's parameter digest is unchanged (the parameter stays absent).

**C's re-validated figures** (FR-003), with the fixes and `knot_at_k`:
- gap recovered 0.891 [0.871, 0.910], as Gate S's validation (0.891); the fixes did not move the
  headline;
- S2 on validation, C − GLR + confirm: +0.632 [+0.559, +0.733] (Gate S: +0.632);
- rows open at k: 210 (5.3%), gap recovered 0.695 against 0.897 elsewhere — the lever Gate 2's E
  is meant to act on;
- gross rows: no estimate 0.6%, range over 50% 11.5%; efficiency 2.78 × the known-manoeuvres
  bound in range.

Files: `metrics.json`, `report.md`, `plan.json`, `run.json`, `inputs.json` from the CI run
(`errors.npz` on the results branch).
