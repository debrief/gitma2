# Data model: Gate 2 on MAN2

Every persisted type is defined once in `schema/tma.yaml`, generated into Pydantic and
JSON Schema (constitution I).

## EModelConfig

The configuration of E, carried in the training plan.

| Field | Meaning |
| --- | --- |
| `encoder` | width, layers, heads, feedforward, head activation (smooth), as `PhysicsModelConfig` |
| `extra_channels` | `["c_code"]`: C's per-row code at prefix k |
| `weight_bound` | bound on the per-bearing log-weight (tanh × bound) |
| `knots` | physics layer knot cap (12) |
| `evidence_network` | E-s's network (as spec 005's), or absent for E-w alone |
| `temperature` | T of the relaxed acceptance |
| `components` | `["weights"]`, `["evidence"]` or both |

## ETrainingPlan

- **Data:** the stream (seed 318, count, commit, digests), plus validation (seed 314, ordinals).
- **C:** the segmentation results branches and paths, with their parameter and code digests.
- **Models:** each with an id (`e-s1`, `e-s2`, `e-s3`, `e-shuffled`, `ew-s1` …) and a seed.
- **Training:** lr, batch, maximum epochs, patience, relative improvement, trim fraction, loss
  cap, exclusion threshold, sampled prefixes per scenario.

Its SHA-256 is bound in the decision.

## DecisionTable (npz, header record typed)

One table per scenario.

**Header:** dataset digest, C's parameter and code digests, ordinals, `git_commit`, `git_dirty`.

**Per decision:**
- row a, candidate start and length;
- source (GLR or search), drop Δ and base threshold τ′;
- the affected scored rows;
- the bound-normalised error components with and without the transition.

## Checkpoint meta

As spec 005's `CheckpointMeta`:
- epoch, best epoch, best robust validation loss;
- `weights_sha256`, `git_commit`, `git_dirty`, `cpu_model`;
- per-job records, so a chained job resumes.

## E predictions (NDJSON)

**Header:** model id, `weights_sha256`, `plan_sha256`, dataset digest, C's digests,
`git_commit`, `git_dirty`, `code_sha256`.

**Per scored row:** ordinal, k, state (x, y, vx, vy), covariance, `plausible`.

## Gate2Decision

Fields as research R7. It is committed before any E training. Amendments (the carried model,
the shuffled-rule outcome, the seed-319 digests) are separate files, listed by digest in the
gate manifest, as Gate S did.

## Gate2Record / verdict

- **Criteria:** G2-a, G2-b, G2-c and G2-d, each with point, lower and upper.
- **Outcome:** each verdict (pass, fail or inconclusive), the shuffled-rule outcome, the overall
  verdict and `decided_by`.
- **Bindings:** `metrics_sha256` and the manifest (every input's SHA-256, provenance read before
  output).

## State transitions

C is fixed, then the decision record is committed, then training runs (three seeds and a
shuffled control). On validation the carried-seed rule and the validation rule are applied, and
the amendments are committed. Then seed 319 is generated, the test is segmented and predicted,
and the gate is scored. The panel reviews it, then the write-up follows.
