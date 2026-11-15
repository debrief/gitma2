# Feature Specification: The browser viewer on the exported artefact

**Feature Branch**: `020-browser-viewer` (developed on `claude/keen-wozniak-77td7j`)

**Created**: 2026-11-15

**Status**: Draft

**Input**: "continue" (owner, 2026-11-15, after PR 37 merged). The time-late track is closed
(SRD §9, 2026-11-15); the one item of SRD §7 step 5's default order not yet done is "the
browser viewer on the exported artefact". AGENTS.md (Autonomy): steps of the SRD plan run
without asking.

**SRD traceability**:
- §1 In scope: "Export of every carried model to a portable artefact (ONNX plus weights and
  manifest) with cross-runtime conformance; a browser viewer on that artefact."
- §7 step 5: "... the browser viewer on the exported artefact."
- Constitution VI: "Browser demos run the exported graph in ONNX Runtime Web; WebGPU is an
  optimisation, never a requirement."
- Constitution IV (honest measurement) and the Gate 3 record
  (`experiments/20261108-g3-val/`): E's raw covariance is overconfident (95% coverage 0.60)
  and must not be shown as an uncertainty without saying so.

## Background

The carried model is Gate 2's E (`experiments/20261107-g2/`, decided by the panel round 2):
C's classical segmentation, with E-s's learned evidence shifting C's confirmation threshold,
then E-w (learned per-bearing weights and a start correction) feeding the declared physics
layer. E-w and E-s are exported to ONNX with three-runtime conformance in CI
(`gate2.export`, `segment.evidence_export`; spec 007 T033). C, and the confirmation that
turns E-s's evidence into a segmentation, are host code in Python and are not exported.

Nothing yet lets a person open a page and watch the exported model run. That is the last
deliverable SRD §1 names, and the first thing an outsider would look at.

The viewer is not a result. It trains nothing, decides nothing and uses no fresh seed. Its
claim is narrow: "the artefact the gates measured runs in a browser and gives the same
numbers there as in Python, on these scenarios".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watch the carried model track a target in the browser (Priority: P1)

A reader opens the viewer page on the project site, picks one of a handful of demo
engagements, and sees the ownship and target tracks. They scrub through time and see the
carried model's estimate of the target, computed in their own browser by the exported
graph at each scored time, drawn as a trail with a marker at the current time.

**Why this priority**: It is the deliverable SRD §1 names; without it the feature does
nothing.

**Independent Test**: Open the built page in a headless browser, select each demo
engagement, step to the last time, and read the estimate from the page: it exists and is
finite where the record says the model answers.

**Acceptance Scenarios**:

1. **Given** the built site, **When** a reader opens the viewer page, **Then** the first
   demo engagement is drawn (ownship blue, target red) and the model's estimate at the
   first scored time is computed in the browser and drawn within a stated load time.
2. **Given** a demo engagement is shown, **When** the reader moves the time control,
   **Then** the estimate's trail from the ownship's zig to the chosen time and its marker at
   that time are shown, and the numeric estimate (range, bearing, course, speed) and its
   error against the truth are displayed.
3. **Given** the time control, **Then** it starts at zig + 5 min (the first G5 row), and the
   page says why no earlier estimate is drawn (the state is undetermined before the zig).

---

### User Story 2 - Compare it with the classical systems (Priority: P2)

The reader turns on comparison trails: batch least squares, the tuned IMM, and the
classical control C″ (C with a zig veto and a fixed fading memory, nothing learned). These
are precomputed by the project's Python code and shipped as data, labelled as such.

**Why this priority**: A single trail says nothing about whether learning helped. The
records' main finding is that E beats C″ by a small margin, and that margin must be
visible beside the estimate.

**Independent Test**: Toggle each comparison on and off, and check that the drawn points
equal the shipped values for that engagement and time.

**Acceptance Scenarios**:

1. **Given** an engagement and a time, **When** comparisons are on, **Then** each system's
   trail and current estimate are drawn in its own colour, with its error against the truth.
2. **Given** a system has no answer at a time (for example, the IMM before it has a state),
   **When** that time is selected, **Then** the system is shown as having no answer, never
   as zero.

---

### User Story 3 - Check that the browser computes what Python computed (Priority: P1)

