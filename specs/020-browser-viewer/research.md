# Research: the browser viewer

## R1 Which artefact runs in the browser

Decision: E-w's graph (`gate2.export`) with the carried weights
`experiments/20261107-g2-val/models/ew-s3/best.safetensors`. It is exported exactly as CI's
conformance step exports it, with no calibration head.

Rationale: E is the carried model (Gate 2). Its learned parts are E-s, an evidence network
whose output feeds C's confirmation, and E-w, which gives weights and a start correction into
the physics layer and produces the estimate. Only E-w's graph gives a number the page can
show. C and the confirmation are host code (spec 007 T033 says so).

Alternatives:
- Also running E-s's graph. Its output cannot be used without C in JavaScript, and CI
  already checks it.
- The Gate 3 calibrated export (`--calibration`). It is not carried: Gate 3 stopped, and its
  head has seeded weights in CI.

## R2 Which engagements

Decision: from seed 319's test split, the σ = 1° scenarios in ordinal order. Engagements
whose G5 rows are not all present are skipped: those have no usable zig leg, or E has no
answer at a G5 row. Classify by the number of target manoeuvres inside the window (the
generator's table):
- quiet (0);
- one manoeuvre (1);
- busy (3 or more).

Take the first of each class. Then take the first remaining engagement in which E's median
range error over its scored rows is worse than C″'s. Then fill to six with the next one of
each class in turn (one, busy). The rule runs over at most the first 200 σ = 1° ordinals.
If a class is empty there, the page says so; the rule is not widened silently.

Rationale: a fixed rule, not by eye (constitution IV; spec FR-002). An engagement where E
loses to C″ stops the demo from reading as an advertisement.

## R3 Data layout

Decision: per engagement, one gzipped JSON file holds:
- the truth;
- the ownship;
- the scored rows' times;
- the comparison estimates;
- the shared input arrays.

Beside it, one gzipped binary file holds the per-row arrays, each row being the graph's 12
inputs for a batch of one, with the Python outputs.

The builder records, for each input, whether it varies across an engagement's rows, and
stores it once if not. All binary data are little-endian float64, and gzip uses `mtime=0`.

To be measured in the builder and recorded in the record: which arrays vary. The first
guess is that `bearing`, `own`, `t` and `sigma` do not; `valid` may vary, if the hand-over
masks transition bearings by clearing `valid`.

## R4 The runtime on the site

Decision: add onnxruntime-web 1.31.1 as a site dependency. The prebuild copies
`ort.wasm.min.js` and `ort-wasm-simd-threaded.wasm` into `site/static/ort/`, which is
gitignored and generated at build. The runtime runs single-threaded: GitHub Pages cannot
send the cross-origin isolation headers that threads need.

Rationale: the same version as the conformance legs, which is a gotcha in AGENTS.md (keep
onnxruntime versions aligned). The page works offline, and no CDN pin to track.

Alternative: jsdelivr pinned at 1.31.1, which would keep 15 MB out of the site build. It is
rejected so the site does not depend on an outside host at view time.

## R5 Comparisons

Decision: these are precomputed with the project's code at the builder's commit, using the
same functions the Gate 2 scorer uses:
- **one leg**: the physics layer on the zig leg (`segment.score.one_leg`), the "plain batch
  least squares" of SRD §5;
- **IMM**: the frozen `imm-cv0.03-ct1-w0.01-s0.0003-p4-r2` via `references.imm`;
- **C**: the physics layer on C's segmentation, with the 12-knot cap;
- **C″**: C's confirmation with the zig veto (W = 6), then the fixed fade (0.73, 0.0079), from
  `configs/gate2/g2-a-fade.json`.

These are labelled "computed in Python" on the page.
