# G0-MAN2, run r0 (machine fail, superseded)

`tma2-g0-man2` at commit `64a2d6f`. Machine verdict **fail** on four checks, both causes errors in
the gate's own code, not in generator 0.6.0:

- `generator-iter1-seed1`, `generator-iter4-seed777`, `generator-phase4-seed777`: P0's
  `check_generator` did not pass the fixture's `generator_version` (0.5.0), so the regenerated
  headers named 0.6.0 and every file's digest differed. Spec 006 added
  `GenerateOptions.generator_version` and the conformance test passed it; P0's check did not.
  Fixed in r1 (and in `tma2-p0`, which had the same fault since PR 13).
- `throughput`: 8,245 scenarios/s, timed as a one-thread Python loop over `run_kernel`. The
  pre-registered "measured: 30,000" came from `features.batch.generate_indices` (the on-the-fly
  training path, a numba `prange` on four threads). r1 times that path for the gate and reports
  the one-thread loop beside it. Disclosed to the panel as a change of measurement after a result.

Every other check passed, including `noise-free-zig-leg` under the owner's amendment to its
coverage limit (`specs/006-generator-man2/g0-checks.md`). The record of decision is
`experiments/20261104-g0-man2-r1/`. `dataset-digests/` (seeds 314 and 316) stays here.