A reviewer, or CI, runs the viewer's computation headless and compares every browser
estimate with the estimate the Python ONNX runtime gives on the same inputs.

**Why this priority**: Without the check the page could show numbers the gates never
measured. It is the constitution's conformance requirement applied to the demo.

**Independent Test**: A CI job builds the demo data, runs the page's computation in a
headless browser, and compares every output with the stored Python outputs.

**Acceptance Scenarios**:

1. **Given** the shipped demo inputs, **When** the browser computes every scored time of
   every engagement, **Then** every output agrees with the stored Python ONNX runtime
   output within the conformance tolerance (1e-5), and the job fails otherwise.
2. **Given** the page, **When** it loads, **Then** it shows the digests of the model graph,
   its weights and the demo data it is running, and they equal the digests in the demo
   data's manifest.

---

### User Story 4 - See the stated uncertainty honestly (Priority: P3)

The reader can turn on the model's 1-σ ellipse at the current time. It is off by default.
When it is on, a warning says that the records found this covariance overconfident (95%
coverage 0.60 against 0.95, Gate 3) and that it must not be read as a calibrated
uncertainty.

**Why this priority**: The model states a covariance and leaving it out would hide part of
the artefact. Showing it without the warning would contradict the Gate 3 and Gate 4
records.

**Independent Test**: Toggle the ellipse; check the warning is visible whenever the
ellipse is.

**Acceptance Scenarios**:

1. **Given** the page loads, **Then** no ellipse is drawn.
2. **Given** the reader turns the ellipse on, **Then** the ellipse is drawn and the warning,
   naming the Gate 3 record, is visible at the same time.

### Edge Cases

- The browser cannot load the WASM runtime, or the model fails to load: the page says so,
  and still shows the truth and the precomputed comparisons.
- A row where the model's flags say the solve did not converge or is implausible: drawn as
  "no answer", with the flag named, as the scorer treats it.
