# Implementation Plan: A robust classical segmenter (Gate R)

**Branch**: `011-robust-segmenter` (developed on `claude/keen-wozniak-77td7j`) |
**Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-robust-segmenter/spec.md`; the diagnosis record
`experiments/20261110-gr-diagnosis/`.

## Summary

Nothing is trained. The diagnosis (tuning seed 323) shows that outliers, and to a lesser degree
correlated error, make the frozen C declare false transitions (248 clean, 1,126 under all four);
misses do not rise, and true nominations do not help. The false transitions enter at
confirmation. C-r is therefore C with its confirmation test made robust (research R2): each
hypothesis is fitted by Huber-weighted least squares, the test compares Huber costs on a scale
estimated without reference to either hypothesis, and the threshold is corrected for the Huber
loss and, if the pilot keeps it, for correlation. C's nominators, parameters and frozen files
are untouched (R1). Gate R measures the share of the gap between C's segmentation and the true
manoeuvre times that C-r closes, every system with the robust control in its final solve (R5),
on validation seed 324 and test seed 325.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: NumPy, numba, PyTorch 2.x (physics layer, double); nothing new.

**Storage**: f32pack splits with the mismatch side file; segmentation NDJSON (gzip); prediction
NDJSON; `errors.npz`; results branches.

**Testing**: `pytest` (C's digests unchanged; C-r with weights of one and the plain scale equals
C; causality by prefix truncation), `ruff`, `mypy --strict`.

**Target Platform**: CI runners (`gater/**`); the session for seconds-long steps only.

**Project Type**: research library and CLIs.

**Performance Goals**: C-r under 4 times C's clean cost per engagement (C: about 16 s clean,
75 s under outliers on one core); the primary test condition in one CI run under 6 h in 20 shards.

**Constraints**: C's `code_sha256` (`4d2c084f…`) and parameter digest (`60e6ee63…`) unchanged;
C-r causal; no estimator reads the mismatch truth; comparisons within one scoring run and the
same chunks (16, padded to the longest); one long CI run at a time.

**Scale/Scope**: tuning seed 323 (150 engagements, as the diagnosis; pilot on 60); validation
324: primary 500, off 300; test 325: primary 2,000, off 500, outliers and correlated alone 300
each, bias and σ alone 150 each (the diagnosis found no effect; smallest size that would show
one of the size of outliers').

## Constitution Check

- **I. Types once (LinkML)**: `RobustConfirmSettings`, the segmentation header's `robust` block,
  `GateRCriteria` and `GateRDecision` go into `schema/tma.yaml` (0.32.0). Pass.
- **II. Determinism**: no randomness in C-r; seeds fresh (323, 324, 325); plan and decision
  bound by digest. Pass.
- **III. Physics does the numerics**: every scored estimate is the declared piecewise-CV solve
  with the Gate H robust control; C-r changes which knots it is given. Pass.
- **IV. Honest measurement**: one leg, the re-tuned IMM and EKF, C″ with the plain solve, the
  true-segmentation reference and the bound on the same rows; settings from the tuning seed by a
  rule declared before the search. Three seeds per carried configuration: not applicable
  (nothing trained). Pass.
- **V. Fail fast through gates**: Gate R pre-registered (SRD row, owner merges; decision record
  before seeds 324 and 325 exist), soundness on validation, the panel. Pass.
- **VI. Portable artefact**: no model carried. Not applicable.
- **Classification**: the mismatch grid is spec 010's declared design grid. Pass.

## Project Structure

```
specs/011-robust-segmenter/     spec, plan, research, data-model, contracts/cli.md, quickstart, tasks
schema/tma.yaml                 RobustConfirmSettings, header block, GateRCriteria, GateRDecision
src/tma2/segment/robust.py      C-r: hypothesis-free scale, Huber-cost confirmation driver, segment_robust
src/tma2/headroom/gls.py        (existing) the weighted layer subclass C-r's fits use
src/tma2/segment/gate_r.py      share closed, R-a, R-b, registered breakdowns
src/tma2/cli/segment.py         --segmenter C-r --robust <json> (cli is outside C's code digest)
src/tma2/cli/hpredict.py        --segmentation file:<segmentation.ndjson.gz>
src/tma2/cli/gr.py              tma2-gr: score and gate
configs/gater/                  gr-draft.json (tuning), gr-a.json (bound by the decision), run plans
.github/workflows/gater.yml     generate → segment (C, C-r; shards) → final solves → score
experiments/                    diagnosis (done), pilot, decision, validation, test
```

## Phases

1. **Finish the diagnosis** (FR-002, FR-003): `hpredict --segmentation file:`; on seed 323 the
   robust final solve on C's own segmentation, on C's clean-data segmentation applied to the
   mismatched bearings, and on the truth; which confirmation decisions over-accept (by source,
   open or closed, drop against threshold; from `Confirmed.decisions`).
2. **C-r and its pilot** (R2–R4): build `segment/robust.py`; pilot on 60 engagements of seed
   323, primary and off; drop settings with no effect; fix the rest by the declared rule.
3. **Register Gate R** (R5): SRD §5 row (owner merges), plan `gr-a.json`, decision record with
   forecasts and the at-most yield.
4. **Validation** (seed 324): R-a soundness; then **test** (seed 325) once; panel; write-up;
   slides post.

## Complexity Tracking

None: no constitution deviation.