- Rows inside an open transition (C's hand-over is still open at the scored time): the
  estimate is shown as the model gives it, and the page marks the row as open.
- Slow devices: a computation over the whole engagement must not freeze the page. The
  reader sees progress, and the current time's estimate first.
- The demo data and the graph's digests disagree with the manifest (a stale build): the
  page refuses to show estimates and says which digest differs.

## Requirements *(mandatory)*

### Functional Requirements

**The artefact and the demo data**

- **FR-001**: The viewer MUST run the carried E-w graph exactly as exported by the
  project's export of Gate 2's carried model (the carried weights named in
  `experiments/20261107-g2-decision/carried.json`). It MUST NOT re-export with other settings,
  retrain, or alter weights.
- **FR-002**: The demo data MUST be a small set of engagements (default six) from a seed
  already used and never a fresh one: generator 0.6.0 MAN2 scenarios at σ = 1°. The rule
  that chooses them is fixed in the plan and is not a choice by eye. They MUST span a quiet
  target, a target that manoeuvres once, a busy target, and at least one engagement where E
  is worse than C″.
- **FR-003**: For each demo engagement and each scored time (every 60 s from the first G5 row,
  zig + 5 min, to the end of the window), the demo data MUST carry the graph's host-side inputs:
  C's segmentation with E-s's evidence applied and C's hand-over, as the Python inference
  path builds them. It MUST also carry the Python ONNX runtime's outputs on those inputs.
- **FR-004**: The demo data MUST carry the truth and, at the same times, the estimates of
  batch least squares, the tuned IMM (the frozen re-tuned settings), C and C″. All are
  produced by the project's code at a named commit.
- **FR-005**: A manifest MUST bind the demo data to the graph by digest: the ONNX graph,
  the weights, each data file, the generating command and its code commit.
- **FR-006**: The demo data MUST be regenerable by one command from the committed code and
  the named seed, and its digests MUST reproduce.

**The page**

- **FR-007**: The viewer MUST be a page of the project's site, built by the site's normal
  build. It MUST work offline once loaded: no data or runtime is fetched from outside the
  site, except the pinned runtime the site already permits.
- **FR-008**: The page MUST compute E's estimate in the browser, by the exported graph in
  ONNX Runtime Web (WASM), from the shipped inputs. It MUST NOT display the shipped Python
  outputs as if they were browser outputs.
- **FR-009**: The track plot MUST follow the project's figure conventions: ownship blue,
  target red, each estimator's trail from the zig with its marker at the current time, and
  no estimate drawn before the zig.
- **FR-010**: The page MUST show, at the current time, each system's range, bearing,
  course and speed and its error against the truth, with units.
- **FR-011**: The 1-σ ellipse MUST be off by default and, when on, MUST be accompanied by
  the overconfidence warning that cites the Gate 3 record (User Story 4).
- **FR-012**: The page MUST show the digests of the graph, weights and data it runs, the
  code commit that produced them, and a short statement of what the page is and is not.
  It is a demonstration on a handful of simulated engagements, not a result. The figures of
  record are in the Gate 2 write-up, which it links.
- **FR-013**: The page MUST state that all data are simulated (mock data, nothing above
  OFFICIAL) and that C and the confirmation step ran in Python ahead of time.

**Conformance**

- **FR-014**: CI MUST run the page's computation in a headless browser on every demo row.
  It MUST compare each output with the stored Python ONNX runtime output and fail above
  1e-5, the conformance tolerance. The job also records the browser's time per row.
- **FR-015**: The conformance job MUST also check that the shipped Python outputs equal a
  fresh Python ONNX runtime run of the graph on the shipped inputs. This catches stale
  data.

**Reporting**

- **FR-016**: A kickoff post before implementation and a slides post before the PR, as the
  reporting practice requires, link the page. The slides carry screenshots of the page
  saved as SVG where possible, or the track figure produced by `tma2-plot` from the same
  data.

### Key Entities

- **Demo engagement**: one generated MAN2 scenario (seed, ordinal), its truth, ownship and
  bearings, and the scored times.
- **Host-side inputs**: per scored time, the arrays E-w's graph takes (bearings, validity,
  ownship, times, σ, knots, speed weights, log-weights, speed skip, C's code channel), as
  the Python inference path builds them.
- **Reference outputs**: per scored time, the Python ONNX runtime's state, covariance and
  flags.
- **Comparison estimates**: per scored time, the states of batch least squares, the IMM, C
  and C″.
- **Manifest**: digests binding graph, weights, data and code commit; the generating
  command.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every browser output on every demo row agrees with the Python ONNX runtime
  within 1e-5, checked in CI on every change that can affect it.
- **SC-002**: On a CI runner the first estimate appears within 10 seconds of opening the
  page, and a whole engagement's estimates within 60 seconds. Both are measured and
  reported.
- **SC-003**: The page's shipped data (graph, weights, demo inputs and comparisons)
  totals under 15 MB, and each demo engagement's data under 2 MB.
- **SC-004**: Regenerating the demo data from the named seed and commit reproduces every
  digest in the manifest.
- **SC-005**: Whenever the ellipse is shown, the warning is visible (checked headless).
- **SC-006**: A reader can name the engagement, the time, each system's range error and
  which system is closest, from the page alone, without reading code.

## Assumptions

- The carried model is Gate 2's E with E-w's carried weights. Gate 3 and Gate 4 stopped at
  validation and carried no calibration, so the covariance shown is E's raw one, with the
  warning.
- Only E-w runs in the browser. E-s's graph is exported too, but its output feeds C's
  confirmation, which is host code. Running E-s in the browser would show a number the
  page cannot use. Porting C and the confirmation to JavaScript is out of scope (owner's
  input text). Alternative, not chosen: running E-s's graph beside E-w as a second check;
  it adds a conformance leg that CI already runs. The plan may add it if it costs little.
- Demo engagements come from seed 319, Gate 2's used test seed, on which E, C and C″ were
  scored. Seed 316 is not used: it is the noise-free seed. No fresh seed is spent.
- Scored times every 60 s keep the data small. The scorer's G5 rows (zig + 5/10/15/20 min)
  are among them.
- The runtime version is the one the conformance legs already pin (onnxruntime-web 1.31.1),
  served from the site's own build or a pinned CDN.
- The time-late track's standing control is not shown. It is not an exported artefact; it
  is classical host code. A later spec may add it as precomputed data.
- Nothing here changes a gate, a criterion or a record. The SRD is not amended. The owner
  is told in the write-up, and a §9 line is not needed for a step of the default plan.
